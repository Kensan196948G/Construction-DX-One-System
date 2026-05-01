import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pir import PIR
from app.schemas.pir import PIRCompleteReview, PIRUpdate


async def create_pir(db: AsyncSession, rfc_id: str) -> PIR:
    pir = PIR(id=str(uuid.uuid4()), rfc_id=rfc_id)
    db.add(pir)
    await db.commit()
    await db.refresh(pir)
    return pir


async def get_pir(db: AsyncSession, pir_id: str) -> PIR | None:
    result = await db.execute(select(PIR).where(PIR.id == pir_id))
    return result.scalar_one_or_none()


async def get_pir_by_rfc(db: AsyncSession, rfc_id: str) -> PIR | None:
    result = await db.execute(select(PIR).where(PIR.rfc_id == rfc_id))
    return result.scalar_one_or_none()


async def update_pir(db: AsyncSession, pir_id: str, payload: PIRUpdate) -> PIR | None:
    pir = await get_pir(db, pir_id)
    if not pir:
        return None

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(pir, key, value)
    pir.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(pir)
    return pir


async def list_pirs(
    db: AsyncSession,
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[PIR]:
    query = select(PIR).order_by(PIR.created_at.desc())
    if status_filter:
        query = query.where(PIR.review_status == status_filter)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_pir_summary(db: AsyncSession) -> dict:
    total_result = await db.execute(select(func.count(PIR.id)))
    total = total_result.scalar() or 0

    completed_result = await db.execute(
        select(func.count(PIR.id)).where(PIR.review_status == "completed")
    )
    completed = completed_result.scalar() or 0

    overdue_result = await db.execute(
        select(func.count(PIR.id)).where(PIR.review_status == "overdue")
    )
    overdue = overdue_result.scalar() or 0

    completion_rate = (completed / total * 100) if total > 0 else 0.0

    avg_time_result = await db.execute(
        select(
            func.avg(
                (func.julianday(PIR.review_date) - func.julianday(PIR.created_at)) * 86400
            )
        ).where(
            PIR.review_status == "completed",
            PIR.review_date.isnot(None),
        )
    )
    avg_seconds = avg_time_result.scalar()
    avg_review_time = float(avg_seconds) if avg_seconds is not None else None

    recent_result = await db.execute(
        select(PIR).order_by(PIR.created_at.desc()).limit(5)
    )
    recent_pirs = list(recent_result.scalars().all())

    return {
        "completion_rate": round(completion_rate, 2),
        "overdue_count": overdue,
        "avg_review_time": avg_review_time,
        "recent_pirs": recent_pirs,
    }


async def complete_review(
    db: AsyncSession,
    pir_id: str,
    reviewer_id: str,
    payload: PIRCompleteReview,
) -> PIR | None:
    pir = await get_pir(db, pir_id)
    if not pir:
        return None

    pir.review_status = "completed"
    pir.reviewer_id = reviewer_id
    pir.review_date = datetime.now(UTC)
    pir.was_successful = payload.was_successful
    pir.issues_encountered = payload.issues_encountered
    pir.lessons_learned = payload.lessons_learned
    pir.rollback_effectiveness = payload.rollback_effectiveness
    pir.recommendation = payload.recommendation
    if payload.follow_up_actions:
        pir.follow_up_actions = {"items": payload.follow_up_actions}
    pir.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(pir)
    return pir


async def mark_overdue(db: AsyncSession) -> list[PIR]:
    seven_days_ago = datetime.now(UTC) - timedelta(days=7)
    query = select(PIR).where(
        PIR.review_status.in_(["pending", "in_review"]),
        PIR.created_at < seven_days_ago,
    )
    result = await db.execute(query)
    overdue_pirs = list(result.scalars().all())
    for pir in overdue_pirs:
        pir.review_status = "overdue"
        pir.updated_at = datetime.now(UTC)
    await db.commit()
    for pir in overdue_pirs:
        await db.refresh(pir)
    return overdue_pirs
