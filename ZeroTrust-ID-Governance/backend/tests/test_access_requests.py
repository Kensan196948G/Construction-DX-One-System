import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.user import User


async def _create_requester(db: AsyncSession) -> tuple[User, str]:
    user = User(
        employee_id="REQ001",
        username="requester",
        email="requester@example.com",
        display_name="リクエスター",
        hashed_password=get_password_hash("pass123"),
        user_type="regular",
        status="active",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token(str(user.id))
    return user, token


async def _create_approver(db: AsyncSession) -> tuple[User, str]:
    user = User(
        employee_id="APR001",
        username="approver",
        email="approver@example.com",
        display_name="承認者",
        hashed_password=get_password_hash("pass123"),
        user_type="admin",
        status="active",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token(str(user.id))
    return user, token


async def _create_request(db: AsyncSession, client: AsyncClient, token: str) -> dict:
    resp = await client.post(
        "/api/v1/access-requests",
        json={
            "target_resource": "project-x-database",
            "justification": "Need access for development",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp.json()


@pytest.mark.asyncio
async def test_create_request(client: AsyncClient, db_session: AsyncSession):
    _, token = await _create_requester(db_session)
    response = await client.post(
        "/api/v1/access-requests",
        json={
            "target_resource": "production-db",
            "justification": "Bug fix required",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["target_resource"] == "production-db"
    assert data["justification"] == "Bug fix required"
    assert data["status"] == "pending"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_requests(client: AsyncClient, db_session: AsyncSession):
    user, token = await _create_requester(db_session)
    await _create_request(db_session, client, token)
    await _create_request(db_session, client, token)

    response = await client.get(
        "/api/v1/access-requests",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_list_requests_filter_status(client: AsyncClient, db_session: AsyncSession):
    user, token = await _create_requester(db_session)
    await _create_request(db_session, client, token)

    # Create another user to approve and cancel
    approver, approver_token = await _create_approver(db_session)
    req = await _create_request(db_session, client, token)

    # Cancel the second request
    await client.delete(
        f"/api/v1/access-requests/{req['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Filter by pending
    response = await client.get(
        "/api/v1/access-requests?status=pending",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert all(r["status"] == "pending" for r in data)


@pytest.mark.asyncio
async def test_get_request(client: AsyncClient, db_session: AsyncSession):
    _, token = await _create_requester(db_session)
    created = await _create_request(db_session, client, token)

    response = await client.get(
        f"/api/v1/access-requests/{created['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


@pytest.mark.asyncio
async def test_get_request_not_found(client: AsyncClient, db_session: AsyncSession):
    _, token = await _create_requester(db_session)
    response = await client.get(
        "/api/v1/access-requests/nonexistent-id",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_approve_request(client: AsyncClient, db_session: AsyncSession):
    _, requester_token = await _create_requester(db_session)
    created = await _create_request(db_session, client, requester_token)

    approver, approver_token = await _create_approver(db_session)
    response = await client.put(
        f"/api/v1/access-requests/{created['id']}/review",
        json={"status": "approved"},
        headers={"Authorization": f"Bearer {approver_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert data["approver_id"] == str(approver.id)
    assert data["reviewed_at"] is not None


@pytest.mark.asyncio
async def test_reject_request(client: AsyncClient, db_session: AsyncSession):
    _, requester_token = await _create_requester(db_session)
    created = await _create_request(db_session, client, requester_token)

    _, approver_token = await _create_approver(db_session)
    response = await client.put(
        f"/api/v1/access-requests/{created['id']}/review",
        json={"status": "rejected"},
        headers={"Authorization": f"Bearer {approver_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"


@pytest.mark.asyncio
async def test_cancel_request(client: AsyncClient, db_session: AsyncSession):
    _, token = await _create_requester(db_session)
    created = await _create_request(db_session, client, token)

    response = await client.delete(
        f"/api/v1/access-requests/{created['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204

    # Verify cancelled
    get_resp = await client.get(
        f"/api/v1/access-requests/{created['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.json()["status"] == "cancelled"
