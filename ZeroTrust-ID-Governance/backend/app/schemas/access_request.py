from datetime import datetime

from pydantic import BaseModel


class AccessRequestCreate(BaseModel):
    target_resource: str
    justification: str
    requested_role_id: str | None = None


class AccessRequestReview(BaseModel):
    status: str  # "approved" | "rejected"
    comment: str | None = None


class AccessRequestRead(BaseModel):
    id: str
    requester_id: str | None = None
    target_resource: str
    justification: str
    requested_role_id: str | None = None
    status: str
    approver_id: str | None = None
    reviewed_at: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
