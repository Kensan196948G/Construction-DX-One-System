from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import init_db
from app.routers import cab_meetings, calendar, freeze_periods, health, impact_analysis, kpi, rfcs


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="IT-Change-CAB-Platform API",
    description="IT Change Advisory Board management backend",
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
app.include_router(rfcs.router, prefix=PREFIX, tags=["rfcs"])
app.include_router(cab_meetings.router, prefix=PREFIX, tags=["cab-meetings"])
app.include_router(impact_analysis.router, prefix=PREFIX, tags=["impact"])
app.include_router(freeze_periods.router, prefix=PREFIX, tags=["freeze-periods"])
app.include_router(kpi.router, prefix=PREFIX, tags=["kpi"])
app.include_router(calendar.router, prefix=PREFIX, tags=["calendar"])
