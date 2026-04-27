from datetime import datetime

from pydantic import BaseModel


class PIRCreate(BaseModel):
    rfc_id: str


class PIRUpdate(BaseModel):
    review_status: str | None = None
    reviewer_id: str | None = None
    was_successful: bool | None = None
    issues_encountered: str | None = None
    lessons_learned: str | None = None
    rollback_effectiveness: str | None = None
    recommendation: str | None = None
    follow_up_actions: list[dict] | None = None


class PIRCompleteReview(BaseModel):
    reviewer_id: str
    was_successful: bool
    issues_encountered: str | None = None
    lessons_learned: str | None = None
    rollback_effectiveness: str | None = None
    recommendation: str | None = None
    follow_up_actions: list[dict] | None = None


class PIRResponse(BaseModel):
    id: str
    rfc_id: str
    review_status: str
    reviewer_id: str | None
    review_date: datetime | None
    actual_start_time: datetime | None
    actual_end_time: datetime | None
    was_successful: bool | None
    issues_encountered: str | None
    lessons_learned: str | None
    rollback_effectiveness: str | None
    recommendation: str | None
    follow_up_actions: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PIRSummary(BaseModel):
    completion_rate: float
    overdue_count: int
    avg_review_time: float | None
    recent_pirs: list[PIRResponse]


class PIRListResponse(BaseModel):
    status: str = "success"
    data: list[PIRResponse]
    meta: dict
