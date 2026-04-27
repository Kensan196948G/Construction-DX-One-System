import uuid
from datetime import datetime

from pydantic import BaseModel


class RoleCreate(BaseModel):
    name: str
    description: str | None = None
    permissions: list[str] = []
    is_privileged: bool = False


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    permissions: list[str] | None = None
    is_privileged: bool | None = None


class RoleRead(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    permissions: list[str]
    is_privileged: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class RoleAssign(BaseModel):
    user_id: uuid.UUID
    expires_at: datetime | None = None
