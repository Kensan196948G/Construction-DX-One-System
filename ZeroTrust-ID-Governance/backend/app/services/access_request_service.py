from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import AccessRequest
from app.schemas.access_request import AccessRequestCreate, AccessRequestReview


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


async def create_request(
    db: AsyncSession, requester_id: str, payload: AccessRequestCreate
) -> AccessRequest:
    request = AccessRequest(
        requester_id=requester_id,
        target_resource=payload.target_resource,
        justification=payload.justification,
        requested_role_id=payload.requested_role_id,
        status="pending",
    )
    db.add(request)
    await db.commit()
    await db.refresh(request)
    return request


async def get_request(db: AsyncSession, request_id: str) -> AccessRequest | None:
    result = await db.execute(select(AccessRequest).where(AccessRequest.id == request_id))
    return result.scalar_one_or_none()


async def list_requests(
    db: AsyncSession,
    status_filter: str | None = None,
    requester_id: str | None = None,
) -> list[AccessRequest]:
    query = select(AccessRequest)
    if status_filter:
        query = query.where(AccessRequest.status == status_filter)
    if requester_id:
        query = query.where(AccessRequest.requester_id == requester_id)
    query = query.order_by(AccessRequest.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def review_request(
    db: AsyncSession,
    request_id: str,
    approver_id: str,
    payload: AccessRequestReview,
) -> AccessRequest:
    request = await get_request(db, request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Access request not found")
    if request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot review request with status '{request.status}'",
        )

    request.status = payload.status
    request.approver_id = approver_id
    request.reviewed_at = _now()
    await db.commit()
    await db.refresh(request)
    return request


async def cancel_request(db: AsyncSession, request_id: str, user_id: str) -> AccessRequest:
    request = await get_request(db, request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Access request not found")
    if request.requester_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You can only cancel your own requests"
        )
    if request.status not in ("pending", "in_review"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel request with status '{request.status}'",
        )

    request.status = "cancelled"
    await db.commit()
    await db.refresh(request)
    return request


async def get_pending_requests(db: AsyncSession) -> list[AccessRequest]:
    result = await db.execute(
        select(AccessRequest)
        .where(AccessRequest.status == "pending")
        .order_by(AccessRequest.created_at.desc())
    )
    return list(result.scalars().all())
