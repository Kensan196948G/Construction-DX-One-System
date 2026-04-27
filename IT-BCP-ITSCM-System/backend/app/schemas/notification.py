from datetime import datetime

from pydantic import BaseModel


class NotificationTest(BaseModel):
    channel: str
    message: str | None = None


class NotificationResult(BaseModel):
    channel: str
    status: str
    sent_at: datetime
    message_id: str
    details: str | None = None


class EscalationRequest(BaseModel):
    level: int = 1
    reason: str | None = None
