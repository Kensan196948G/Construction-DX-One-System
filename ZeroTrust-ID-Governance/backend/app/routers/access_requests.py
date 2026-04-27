from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.schemas.access_request import AccessRequestCreate, AccessRequestRead, AccessRequestReview
from app.services.access_request_service import (
    cancel_request,
    create_request,
    get_request,
    list_requests,
    review_request,
)

router = APIRouter(prefix="/access-requests", tags=["access-requests"])
bearer_scheme = HTTPBearer()


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> str:
    data = decode_token(credentials.credentials)
    sub = data.get("sub")
    if not sub or data.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return sub


@router.post("", response_model=AccessRequestRead, status_code=status.HTTP_201_CREATED)
async def create_access_request_endpoint(
    payload: AccessRequestCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    request = await create_request(db, user_id, payload)
    return AccessRequestRead.model_validate(request)


@router.get("", response_model=list[AccessRequestRead])
async def list_access_requests_endpoint(
    status: str | None = Query(None),
    requester_id: str | None = Query(None),
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    requests = await list_requests(db, status_filter=status, requester_id=requester_id)
    return [AccessRequestRead.model_validate(r) for r in requests]


@router.get("/{request_id}", response_model=AccessRequestRead)
async def get_access_request_endpoint(
    request_id: str,
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    request = await get_request(db, request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Access request not found")
    return AccessRequestRead.model_validate(request)


@router.put("/{request_id}/review", response_model=AccessRequestRead)
async def review_access_request_endpoint(
    request_id: str,
    payload: AccessRequestReview,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    request = await review_request(db, request_id, user_id, payload)
    return AccessRequestRead.model_validate(request)


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_access_request_endpoint(
    request_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await cancel_request(db, request_id, user_id)
