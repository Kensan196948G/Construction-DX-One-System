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


async def _create_test_user(db: AsyncSession) -> tuple[User, str]:
    user = User(
        employee_id="EMP002",
        username="testuser",
        email="testuser@miraikensetu.co.jp",
        display_name="テストユーザー",
        hashed_password=get_password_hash("testpass123"),
        user_type="regular",
        status="active",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token(str(user.id))
    return user, token


@pytest.mark.asyncio
async def test_create_role(client: AsyncClient, db_session: AsyncSession):
    _, token = await _create_admin(db_session)
    response = await client.post(
        "/api/v1/roles",
        json={
            "name": "admin",
            "description": "Administrator role",
            "permissions": ["user:read", "user:write"],
            "is_privileged": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "admin"
    assert data["is_privileged"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_list_roles(client: AsyncClient, db_session: AsyncSession):
    _, token = await _create_admin(db_session)
    # Create a role first
    await client.post(
        "/api/v1/roles",
        json={"name": "viewer", "permissions": ["user:read"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    response = await client.get(
        "/api/v1/roles",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_role(client: AsyncClient, db_session: AsyncSession):
    _, token = await _create_admin(db_session)
    create_resp = await client.post(
        "/api/v1/roles",
        json={"name": "editor", "permissions": ["user:read"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    role_id = create_resp.json()["id"]
    response = await client.get(
        f"/api/v1/roles/{role_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "editor"


@pytest.mark.asyncio
async def test_get_role_not_found(client: AsyncClient, db_session: AsyncSession):
    _, token = await _create_admin(db_session)
    response = await client.get(
        "/api/v1/roles/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_role(client: AsyncClient, db_session: AsyncSession):
    _, token = await _create_admin(db_session)
    create_resp = await client.post(
        "/api/v1/roles",
        json={"name": "toupdate", "permissions": ["user:read"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    role_id = create_resp.json()["id"]
    response = await client.put(
        f"/api/v1/roles/{role_id}",
        json={"name": "updated", "description": "Updated description"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "updated"
    assert response.json()["description"] == "Updated description"


@pytest.mark.asyncio
async def test_delete_role(client: AsyncClient, db_session: AsyncSession):
    _, token = await _create_admin(db_session)
    create_resp = await client.post(
        "/api/v1/roles",
        json={"name": "todelete", "permissions": []},
        headers={"Authorization": f"Bearer {token}"},
    )
    role_id = create_resp.json()["id"]
    response = await client.delete(
        f"/api/v1/roles/{role_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_assign_role_to_user(client: AsyncClient, db_session: AsyncSession):
    admin, admin_token = await _create_admin(db_session)
    test_user, _ = await _create_test_user(db_session)

    create_resp = await client.post(
        "/api/v1/roles",
        json={"name": "assignable", "permissions": ["user:read"]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    role_id = create_resp.json()["id"]

    response = await client.post(
        f"/api/v1/roles/{role_id}/assign",
        json={"user_id": str(test_user.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_revoke_role(client: AsyncClient, db_session: AsyncSession):
    admin, admin_token = await _create_admin(db_session)
    test_user, _ = await _create_test_user(db_session)

    create_resp = await client.post(
        "/api/v1/roles",
        json={"name": "revocable", "permissions": ["user:read"]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    role_id = create_resp.json()["id"]

    # Assign first
    await client.post(
        f"/api/v1/roles/{role_id}/assign",
        json={"user_id": str(test_user.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Revoke
    response = await client.delete(
        f"/api/v1/roles/{role_id}/revoke/{test_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 204
