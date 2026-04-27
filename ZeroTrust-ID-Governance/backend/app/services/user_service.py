import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID | str) -> User | None:
    result = await db.execute(select(User).where(User.id == str(user_id)))
    return result.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    user = await get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if user.status != "active":
        return None
    return user


async def create_user(db: AsyncSession, data: UserCreate) -> User:
    user = User(
        employee_id=data.employee_id,
        username=data.username,
        email=data.email,
        display_name=data.display_name,
        department=data.department,
        user_type=data.user_type,
        hashed_password=get_password_hash(data.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user(db: AsyncSession, user: User, data: UserUpdate) -> User:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user: User) -> None:
    await db.delete(user)
    await db.commit()


async def list_users(
    db: AsyncSession, page: int = 1, page_size: int = 20
) -> tuple[list[User], int]:
    offset = (page - 1) * page_size
    count_result = await db.execute(select(func.count()).select_from(User))
    total = count_result.scalar_one()
    result = await db.execute(select(User).offset(offset).limit(page_size))
    users = list(result.scalars().all())
    return users, total
