import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.exercise import Exercise
from app.schemas.exercise import ExerciseCreate, ExerciseListResponse, ExerciseResponse

router = APIRouter()


@router.get("/exercises", response_model=ExerciseListResponse)
async def list_exercises(
    exercise_type: str | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Exercise).order_by(Exercise.created_at.desc())
    if exercise_type:
        query = query.where(Exercise.exercise_type == exercise_type)
    if status:
        query = query.where(Exercise.status == status)

    result = await db.execute(query)
    exercises = result.scalars().all()

    return ExerciseListResponse(
        data=[ExerciseResponse.model_validate(e) for e in exercises],
        meta={"total": len(exercises)},
    )


@router.post("/exercises", response_model=ExerciseResponse, status_code=201)
async def create_exercise(payload: ExerciseCreate, db: AsyncSession = Depends(get_db)):
    exercise = Exercise(
        id=str(uuid.uuid4()),
        title=payload.title,
        exercise_type=payload.exercise_type,
        scheduled_date=payload.scheduled_date,
        participants=payload.participants,
        description=payload.description,
    )
    db.add(exercise)
    await db.commit()
    await db.refresh(exercise)
    return ExerciseResponse.model_validate(exercise)


@router.get("/exercises/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(exercise_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Exercise).where(Exercise.id == exercise_id))
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return ExerciseResponse.model_validate(exercise)


@router.patch("/exercises/{exercise_id}/complete", response_model=ExerciseResponse)
async def complete_exercise(
    exercise_id: str,
    results: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Exercise).where(Exercise.id == exercise_id))
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    exercise.status = "completed"
    exercise.completed_date = date.today()
    if results:
        exercise.results = results
    exercise.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(exercise)
    return ExerciseResponse.model_validate(exercise)
