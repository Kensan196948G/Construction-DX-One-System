from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.rfc import (
    ConflictDetectionResult,
    ImpactAnalysisRequest,
    ImpactAnalysisResult,
)
from app.services import impact_analysis as svc

router = APIRouter()


@router.post("/impact/analyze", response_model=ImpactAnalysisResult)
async def analyze_impact(
    payload: ImpactAnalysisRequest,
    db: AsyncSession = Depends(get_db),
):
    return await svc.analyze_impact(payload.model_dump(), db)


@router.post("/impact/detect-conflicts", response_model=ConflictDetectionResult)
async def detect_conflicts(
    payload: ImpactAnalysisRequest,
    db: AsyncSession = Depends(get_db),
):
    conflicts = await svc.detect_conflicts(payload.model_dump(), db)
    return ConflictDetectionResult(
        has_conflicts=len(conflicts) > 0,
        total_conflicts=len(conflicts),
        conflicting_rfcs=conflicts,
    )


@router.get("/impact/change-calendar")
async def get_change_calendar(
    date_from: datetime = Query(...),
    date_to: datetime = Query(...),
    db: AsyncSession = Depends(get_db),
):
    entries = await svc.get_change_calendar(date_from, date_to, db)
    return {"status": "success", "data": entries, "meta": {"total": len(entries)}}


@router.get("/impact/system-map")
async def get_system_impact_map(
    db: AsyncSession = Depends(get_db),
):
    return await svc.get_system_impact_map(db)
