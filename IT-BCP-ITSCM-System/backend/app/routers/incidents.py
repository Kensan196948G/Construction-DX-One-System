import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.incident import Incident
from app.schemas.incident import (
    IncidentCreate,
    IncidentListResponse,
    IncidentResponse,
    IncidentStatusUpdate,
)

router = APIRouter()


@router.get("/incidents", response_model=IncidentListResponse)
async def list_incidents(
    severity: str | None = Query(None),
    status: str | None = Query(None),
    bcp_activated: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Incident).order_by(Incident.created_at.desc())
    if severity:
        query = query.where(Incident.severity == severity)
    if status:
        query = query.where(Incident.status == status)
    if bcp_activated is not None:
        query = query.where(Incident.bcp_activated == bcp_activated)

    result = await db.execute(query)
    incidents = result.scalars().all()

    return IncidentListResponse(
        data=[IncidentResponse.model_validate(i) for i in incidents],
        meta={"total": len(incidents)},
    )


@router.post("/incidents", response_model=IncidentResponse, status_code=201)
async def create_incident(payload: IncidentCreate, db: AsyncSession = Depends(get_db)):
    incident = Incident(
        id=str(uuid.uuid4()),
        title=payload.title,
        description=payload.description,
        severity=payload.severity,
        affected_systems=payload.affected_systems,
        rto_deadline=payload.rto_deadline,
    )
    db.add(incident)
    await db.commit()
    await db.refresh(incident)
    return IncidentResponse.model_validate(incident)


@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return IncidentResponse.model_validate(incident)


@router.patch("/incidents/{incident_id}/status", response_model=IncidentResponse)
async def update_incident_status(
    incident_id: str,
    payload: IncidentStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident.status = payload.status
    if payload.status == "resolved" and incident.created_at:
        delta = datetime.now(UTC) - incident.created_at.replace(tzinfo=UTC)
        incident.recovery_time_minutes = int(delta.total_seconds() / 60)
        incident.rto_achieved = (
            incident.rto_deadline is None
            or datetime.now(UTC) <= incident.rto_deadline.replace(tzinfo=UTC)
        )

    incident.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(incident)
    return IncidentResponse.model_validate(incident)


@router.patch("/incidents/{incident_id}/activate-bcp", response_model=IncidentResponse)
async def activate_bcp(incident_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident.bcp_activated = True
    incident.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(incident)
    return IncidentResponse.model_validate(incident)
