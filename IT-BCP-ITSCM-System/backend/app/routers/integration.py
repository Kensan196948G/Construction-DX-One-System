"""Integration API router: BCP ↔ GRC / CAB cross-system communication."""
import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.incident import Incident
from app.models.system import ITSystem

router = APIRouter(prefix="/api/v1/integration", tags=["integration"])

_api_key_header = APIKeyHeader(name="X-Integration-Key", auto_error=False)
_INTEGRATION_KEY = "dev-integration-key-change-in-prod"


async def verify_integration_key(
    api_key: Annotated[str | None, Depends(_api_key_header)],
) -> None:
    if not api_key or api_key != _INTEGRATION_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing integration API key",
        )


IntegrationAuth = Depends(verify_integration_key)


# ── Schemas ───────────────────────────────────────────────────────────────────

class RecoveryPlan(BaseModel):
    system_id: str
    system_name: str
    tier: str
    rto_minutes: int
    rpo_minutes: int
    status: str
    current_incidents: int


class RecoveryPlansResponse(BaseModel):
    plans: list[RecoveryPlan]
    active_incidents: int
    generated_at: datetime


class RiskAlertRequest(BaseModel):
    risk_id: str
    title: str
    risk_score: float
    category: str
    source_system: str = "GRC"


class CABChangeNotification(BaseModel):
    change_id: str
    title: str
    risk_level: str
    affected_systems: list[str]
    scheduled_at: datetime | None = None
    source_system: str = "CAB"


class BCPActivationResponse(BaseModel):
    incident_id: str
    title: str
    bcp_activated: bool
    affected_systems: list[str]
    message: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/recovery-plans",
    response_model=RecoveryPlansResponse,
    summary="Provide recovery plans to GRC for continuity compliance",
)
async def get_recovery_plans(
    tier: str | None = Query(None, description="Filter by system tier (tier1|tier2|tier3)"),
    _: None = IntegrationAuth,
    db: AsyncSession = Depends(get_db),
):
    """Return IT system recovery plans with current incident status."""
    stmt = select(ITSystem)
    if tier:
        stmt = stmt.where(ITSystem.tier == tier)
    result = await db.execute(stmt)
    systems = result.scalars().all()

    inc_result = await db.execute(
        select(Incident).where(Incident.status == "open", Incident.bcp_activated == True)  # noqa: E712
    )
    active_incidents = inc_result.scalars().all()
    active_system_names = set()
    for inc in active_incidents:
        if inc.affected_systems:
            active_system_names.update(inc.affected_systems.split(","))

    plans = [
        RecoveryPlan(
            system_id=s.id,
            system_name=s.name,
            tier=s.tier,
            rto_minutes=s.rto_minutes,
            rpo_minutes=s.rpo_minutes,
            status=s.status,
            current_incidents=sum(1 for name in active_system_names if s.name in name),
        )
        for s in systems
    ]

    return RecoveryPlansResponse(
        plans=plans,
        active_incidents=len(active_incidents),
        generated_at=datetime.now(UTC),
    )


@router.post(
    "/risk-alerts",
    status_code=status.HTTP_201_CREATED,
    summary="Receive high-risk alerts from GRC and create BCP incidents",
)
async def receive_risk_alert(
    payload: RiskAlertRequest,
    _: None = IntegrationAuth,
    db: AsyncSession = Depends(get_db),
):
    """Create a BCP incident when GRC reports a high-risk item (score >= 15)."""
    if payload.risk_score < 15:
        return {"created": False, "reason": "Risk score below BCP threshold (15)"}

    severity = "critical" if payload.risk_score >= 20 else "high"
    incident = Incident(
        id=str(uuid.uuid4()),
        title=f"[GRC Risk] {payload.title}",
        description=f"High-risk item escalated from GRC. Score: {payload.risk_score}. Category: {payload.category}",
        severity=severity,
        status="open",
        bcp_activated=severity == "critical",
    )
    db.add(incident)
    await db.commit()
    return {"created": True, "incident_id": incident.id, "severity": severity}


@router.post(
    "/change-notifications",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Receive change notifications from CAB",
)
async def receive_change_notification(
    payload: CABChangeNotification,
    _: None = IntegrationAuth,
    db: AsyncSession = Depends(get_db),
):
    """Record high-risk changes from CAB that may affect BCP continuity."""
    if payload.risk_level not in ("high", "critical"):
        return None

    incident = Incident(
        id=str(uuid.uuid4()),
        title=f"[CAB Change] {payload.title}",
        description=f"High-risk change from CAB. Risk level: {payload.risk_level}. Change ID: {payload.change_id}",
        severity=payload.risk_level,
        status="monitoring",
        bcp_activated=False,
        affected_systems=",".join(payload.affected_systems),
    )
    db.add(incident)
    await db.commit()
    return None
