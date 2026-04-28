from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import AsyncSessionLocal, init_db
from app.routers import (
    alerts,
    auth,
    events,
    events_processing,
    health,
    integration,
    iot,
    ml,
    notifications,
    playbooks,
    rules,
    threat_intel,
)
from app.services.rule_engine import seed_rules


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with AsyncSessionLocal() as session:
        await seed_rules(session)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router)
app.include_router(events.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(rules.router, prefix="/api/v1")
app.include_router(ml.router, prefix="/api/v1")
app.include_router(playbooks.router, prefix="/api/v1")
app.include_router(events_processing.router, prefix="/api/v1")
app.include_router(notifications.router)
app.include_router(iot.router)
app.include_router(threat_intel.router)
app.include_router(integration.router)
