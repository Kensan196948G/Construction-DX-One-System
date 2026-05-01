"""Integration API router: CAB ↔ SIEM / BCP cross-system communication."""
import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.rfc import RFC

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

class CreateRFCFromIncidentRequest(BaseModel):
    incident_id: str
    incident_title: str
    incident_severity: str
    incident_description: str
    source_system: str = "SIEM"
    requested_by: str = "SIEM-AutoEscalation"
    urgency: str = "normal"


class CreateRFCFromIncidentResponse(BaseModel):
    rfc_id: str
    title: str
    status: str
    risk_level: str
    incident_reference: str
    message: str


class PendingChangeResponse(BaseModel):
    id: str
    title: str
    change_type: str
    status: str
    risk_level: str
    priority: str
    affected_systems: list[str]
    planned_start: datetime | None
    created_at: datetime


class ChangesSummaryResponse(BaseModel):
    pending_count: int
    approved_count: int
    high_risk_count: int
    emergency_count: int
    generated_at: datetime


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/rfcs/from-incident",
    response_model=CreateRFCFromIncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create RFC from a SIEM incident",
)
async def create_rfc_from_incident(
    payload: CreateRFCFromIncidentRequest,
    _: None = IntegrationAuth,
    db: AsyncSession = Depends(get_db),
):
    """Auto-create an RFC when SIEM escalates a high-severity incident."""
    severity_to_risk = {"critical": "high", "high": "high", "medium": "medium", "low": "low"}
    severity_to_priority = {"critical": "critical", "high": "high", "medium": "medium", "low": "low"}
    severity_to_type = {"critical": "emergency", "high": "urgent", "medium": "normal", "low": "normal"}

    rfc = RFC(
        id=str(uuid.uuid4()),
        title=f"[SIEM Escalation] {payload.incident_title}",
        description=(
            f"Automatically created from SIEM incident.\n"
            f"Incident ID: {payload.incident_id}\n"
            f"Severity: {payload.incident_severity}\n\n"
            f"{payload.incident_description}"
        ),
        change_type=severity_to_type.get(payload.incident_severity, "normal"),
        status="draft",
        priority=severity_to_priority.get(payload.incident_severity, "medium"),
        risk_level=severity_to_risk.get(payload.incident_severity, "medium"),
        requester=payload.requested_by,
    )
    db.add(rfc)
    await db.commit()

    return CreateRFCFromIncidentResponse(
        rfc_id=rfc.id,
        title=rfc.title,
        status=rfc.status,
        risk_level=rfc.risk_level,
        incident_reference=payload.incident_id,
        message=f"RFC created from SIEM incident {payload.incident_id}",
    )


@router.get(
    "/changes/pending",
    response_model=list[PendingChangeResponse],
    summary="Get pending high-risk changes for BCP notification",
)
async def get_pending_changes(
    risk_level: str = Query("high", description="Minimum risk level (medium|high)"),
    _: None = IntegrationAuth,
    db: AsyncSession = Depends(get_db),
):
    """Provide pending approved changes to BCP for continuity monitoring."""
    risk_levels = ["high"] if risk_level == "high" else ["medium", "high"]
    result = await db.execute(
        select(RFC).where(
            RFC.risk_level.in_(risk_levels),
            RFC.status.in_(["approved", "pending_cab"]),
        ).order_by(RFC.created_at.desc()).limit(100)
    )
    rfcs = result.scalars().all()

    return [
        PendingChangeResponse(
            id=r.id,
            title=r.title,
            change_type=r.change_type,
            status=r.status,
            risk_level=r.risk_level,
            priority=r.priority,
            affected_systems=r.affected_systems.split(",") if r.affected_systems else [],
            planned_start=r.planned_start,
            created_at=r.created_at,
        )
        for r in rfcs
    ]


@router.get(
    "/changes/summary",
    response_model=ChangesSummaryResponse,
    summary="Get change summary for BCP and GRC dashboards",
)
async def get_changes_summary(
    _: None = IntegrationAuth,
    db: AsyncSession = Depends(get_db),
):
    """Aggregate RFC counts by status and risk for cross-system dashboards."""
    result = await db.execute(select(RFC))
    all_rfcs = result.scalars().all()

    return ChangesSummaryResponse(
        pending_count=sum(1 for r in all_rfcs if r.status in ("draft", "pending_cab")),
        approved_count=sum(1 for r in all_rfcs if r.status == "approved"),
        high_risk_count=sum(1 for r in all_rfcs if r.risk_level == "high"),
        emergency_count=sum(1 for r in all_rfcs if r.change_type == "emergency"),
        generated_at=datetime.now(UTC),
    )
