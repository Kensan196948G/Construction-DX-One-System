from datetime import datetime

from pydantic import BaseModel


class ADUserSync(BaseModel):
    user_id: str
    synced: bool
    sync_status: str
    ad_object_id: str | None = None
    synced_at: datetime | None = None
    details: dict | None = None


class ADSyncStatus(BaseModel):
    user_id: str
    ad_object_id: str | None = None
    sync_status: str
    last_synced_at: datetime | None = None
    errors: list[str] = []


class ADBulkSyncResult(BaseModel):
    total: int
    succeeded: int
    failed: int
    results: list[ADUserSync]
