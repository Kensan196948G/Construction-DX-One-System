from datetime import datetime

from pydantic import BaseModel


class AuditLogRead(BaseModel):
    id: int
    action: str
    actor_id: str | None = None
    actor_ip: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    payload: dict | None = None
    result: str | None = None
    prev_hash: str | None = None
    hash: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChainVerificationResult(BaseModel):
    valid: bool
    broken_at: str | None = None
    total_entries: int
    checked_entries: int


class ChainStats(BaseModel):
    total_entries: int
    first_entry_at: datetime | None = None
    last_entry_at: datetime | None = None
    action_breakdown: dict[str, int]
