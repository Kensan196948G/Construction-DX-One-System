import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.schemas.role import RoleAssign, RoleCreate, RoleRead, RoleUpdate
from app.services.audit_service import log_action
from app.services.role_service import (
    assign_role,
    create_role,
    delete_role,
    get_role,
    list_roles,
    revoke_role,
    update_role,
)
from app.services.user_service import get_user_by_id

router = APIRouter(prefix="/roles", tags=["roles"])
bearer_scheme = HTTPBearer()


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> str:
    data = decode_token(credentials.credentials)
    sub = data.get("sub")
    if not sub or data.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return sub


@router.post("", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_role_endpoint(
    payload: RoleCreate,
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    role = await create_role(db, payload)
    await log_action(
        db, action="role_create", actor_id=_user_id,
        target_type="role", target_id=str(role.id),
        payload={"name": role.name}, result="success",
    )
    return RoleRead.model_validate(role)


@router.get("", response_model=list[RoleRead])
async def list_roles_endpoint(
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    roles = await list_roles(db)
    return [RoleRead.model_validate(r) for r in roles]


@router.get("/{role_id}", response_model=RoleRead)
async def get_role_endpoint(
    role_id: uuid.UUID,
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    role = await get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return RoleRead.model_validate(role)


@router.put("/{role_id}", response_model=RoleRead)
async def update_role_endpoint(
    role_id: uuid.UUID,
    payload: RoleUpdate,
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    role = await get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    role = await update_role(db, role, payload)
    await log_action(
        db, action="role_update", actor_id=_user_id,
        target_type="role", target_id=str(role.id),
        payload=payload.model_dump(exclude_unset=True), result="success",
    )
    return RoleRead.model_validate(role)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role_endpoint(
    role_id: uuid.UUID,
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    role = await get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    await log_action(
        db, action="role_delete", actor_id=_user_id,
        target_type="role", target_id=str(role.id), result="success",
    )
    await delete_role(db, role)


@router.post("/{role_id}/assign", response_model=RoleRead)
async def assign_role_endpoint(
    role_id: uuid.UUID,
    payload: RoleAssign,
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_id(db, payload.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    role = await get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    await assign_role(db, payload.user_id, role_id, payload.expires_at)
    await log_action(
        db, action="role_assign", actor_id=_user_id,
        target_type="role", target_id=str(role_id),
        payload={"user_id": str(payload.user_id)}, result="success",
    )
    return RoleRead.model_validate(role)


@router.delete("/{role_id}/revoke/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_role_endpoint(
    role_id: uuid.UUID,
    user_id: uuid.UUID,
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    role = await get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    await log_action(
        db, action="role_revoke", actor_id=_user_id,
        target_type="role", target_id=str(role_id),
        payload={"user_id": str(user_id)}, result="success",
    )
    await revoke_role(db, user_id, role_id)
