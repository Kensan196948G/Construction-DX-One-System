"""Initialize database tables and create admin user."""
import asyncio
import sys

from app.core.config import get_settings
from app.core.database import Base, engine
from app.core.security import get_password_hash
from app.models import *  # noqa: F401, F403 - load all models

settings = get_settings()


async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created.")

    # Create admin user
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    from app.models.user import User

    AsyncSession_ = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSession_() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.username == "admin"))
        if result.scalar_one_or_none():
            print("Admin user already exists.")
            return

        admin = User(
            employee_id="EMP0001",
            username="admin",
            email="admin@miraikensetu.co.jp",
            display_name="システム管理者",
            hashed_password=get_password_hash("Admin@1234"),
            user_type="admin",
            status="active",
        )
        session.add(admin)
        await session.commit()
        print("Admin user created: admin / Admin@1234")


if __name__ == "__main__":
    asyncio.run(init())
