import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.user import User


async def _create_admin(db: AsyncSession) -> tuple[User, str]:
    user = User(
        employee_id="AADM001",
        username="adadmin",
        email="adadmin@miraikensetu.co.jp",
        display_name="AD管理者",
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
            "employee_id": "ASYNC01",
            "username": "aduser",
            "email": "aduser@miraikensetu.co.jp",
            "display_name": "AD同期ユーザー",
            "password": "pass1234",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_resp.status_code == 201
    user_id = create_resp.json()["id"]

    response = await client.post(
        f"/api/v1/external/ad/sync/user/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["synced"] is True
    assert data["sync_status"] == "synced"
    assert "ad_object_id" in data


@pytest.mark.asyncio
async def test_sync_user_not_found(client: AsyncClient, db_session: AsyncSession):
    _, token = await _create_admin(db_session)
    response = await client.post(
        "/api/v1/external/ad/sync/user/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_sync_status(client: AsyncClient, db_session: AsyncSession):
    admin, token = await _create_admin(db_session)

    response = await client.get(
        f"/api/v1/external/ad/status/{admin.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == str(admin.id)
    assert data["sync_status"] in ("pending", "synced")


@pytest.mark.asyncio
async def test_bulk_sync(client: AsyncClient, db_session: AsyncSession):
    admin, token = await _create_admin(db_session)

    for i in range(3):
        await client.post(
            "/api/v1/users",
            json={
                "employee_id": f"ABULK{i:03d}",
                "username": f"adbulkuser{i}",
                "email": f"adbulkuser{i}@miraikensetu.co.jp",
                "display_name": f"AD一括同期{i}",
                "password": "pass1234",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    response = await client.post(
        "/api/v1/external/ad/sync/bulk",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 4
    assert data["succeeded"] >= 4
    assert data["failed"] == 0
    assert len(data["results"]) >= 4
