from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.alert import Alert
from app.schemas.alert import (
    AlertCreate,
    AlertListResponse,
    AlertResponse,
    AlertStatusUpdate,
    AlertSummaryItem,
    AlertSummaryResponse,
)

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    severity: str | None = None,
    status: str | None = None,
    acknowledged: bool | None = None,
    source: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Alert)
    count_query = select(func.count()).select_from(Alert)

    if severity:
        query = query.where(Alert.severity == severity)
        count_query = count_query.where(Alert.severity == severity)
    if status:
        query = query.where(Alert.status == status)
        count_query = count_query.where(Alert.status == status)
    if acknowledged is not None:
        query = query.where(Alert.acknowledged == acknowledged)
        count_query = count_query.where(Alert.acknowledged == acknowledged)
    if source:
        query = query.where(Alert.source == source)
        count_query = count_query.where(Alert.source == source)

    total = (await db.execute(count_query)).scalar_one()
    offset = (page - 1) * per_page
    result = await db.execute(query.order_by(Alert.created_at.desc()).offset(offset).limit(per_page))
    alerts = result.scalars().all()

    return AlertListResponse(
        data=[AlertResponse.model_validate(a) for a in alerts],
        meta={"page": page, "per_page": per_page, "total": total, "total_pages": (total + per_page - 1) // per_page},
    )


@router.get("/summary/by-severity", response_model=AlertSummaryResponse)
async def alert_summary_by_severity(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Alert.severity, func.count().label("count"))
        .group_by(Alert.severity)
    )
    rows = result.all()
    return AlertSummaryResponse(data=[AlertSummaryItem(severity=r[0], count=r[1]) for r in rows])


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertResponse.model_validate(alert)


@router.post("", response_model=AlertResponse, status_code=201)
async def create_alert(payload: AlertCreate, db: AsyncSession = Depends(get_db)):
    alert = Alert(**payload.model_dump())
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return AlertResponse.model_validate(alert)


@router.patch("/{alert_id}/status", response_model=AlertResponse)
async def update_alert_status(
    alert_id: str,
    payload: AlertStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = payload.status
    alert.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(alert)
    return AlertResponse.model_validate(alert)


@router.patch("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: str,
    acknowledged_by: str = "system",
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.acknowledged = True
    alert.acknowledged_by = acknowledged_by
    alert.acknowledged_at = datetime.utcnow()
    alert.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(alert)
    return AlertResponse.model_validate(alert)


@router.post("/ingest", response_model=AlertResponse, status_code=201)
async def ingest_alert(payload: AlertCreate, db: AsyncSession = Depends(get_db)):
    """Ingest alert from external security tools."""
    alert = Alert(**payload.model_dump())
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return AlertResponse.model_validate(alert)
