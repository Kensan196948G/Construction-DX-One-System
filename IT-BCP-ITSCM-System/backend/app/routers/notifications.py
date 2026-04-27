from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.incident import Incident
from app.schemas.notification import EscalationRequest, NotificationResult, NotificationTest
from app.services import notification_service

router = APIRouter()


@router.post("/notifications/test", response_model=NotificationResult)
async def test_notification(
    payload: NotificationTest,
    db: AsyncSession = Depends(get_db),
):
    if payload.channel not in ("teams", "email", "sms"):
        raise HTTPException(status_code=400, detail="Invalid channel. Must be teams, email, or sms")

    dummy = Incident(
        id="test-00000000-0000-0000-0000-000000000000",
        title="Test Notification",
        description=payload.message or "This is a test notification from IT-BCP-ITSCM System",
        severity="low",
        status="open",
    )
    result = await notification_service.send_incident_notification(dummy, payload.channel)
    return NotificationResult(**result)


@router.post("/notifications/escalate/{incident_id}", response_model=NotificationResult)
async def escalate_incident(
    incident_id: str,
    payload: EscalationRequest = EscalationRequest(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    escalation_result = await notification_service.send_escalation(incident, payload.level)
    return NotificationResult(**escalation_result)
