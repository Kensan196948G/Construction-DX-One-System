from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.alert import AlertCreate, AlertRead, AlertStatusUpdate
from app.services import alert_service

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.post("", response_model=AlertRead, status_code=status.HTTP_201_CREATED)
async def create_alert(payload: AlertCreate, db: AsyncSession = Depends(get_db)) -> AlertRead:
    alert = await alert_service.create_alert(db, payload)
    return AlertRead.model_validate(alert)


@router.get("", response_model=list[AlertRead])
async def list_alerts(
    status_filter: str | None = Query(default=None, alias="status"),
    severity: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[AlertRead]:
    alerts = await alert_service.list_alerts(
        db, status=status_filter, severity=severity, limit=limit, offset=offset
    )
    return [AlertRead.model_validate(a) for a in alerts]


@router.get("/{alert_id}", response_model=AlertRead)
async def get_alert(alert_id: str, db: AsyncSession = Depends(get_db)) -> AlertRead:
    alert = await alert_service.get_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return AlertRead.model_validate(alert)


@router.patch("/{alert_id}/status", response_model=AlertRead)
async def update_status(
    alert_id: str,
    payload: AlertStatusUpdate,
    db: AsyncSession = Depends(get_db),
) -> AlertRead:
    alert = await alert_service.update_alert_status(db, alert_id, payload)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return AlertRead.model_validate(alert)
