from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import init_db
from app.routers import (
    bia,
    dashboard,
    exercises,
    health,
    incidents,
    integration,
    notifications,
    reports,
    systems,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="IT-BCP-ITSCM-System API",
    description="IT BCP / ITSCM management backend",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX = "/api/v1"
app.include_router(health.router, prefix=PREFIX, tags=["health"])
app.include_router(incidents.router, prefix=PREFIX, tags=["incidents"])
app.include_router(systems.router, prefix=PREFIX, tags=["systems"])
app.include_router(exercises.router, prefix=PREFIX, tags=["exercises"])
app.include_router(dashboard.router, prefix=PREFIX, tags=["dashboard"])
app.include_router(bia.router, prefix=PREFIX, tags=["bia"])
app.include_router(reports.router, prefix=PREFIX, tags=["reports"])
app.include_router(notifications.router, prefix=PREFIX, tags=["notifications"])
app.include_router(integration.router, tags=["integration"])
