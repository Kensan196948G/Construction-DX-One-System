from datetime import datetime

from pydantic import BaseModel


class SCIMUserSync(BaseModel):
    user_id: str
    synced: bool
    sync_status: str
    scim_id: str | None = None
    synced_at: datetime | None = None
    details: dict | None = None


class SCIMSyncStatus(BaseModel):
    user_id: str
    hengeone_user_id: str | None = None
    sync_status: str
    last_synced_at: datetime | None = None
    errors: list[str] = []


class SCIMGroupSyncResult(BaseModel):
    group_name: str
    synced: bool
    members_synced: int
    details: dict | None = None


class SCIMGroupSync(BaseModel):
    total: int
    succeeded: int
    failed: int
    results: list[SCIMGroupSyncResult]
