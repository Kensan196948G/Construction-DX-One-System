from datetime import datetime

from pydantic import BaseModel


class EntraIDUserSync(BaseModel):
    user_id: str
    synced: bool
    sync_status: str
    synced_at: datetime | None = None
    details: dict | None = None


class EntraIDSyncStatus(BaseModel):
    user_id: str
    entra_object_id: str | None = None
    sync_status: str
    last_synced_at: datetime | None = None
    errors: list[str] = []


class BulkSyncResult(BaseModel):
    total: int
    succeeded: int
    failed: int
    results: list[EntraIDUserSync]
