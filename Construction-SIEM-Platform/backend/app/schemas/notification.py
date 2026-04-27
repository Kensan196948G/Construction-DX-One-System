from datetime import datetime

from pydantic import BaseModel


class NotificationSendRequest(BaseModel):
    channel: str
    recipient: str
    subject: str | None = None
    body: str
    html: str | None = None
    related_entity_type: str | None = None
    related_entity_id: str | None = None


class NotificationSendResponse(BaseModel):
    status: str = "success"
    channel: str
    recipient: str
    notification_id: str | None = None
    message: str


class AlertNotificationRequest(BaseModel):
    alert_id: str
    channels: list[str]


class NotificationLogResponse(BaseModel):
    id: str
    channel: str
    recipient: str
    subject: str | None
    body: str
    status: str
    error_message: str | None
    related_entity_type: str | None
    related_entity_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationHistoryResponse(BaseModel):
    status: str = "success"
    data: list[NotificationLogResponse]


class NotificationTemplateCreate(BaseModel):
    name: str
    channel: str
    subject_template: str | None = None
    body_template: str


class NotificationTemplateResponse(BaseModel):
    id: str
    name: str
    channel: str
    subject_template: str | None
    body_template: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NotificationTemplateListResponse(BaseModel):
    status: str = "success"
    data: list[NotificationTemplateResponse]
