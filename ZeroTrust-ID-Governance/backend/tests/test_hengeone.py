import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.user import User


async def _create_admin(db: AsyncSession) -> tuple[User, str]:
    user = User(
        employee_id="HADM001",
        username="hengeadmin",
        email="hengeadmin@miraikensetu.co.jp",
        display_name="HENGEONE管理者",
        hashed_password=get_password_hash("adminpass123"),
        user_type="admin",
        status="active",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token(str(user.id))
    return user, token


@pytest.mark.asyncio
async def test_sync_user(client: AsyncClient, db_session: AsyncSession):
    admin, token = await _create_admin(db_session)

    create_resp = await client.post(
        "/api/v1/users",
        json={
            "employee_id": "HSYNC01",
            "username": "hengeuser",
            "email": "hengeuser@miraikensetu.co.jp",
            "display_name": "HENGE同期ユーザー",
            "password": "pass1234",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_resp.status_code == 201
    user_id = create_resp.json()["id"]

    response = await client.post(
        f"/api/v1/external/hengeone/sync/user/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["synced"] is True
    assert data["sync_status"] == "synced"
    assert "scim_id" in data


@pytest.mark.asyncio
async def test_sync_user_not_found(client: AsyncClient, db_session: AsyncSession):
    _, token = await _create_admin(db_session)
    response = await client.post(
        "/api/v1/external/hengeone/sync/user/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_sync_status(client: AsyncClient, db_session: AsyncSession):
    admin, token = await _create_admin(db_session)

    response = await client.get(
        f"/api/v1/external/hengeone/status/{admin.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == str(admin.id)
    assert data["sync_status"] in ("pending", "synced")


@pytest.mark.asyncio
async def test_group_sync(client: AsyncClient, db_session: AsyncSession):
    admin, token = await _create_admin(db_session)

    user = User(
        employee_id="HDEPT01",
        username="deptuser",
        email="deptuser@miraikensetu.co.jp",
        display_name="部署ユーザー",
        hashed_password=get_password_hash("pass1234"),
        department="工事部",
        status="active",
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/v1/external/hengeone/sync/groups",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert "results" in data
