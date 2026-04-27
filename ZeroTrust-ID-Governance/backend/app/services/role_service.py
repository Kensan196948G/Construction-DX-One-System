import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Role, User, UserRole
from app.schemas.role import RoleCreate, RoleUpdate


async def create_role(db: AsyncSession, payload: RoleCreate) -> Role:
    role = Role(
        name=payload.name,
        description=payload.description,
        permissions=payload.permissions,
        is_privileged=payload.is_privileged,
    )
    db.add(role)
    try:
        await db.commit()
        await db.refresh(role)
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Role name already exists",
        )
    return role


async def get_role(db: AsyncSession, role_id: uuid.UUID | str) -> Role | None:
    result = await db.execute(select(Role).where(Role.id == str(role_id)))
    return result.scalar_one_or_none()


async def list_roles(db: AsyncSession) -> list[Role]:
    result = await db.execute(select(Role).order_by(Role.name))
    return list(result.scalars().all())


async def update_role(db: AsyncSession, role: Role, payload: RoleUpdate) -> Role:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(role, field, value)
    try:
        await db.commit()
        await db.refresh(role)
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Role name already exists",
        )
    return role


async def delete_role(db: AsyncSession, role: Role) -> None:
    await db.delete(role)
    await db.commit()


async def assign_role(
    db: AsyncSession, user_id: uuid.UUID | str, role_id: uuid.UUID | str, expires_at=None
) -> UserRole:
    user_result = await db.execute(select(User).where(User.id == str(user_id)))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    role_result = await db.execute(select(Role).where(Role.id == str(role_id)))
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    existing = await db.execute(
        select(UserRole).where(
            UserRole.user_id == str(user_id), UserRole.role_id == str(role_id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already has this role",
        )

    user_role = UserRole(user_id=str(user_id), role_id=str(role_id), expires_at=expires_at)
    db.add(user_role)
    await db.commit()
    await db.refresh(user_role)
    return user_role


async def revoke_role(db: AsyncSession, user_id: uuid.UUID | str, role_id: uuid.UUID | str) -> None:
    result = await db.execute(
        select(UserRole).where(
            UserRole.user_id == str(user_id), UserRole.role_id == str(role_id)
        )
    )
    user_role = result.scalar_one_or_none()
    if not user_role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role assignment not found")
    await db.delete(user_role)
    await db.commit()
