import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.user import User


async def _create_admin(db: AsyncSession) -> tuple[User, str]:
    user = User(
        employee_id="ADM001",
        username="admin",
        email="admin@miraikensetu.co.jp",
        display_name="システム管理者",
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
async def test_create_user(client: AsyncClient, db_session: AsyncSession):
    _, token = await _create_admin(db_session)
    response = await client.post(
        "/api/v1/users",
        json={
            "employee_id": "EMP002",
            "username": "newuser",
            "email": "newuser@miraikensetu.co.jp",
            "display_name": "新規ユーザー",
            "password": "pass1234",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_users(client: AsyncClient, db_session: AsyncSession):
    _, token = await _create_admin(db_session)
    response = await client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_user(client: AsyncClient, db_session: AsyncSession):
    admin, token = await _create_admin(db_session)
    response = await client.get(
        f"/api/v1/users/{admin.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["username"] == "admin"


@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient, db_session: AsyncSession):
    _, token = await _create_admin(db_session)
    response = await client.get(
        "/api/v1/users/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_user(client: AsyncClient, db_session: AsyncSession):
    admin, token = await _create_admin(db_session)
    response = await client.put(
        f"/api/v1/users/{admin.id}",
        json={"display_name": "更新後管理者"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["display_name"] == "更新後管理者"


@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient, db_session: AsyncSession):
    admin, token = await _create_admin(db_session)
    # Create a second user to delete
    create_resp = await client.post(
        "/api/v1/users",
        json={
            "employee_id": "EMP099",
            "username": "todelete",
            "email": "todelete@miraikensetu.co.jp",
            "display_name": "削除対象",
            "password": "pass1234",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    user_id = create_resp.json()["id"]
    response = await client.delete(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_users_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/users")
    assert response.status_code in (401, 403)
