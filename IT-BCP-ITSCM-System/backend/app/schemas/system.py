from datetime import datetime

from pydantic import BaseModel


class ITSystemResponse(BaseModel):
    id: str
    name: str
    tier: str
    status: str
    rto_minutes: int
    rpo_minutes: int
    description: str | None
    owner: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ITSystemListResponse(BaseModel):
    status: str = "success"
    data: list[ITSystemResponse]
    meta: dict


class ITSystemCreate(BaseModel):
    name: str
    tier: str = "tier3"
    status: str = "operational"
    rto_minutes: int = 240
    rpo_minutes: int = 60
    description: str | None = None
    owner: str | None = None
