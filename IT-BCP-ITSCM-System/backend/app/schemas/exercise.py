from datetime import date, datetime

from pydantic import BaseModel


class ExerciseCreate(BaseModel):
    title: str
    exercise_type: str = "tabletop"
    scheduled_date: date | None = None
    participants: int = 0
    description: str | None = None


class ExerciseResponse(BaseModel):
    id: str
    title: str
    exercise_type: str
    status: str
    scheduled_date: date | None
    completed_date: date | None
    participants: int
    results: str | None
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExerciseListResponse(BaseModel):
    status: str = "success"
    data: list[ExerciseResponse]
    meta: dict
