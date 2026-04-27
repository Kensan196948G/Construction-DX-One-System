import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import UserCreate
from app.services.auth_service import create_user


@pytest.mark.asyncio
async def test_register(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"username": "analyst01", "email": "analyst01@test.com", "password": "Passw0rd!"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "analyst01"
    assert data["role"] == "analyst"


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, db: AsyncSession) -> None:
    await create_user(db, UserCreate(username="user1", email="u1@test.com", password="Secret123"))
    await db.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "user1", "password": "Secret123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, db: AsyncSession) -> None:
    await create_user(db, UserCreate(username="user2", email="u2@test.com", password="Correct99"))
    await db.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "user2", "password": "WrongPass"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, db: AsyncSession) -> None:
    await create_user(db, UserCreate(username="user3", email="u3@test.com", password="Pass1234"))
    await db.commit()

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": "user3", "password": "Pass1234"},
    )
    assert login_res.status_code == 200
    refresh_token = login_res.json()["refresh_token"]

    refresh_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 200
    assert "access_token" in refresh_res.json()
