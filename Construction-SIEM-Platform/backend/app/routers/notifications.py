from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.alert import Alert
from app.models.notification import NotificationTemplate
from app.schemas.notification import (
    AlertNotificationRequest,
    NotificationHistoryResponse,
    NotificationLogResponse,
    NotificationSendRequest,
    NotificationSendResponse,
    NotificationTemplateCreate,
    NotificationTemplateListResponse,
    NotificationTemplateResponse,
)
from app.services.notification_service import get_notification_service

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.post("/send", response_model=NotificationSendResponse)
async def send_notification(
    payload: NotificationSendRequest,
    db: AsyncSession = Depends(get_db),
):
    service = get_notification_service(db)
    if payload.channel == "email":
        result = await service.send_email(
            to=payload.recipient,
            subject=payload.subject or "",
            body=payload.body,
            html=payload.html,
        )
    elif payload.channel == "teams":
        result = await service.send_teams(
            title=payload.subject or "Notification",
            message=payload.body,
        )
    elif payload.channel == "sms":
        result = await service.send_sms(
            phone=payload.recipient,
            message=payload.body,
        )
    else:
        return NotificationSendResponse(
            status="error",
            channel=payload.channel,
            recipient=payload.recipient,
            message=f"Unsupported channel: {payload.channel}",
        )
    return NotificationSendResponse(
        status="success" if result.get("success") else "error",
        channel=payload.channel,
        recipient=payload.recipient,
        notification_id=result.get("notification_id"),
        message=f"Notification sent via {payload.channel}",
    )


@router.get("/history", response_model=NotificationHistoryResponse)
async def get_notification_history(
    entity_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    service = get_notification_service(db)
    logs = await service.get_notification_history(entity_id=entity_id, limit=limit)
    return NotificationHistoryResponse(
        data=[NotificationLogResponse.model_validate(log) for log in logs],
    )


@router.post("/alert", response_model=dict)
async def send_alert_notification(
    payload: AlertNotificationRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Alert).where(Alert.id == payload.alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Alert not found")
    service = get_notification_service(db)
    results = await service.send_alert_notification(alert, payload.channels)
    return {"status": "success", "results": results}


@router.post("/templates", response_model=NotificationTemplateResponse, status_code=201)
async def create_notification_template(
    payload: NotificationTemplateCreate,
    db: AsyncSession = Depends(get_db),
):
    template = NotificationTemplate(**payload.model_dump())
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return NotificationTemplateResponse.model_validate(template)


@router.get("/templates", response_model=NotificationTemplateListResponse)
async def list_notification_templates(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(NotificationTemplate).order_by(NotificationTemplate.created_at.desc()))
    templates = result.scalars().all()
    return NotificationTemplateListResponse(
        data=[NotificationTemplateResponse.model_validate(t) for t in templates],
    )
