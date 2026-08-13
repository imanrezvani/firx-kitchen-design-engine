from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai.routes import router as ai_router
from app.auth.routes import router as auth_router
from app.catalog.routes import router as catalog_router
from app.core.config import settings
from app.core.database import init_platform_db
from app.customers.routes import router as customers_router
from app.dashboard.routes import router as dashboard_router
from app.design.routes import router as design_router
from app.files.routes import router as files_router
from app.projects.routes import router as projects_router
from app.rooms.routes import router as rooms_router
from app.tenants.routes import router as tenants_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_platform_db()
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(ai_router)
app.include_router(tenants_router)
app.include_router(customers_router)
app.include_router(projects_router)
app.include_router(rooms_router)
app.include_router(catalog_router)
app.include_router(design_router)
app.include_router(dashboard_router)
app.include_router(files_router)


@app.get("/api/v1/health")
async def health():
    return {"status": "ok"}
