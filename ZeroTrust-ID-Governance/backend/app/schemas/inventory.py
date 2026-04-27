from datetime import date, datetime

from pydantic import BaseModel


class InventoryCampaignCreate(BaseModel):
    name: str
    description: str | None = None
    review_period_start: date
    review_period_end: date


class InventoryCampaignUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    review_period_start: date | None = None
    review_period_end: date | None = None


class InventoryCampaignRead(BaseModel):
    id: str
    name: str
    description: str | None = None
    status: str
    review_period_start: date
    review_period_end: date
    total_accounts: int = 0
    reviewed_count: int = 0
    flagged_count: int = 0
    created_by: str
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InventoryItemRead(BaseModel):
    id: str
    campaign_id: str
    user_id: str
    status: str = "pending"
    reviewer_notes: str | None = None
    last_login_days: int | None = None
    risk_level: str | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InventoryItemUpdate(BaseModel):
    status: str
    reviewer_notes: str | None = None
    risk_level: str | None = None


class CampaignSummary(BaseModel):
    total: int
    reviewed: int
    flagged: int
    completion_rate: float
    high_risk_count: int
