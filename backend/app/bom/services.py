"""BOM (Bill of Materials) generation from a parametric design."""

from __future__ import annotations

from app.design.parametric import DesignModel
from app.design import rules as R


def generate_bom(design: DesignModel, catalog_by_id: dict[str, dict]) -> dict:
    """Returns a structured BOM: cabinet/material/appliance/countertop rows
    plus totals. catalog_by_id maps catalog item id -> row (price etc.)."""
    rows: list[dict] = []

    # cabinets
    for c in design.cabinets:
        cat = catalog_by_id.get(c.catalog_item_id or "") if c.catalog_item_id else None
        unit = float(cat["base_price"]) if cat else 0.0
        name = cat.get("name") if cat else c.name
        rows.append(
            {
                "category": "cabinet",
                "code": cat.get("code") if cat else "",
                "name": name,
                "qty": 1,
                "width_mm": c.width_mm,
                "height_mm": c.height_mm,
                "depth_mm": c.depth_mm,
                "unit_price": unit,
                "total_price": unit,
            }
        )

    # appliances
    for ap in design.appliances:
        cat = catalog_by_id.get(ap.catalog_item_id or "") if ap.catalog_item_id else None
        unit = float(cat["price"]) if cat else 0.0
        rows.append(
            {
                "category": "appliance",
                "code": cat.get("code") if cat else "",
                "name": ap.name,
                "qty": 1,
                "width_mm": ap.width_mm,
                "height_mm": ap.height_mm,
                "depth_mm": ap.depth_mm,
                "unit_price": unit,
                "total_price": unit,
            }
        )

    # countertops (approx surface)
    for ct in design.countertops:
        area = (ct.width_mm / 1000) * (ct.depth_mm / 1000)
        unit_price = 0.0
        mat_name = ct.material_name or "کورین"
        rows.append(
            {
                "category": "countertop",
                "code": "",
                "name": f"صفحه کابینت ({mat_name})",
                "qty": 1,
                "width_mm": ct.width_mm,
                "height_mm": ct.thickness_mm,
                "depth_mm": ct.depth_mm,
                "unit_price": round(unit_price, 2),
                "total_price": round(unit_price, 2),
            }
        )

    # materials consumption (sheet estimate, +/-10%)
    sheets = _sheet_estimate(design)

    cabinet_total = sum(r["total_price"] for r in rows if r["category"] == "cabinet")
    appliance_total = sum(r["total_price"] for r in rows if r["category"] == "appliance")
    counter_total = sum(r["total_price"] for r in rows if r["category"] == "countertop")
    total = cabinet_total + appliance_total + counter_total

    return {
        "rows": rows,
        "totals": {
            "cabinets": round(cabinet_total, 2),
            "appliances": round(appliance_total, 2),
            "countertops": round(counter_total, 2),
            "grand_total": round(total, 2),
            "accuracy": "±۱۰٪",
        },
        "sheets": sheets,
        "note": "این BOM برآورد تخمینی متریال و قیمت است؛ برای تولید نهایی به تأیید مهندسی نیاز دارد.",
    }


def _sheet_estimate(design: DesignModel) -> dict:
    """Rough 18mm sheet count from visible cabinet faces (front + side tops)."""
    sheet_area = 1.22 * 2.44  # m^2
    total_area = 0.0
    for c in design.cabinets:
        if c.type == "wall":
            area = (c.width_mm / 1000) * (c.height_mm / 1000)
        else:
            area = (c.width_mm / 1000) * (c.height_mm / 1000)
        total_area += area
    sheets = int(total_area / sheet_area) + 2
    return {"m2": round(total_area, 2), "sheets_18mm": sheets}
