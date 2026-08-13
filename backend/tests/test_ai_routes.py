"""HTTP-level tests for the AI pipeline endpoints.

Uses FastAPI TestClient with the auth dependency overridden so the full
request → validation → pipeline → response path is exercised without a DB.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.deps import resolve_context


class _FakeUser:
    id = "00000000-0000-0000-0000-000000000001"
    is_active = True


class _FakeTenant:
    id = "00000000-0000-0000-0000-000000000002"
    is_active = True


class _FakeMembership:
    tenant_id = _FakeTenant.id
    user_id = _FakeUser.id
    role = "owner"


class _FakeCtx:
    user = _FakeUser()
    tenant = _FakeTenant()
    membership = _FakeMembership()
    schema = "tnt_test"

    @property
    def user_id(self):
        return self.user.id

    @property
    def tenant_id(self):
        return self.tenant.id


@pytest.fixture
def client() -> TestClient:
    # NOTE: we intentionally do NOT use `with TestClient(app)` here. The app
    # lifespan calls init_platform_db() which opens asyncpg connections bound
    # to this test's event loop; after the loop closes those pooled
    # connections break subsequent tests ("Future attached to a different
    # loop"). The AI endpoints never touch the database (auth is overridden),
    # so we create the client without entering the lifespan.
    app.dependency_overrides[resolve_context] = lambda: _FakeCtx()
    return TestClient(app)


def _clear_overrides():
    app.dependency_overrides.clear()


def _payload() -> dict:
    return {
        "version": "1.0",
        "project_id": "p-001",
        "project_name": "آشپزخانه نمونه",
        "room": {"width": 4200, "length": 3600, "height": 2700, "unit": "mm"},
        "walls": [
            {"side": "north", "length": 4200},
            {"side": "south", "length": 4200},
            {"side": "east", "length": 3600},
            {"side": "west", "length": 3600},
        ],
        "doors": [{"id": "d1", "wall": "north", "offset": 3200, "width": 900, "swing": "right"}],
        "windows": [{"id": "w1", "wall": "south", "offset": 1400, "width": 1400, "sill_height": 900}],
        "layout": "L_SHAPE",
        "cabinets": [
            {"type": "base", "width": 600, "height": 720, "depth": 600, "count": 6},
            {"type": "wall", "width": 600, "height": 900, "depth": 350, "count": 3},
        ],
        "appliances": [
            {"type": "refrigerator", "variant": "double_door"},
            {"type": "dishwasher", "variant": "60cm"},
            {"type": "cooktop", "variant": "built_in"},
        ],
        "sink": {"type": "double_bowl", "width": 900, "depth": 500},
        "objects": [
            {"type": "refrigerator", "wall": "east", "offset": 3000, "width": 700, "depth": 700, "height": 1780},
            {"type": "island", "wall": None, "offset": 0, "width": 1500, "depth": 900, "height": 900},
        ],
        "style": "modern",
        "colors": {"cabinet_color": "سفید", "cabinet_finish": "مات", "handle_style": "بدون دستگیره"},
        "countertop": {"material": "کوارتز", "color": "سفید", "thickness": 40},
        "photos": [{"id": "ph1", "url": "https://example.com/ph1.jpg"}],
        "user_requirements": {"notes": "خانواده چهار نفره", "preferences": [], "must_include": [], "must_avoid": []},
    }


def test_pipeline_full_flow(client: TestClient):
    r = client.post("/api/v1/ai/pipeline", json=_payload())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["spec"]["layout"] == "L_SHAPE"
    assert body["provider"] == "mock"
    assert body["model"] == "firx-rule-engine-v1"
    assert body["prompt"]["layout"] == "L_SHAPE"
    assert len(body["prompt"]["sections"]) == 14
    assert body["design"]["score"] > 0
    assert body["design"]["cabinets"]
    assert body["design"]["appliances"]
    assert body["design"]["render_instructions"]


def test_pipeline_with_custom_camera_views(client: TestClient):
    r = client.post(
        "/api/v1/ai/pipeline?camera_views=MAIN_PERSPECTIVE&camera_views=ENTRANCE_VIEW",
        json=_payload(),
    )
    assert r.status_code == 200, r.text
    views = r.json()["prompt"]["camera_views"]
    assert set(views) == {"MAIN_PERSPECTIVE", "ENTRANCE_VIEW"}


def test_pipeline_unknown_provider_422(client: TestClient):
    r = client.post("/api/v1/ai/pipeline?provider_name=deepseek", json=_payload())
    assert r.status_code == 422
    assert r.json()["detail"] == "unknown_provider"


def test_pipeline_gpt_without_key_503(client: TestClient):
    r = client.post("/api/v1/ai/pipeline?provider_name=gpt", json=_payload())
    assert r.status_code == 503
    assert "APP_OPENAI_API_KEY" in r.json()["detail"]


def test_validate_spec_endpoint(client: TestClient):
    r = client.post("/api/v1/ai/spec", json=_payload())
    assert r.status_code == 200
    assert r.json()["valid"] is True
    assert r.json()["spec"]["layout"] == "L_SHAPE"


def test_validate_spec_rejects_bad_appliance(client: TestClient):
    payload = _payload()
    payload["appliances"] = [{"type": "teleport", "variant": "x"}]
    r = client.post("/api/v1/ai/spec", json=payload)
    assert r.status_code == 422


def test_providers_list(client: TestClient):
    r = client.get("/api/v1/ai/providers")
    assert r.status_code == 200
    body = r.json()
    assert set(body["providers"]) == {"gpt", "gemini", "mock"}
    assert body["default"] == "mock"
    assert body["selected"] == "mock"


def test_pipeline_unauthorized(client: TestClient):
    _clear_overrides()
    r = client.post("/api/v1/ai/pipeline", json=_payload())
    assert r.status_code == 401


def test_roundtrip_parses_as_pydantic_model():
    from app.ai.spec import KitchenSpecification

    c = TestClient(app)
    app.dependency_overrides[resolve_context] = lambda: _FakeCtx()
    try:
        r = c.post("/api/v1/ai/pipeline", json=_payload())
        assert r.status_code == 200
        spec = KitchenSpecification.model_validate(r.json()["spec"])
        assert spec.layout.value == "L_SHAPE"
        assert len(spec.cabinets) == 2
    finally:
        app.dependency_overrides.clear()


def test_debug_endpoint_no_credentials(client: TestClient):
    r = client.get("/api/v1/ai/debug")
    assert r.status_code == 200, r.text
    body = r.json()
    # must expose pipeline internals for debugging...
    assert body["pipeline"]["provider"] == "mock"
    assert body["pipeline"]["design_score"] > 0
    assert len(body["prompt"]["sections"]) == 14
    assert body["design"]["cabinets"]
    # ...but NEVER any credential material
    assert "api_key" not in r.text.lower()
    assert "sk-" not in r.text
    # provider status reports configured without leaking values
    assert body["selected"]["configured_providers"]["gpt"]["configured"] is False
