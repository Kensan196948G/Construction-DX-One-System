from fastapi import APIRouter, Query

from app.schemas.threat_intel import (
    CorrelateEventRequest,
    CorrelateEventResponse,
    IoCCheckRequest,
    IoCCheckResponse,
    RecentThreatsResponse,
)
from app.services.threat_intel import get_threat_intel_service

router = APIRouter(prefix="/api/v1/threat-intel", tags=["threat-intel"])


@router.post("/check", response_model=IoCCheckResponse)
async def check_ioc(payload: IoCCheckRequest):
    service = get_threat_intel_service()
    result = service.check_ioc(value=payload.value, ioc_type=payload.ioc_type)
    return IoCCheckResponse(**result)


@router.post("/correlate", response_model=CorrelateEventResponse)
async def correlate_event(payload: CorrelateEventRequest):
    service = get_threat_intel_service()
    matches = service.correlate_event_with_iocs(payload.event_data)
    risk_score = 0.0
    if matches:
        risk_score = sum(
            m["match"]["confidence"] * 7.0
            for m in matches
        ) / len(matches)
    return CorrelateEventResponse(
        status="success",
        matches=matches,
        total_matches=len(matches),
        risk_score=round(risk_score, 2),
    )


@router.get("/recent", response_model=RecentThreatsResponse)
async def get_recent_threats(hours: int = Query(24, ge=1, le=720)):
    service = get_threat_intel_service()
    recent = service.get_recent_threats(hours=hours)
    return RecentThreatsResponse(data=recent)
