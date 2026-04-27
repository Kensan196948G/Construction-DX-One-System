import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.schemas.user import UserCreate, UserListResponse, UserResponse, UserUpdate
from app.services.audit_service import log_action
from app.services.user_service import (
    create_user,
    delete_user,
    get_user_by_id,
    list_users,
    suspend_user,
    update_user,
)

router = APIRouter(prefix="/users", tags=["users"])
bearer_scheme = HTTPBearer()


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> str:
    data = decode_token(credentials.credentials)
    sub = data.get("sub")
    if not sub or data.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return sub


@router.get("", response_model=UserListResponse)
async def list_users_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    users, total = await list_users(db, page=page, page_size=page_size)
    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    payload: UserCreate,
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await create_user(db, payload)
    await log_action(
        db, action="user_create", actor_id=_user_id,
        target_type="user", target_id=str(user.id),
        payload={"username": user.username, "email": user.email},
        result="success",
    )
    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_endpoint(
    user_id: uuid.UUID,
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user_endpoint(
    user_id: uuid.UUID,
    payload: UserUpdate,
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user = await update_user(db, user, payload)
    await log_action(
        db, action="user_update", actor_id=_user_id,
        target_type="user", target_id=str(user.id),
        payload=payload.model_dump(exclude_unset=True),
        result="success",
    )
    return UserResponse.model_validate(user)


@router.put("/{user_id}/suspend", response_model=UserResponse)
async def suspend_user_endpoint(
    user_id: uuid.UUID,
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user = await suspend_user(db, user)
    await log_action(
        db, action="user_suspend", actor_id=_user_id,
        target_type="user", target_id=str(user.id), result="success",
    )
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(
    user_id: uuid.UUID,
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await log_action(
        db, action="user_delete", actor_id=_user_id,
        target_type="user", target_id=str(user.id), result="success",
    )
    await delete_user(db, user)
