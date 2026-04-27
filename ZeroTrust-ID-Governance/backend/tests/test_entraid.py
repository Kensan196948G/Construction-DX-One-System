import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.user import User


async def _create_admin(db: AsyncSession) -> tuple[User, str]:
    user = User(
        employee_id="EADM001",
        username="entradmin",
        email="entradmin@miraikensetu.co.jp",
        display_name="EntraID管理者",
        hashed_password=get_password_hash("adminpass123"),
        user_type="admin",
        status="active",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token(str(user.id))
    return user, token


async def _create_regular_user(db: AsyncSession) -> tuple[User, str]:
    user = User(
        employee_id="EUSR001",
        username="entrauser",
        email="entrauser@miraikensetu.co.jp",
        display_name="EntraID一般ユーザー",
        hashed_password=get_password_hash("userpass123"),
        user_type="regular",
        status="active",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user, create_access_token(str(user.id))


@pytest.mark.asyncio
async def test_sync_user_create(client: AsyncClient, db_session: AsyncSession):
    admin, token = await _create_admin(db_session)

    # create a user to sync
    create_resp = await client.post(
        "/api/v1/users",
        json={
            "employee_id": "ESYNC01",
            "username": "syncuser",
            "email": "syncuser@miraikensetu.co.jp",
            "display_name": "同期ユーザー",
            "password": "pass1234",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_resp.status_code == 201
    user_id = create_resp.json()["id"]

    response = await client.post(
        f"/api/v1/external/entraid/sync/user/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["synced"] is True
    assert data["sync_status"] == "synced"
    assert "user_id" in data


@pytest.mark.asyncio
async def test_sync_user_not_found(client: AsyncClient, db_session: AsyncSession):
    _, token = await _create_admin(db_session)
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.post(
        f"/api/v1/external/entraid/sync/user/{fake_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_sync_status(client: AsyncClient, db_session: AsyncSession):
    admin, token = await _create_admin(db_session)

    response = await client.get(
        f"/api/v1/external/entraid/status/{admin.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == str(admin.id)
    assert data["sync_status"] in ("pending", "synced")


@pytest.mark.asyncio
async def test_sync_status_unknown_user(client: AsyncClient, db_session: AsyncSession):
    _, token = await _create_admin(db_session)
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(
        f"/api/v1/external/entraid/status/{fake_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["sync_status"] == "unknown"


@pytest.mark.asyncio
async def test_bulk_sync(client: AsyncClient, db_session: AsyncSession):
    admin, token = await _create_admin(db_session)

    # create a few users
    for i in range(3):
        await client.post(
            "/api/v1/users",
            json={
                "employee_id": f"EBULK{i:03d}",
                "username": f"bulkuser{i}",
                "email": f"bulkuser{i}@miraikensetu.co.jp",
                "display_name": f"一括同期{i}",
                "password": "pass1234",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    response = await client.post(
        "/api/v1/external/entraid/sync/bulk",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 4
    assert data["succeeded"] >= 4
    assert data["failed"] == 0
    assert len(data["results"]) >= 4


@pytest.mark.asyncio
async def test_overall_sync_status(client: AsyncClient, db_session: AsyncSession):
    admin, token = await _create_admin(db_session)

    response = await client.get(
        "/api/v1/external/entraid/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "user_id" in data[0]
    assert "sync_status" in data[0]
