from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import access_requests, audit, auth, entraid, health, roles, users

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="建設業ゼロトラスト統合 ID 管理 API",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(roles.router, prefix="/api/v1")
app.include_router(access_requests.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(entraid.router, prefix="/api/v1")
