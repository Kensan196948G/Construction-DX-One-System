from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.user import User


async def _create_admin(db: AsyncSession) -> tuple[User, str]:
    user = User(
        employee_id="ADM001",
        username="inventory_admin",
        email="inventory_admin@example.com",
        display_name="棚卸管理者",
        hashed_password=get_password_hash("pass123"),
        user_type="admin",
        status="active",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token(str(user.id))
    return user, token


async def _create_users(db: AsyncSession, count: int = 3) -> list[User]:
    now = datetime.now(UTC).replace(tzinfo=None)
    users = []
    for i in range(count):
        last_login = now - timedelta(days=30 * (i + 1))
        user = User(
            employee_id=f"USR{100 + i}",
            username=f"testuser{i}",
            email=f"testuser{i}@example.com",
            display_name=f"テストユーザ{i}",
            hashed_password=get_password_hash("pass123"),
            user_type="regular",
            status="active",
            last_login_at=last_login,
        )
        db.add(user)
        users.append(user)
    await db.commit()
    for u in users:
        await db.refresh(u)
    return users


@pytest.mark.asyncio
async def test_create_campaign(client: AsyncClient, db_session: AsyncSession):
    _, token = await _create_admin(db_session)
    response = await client.post(
        "/api/v1/inventory/campaigns",
        json={
            "name": "2026-Q2 アカウント棚卸",
            "description": "四半期棚卸",
            "review_period_start": "2026-04-01",
            "review_period_end": "2026-04-30",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "2026-Q2 アカウント棚卸"
    assert data["status"] == "draft"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_campaigns(client: AsyncClient, db_session: AsyncSession):
    _, token = await _create_admin(db_session)
    await client.post(
        "/api/v1/inventory/campaigns",
        json={
            "name": "Campaign A",
            "review_period_start": "2026-04-01",
            "review_period_end": "2026-04-30",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        "/api/v1/inventory/campaigns",
        json={
            "name": "Campaign B",
            "review_period_start": "2026-05-01",
            "review_period_end": "2026-05-31",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    response = await client.get(
        "/api/v1/inventory/campaigns",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_start_campaign(client: AsyncClient, db_session: AsyncSession):
    _, token = await _create_admin(db_session)
    await _create_users(db_session, count=3)

    create_resp = await client.post(
        "/api/v1/inventory/campaigns",
        json={
            "name": "Start Test Campaign",
            "review_period_start": "2026-04-01",
            "review_period_end": "2026-04-30",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_id = create_resp.json()["id"]

    start_resp = await client.post(
        f"/api/v1/inventory/campaigns/{campaign_id}/start",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert start_resp.status_code == 200
    data = start_resp.json()
    assert data["status"] == "active"
    assert data["total_accounts"] == 4

    items_resp = await client.get(
        f"/api/v1/inventory/campaigns/{campaign_id}/items",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert items_resp.status_code == 200
    items = items_resp.json()
    assert len(items) == 4
    assert all(item["status"] == "pending" for item in items)


@pytest.mark.asyncio
async def test_get_campaign(client: AsyncClient, db_session: AsyncSession):
    _, token = await _create_admin(db_session)
    create_resp = await client.post(
        "/api/v1/inventory/campaigns",
        json={
            "name": "Get Test",
            "review_period_start": "2026-04-01",
            "review_period_end": "2026-04-30",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_id = create_resp.json()["id"]

    response = await client.get(
        f"/api/v1/inventory/campaigns/{campaign_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["id"] == campaign_id


@pytest.mark.asyncio
async def test_review_item(client: AsyncClient, db_session: AsyncSession):
    _, token = await _create_admin(db_session)
    await _create_users(db_session, count=2)

    create_resp = await client.post(
        "/api/v1/inventory/campaigns",
        json={
            "name": "Review Test",
            "review_period_start": "2026-04-01",
            "review_period_end": "2026-04-30",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_id = create_resp.json()["id"]

    await client.post(
        f"/api/v1/inventory/campaigns/{campaign_id}/start",
        headers={"Authorization": f"Bearer {token}"},
    )

    items_resp = await client.get(
        f"/api/v1/inventory/campaigns/{campaign_id}/items",
        headers={"Authorization": f"Bearer {token}"},
    )
    item = items_resp.json()[0]

    review_resp = await client.put(
        f"/api/v1/inventory/campaigns/{campaign_id}/items/{item['id']}/review",
        json={"status": "confirmed", "reviewer_notes": "OK"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert review_resp.status_code == 200
    data = review_resp.json()
    assert data["status"] == "confirmed"
    assert data["reviewer_notes"] == "OK"
    assert data["reviewed_by"] is not None
    assert data["reviewed_at"] is not None


@pytest.mark.asyncio
async def test_complete_campaign(client: AsyncClient, db_session: AsyncSession):
    _, token = await _create_admin(db_session)
    await _create_users(db_session, count=1)

    create_resp = await client.post(
        "/api/v1/inventory/campaigns",
        json={
            "name": "Complete Test",
            "review_period_start": "2026-04-01",
            "review_period_end": "2026-04-30",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_id = create_resp.json()["id"]

    await client.post(
        f"/api/v1/inventory/campaigns/{campaign_id}/start",
        headers={"Authorization": f"Bearer {token}"},
    )

    complete_resp = await client.post(
        f"/api/v1/inventory/campaigns/{campaign_id}/complete",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert complete_resp.status_code == 200
    data = complete_resp.json()
    assert data["status"] == "completed"
    assert data["completed_at"] is not None


@pytest.mark.asyncio
async def test_campaign_summary(client: AsyncClient, db_session: AsyncSession):
    _, token = await _create_admin(db_session)
    await _create_users(db_session, count=2)

    create_resp = await client.post(
        "/api/v1/inventory/campaigns",
        json={
            "name": "Summary Test",
            "review_period_start": "2026-04-01",
            "review_period_end": "2026-04-30",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_id = create_resp.json()["id"]

    await client.post(
        f"/api/v1/inventory/campaigns/{campaign_id}/start",
        headers={"Authorization": f"Bearer {token}"},
    )

    items_resp = await client.get(
        f"/api/v1/inventory/campaigns/{campaign_id}/items",
        headers={"Authorization": f"Bearer {token}"},
    )
    items = items_resp.json()
    await client.put(
        f"/api/v1/inventory/campaigns/{campaign_id}/items/{items[0]['id']}/review",
        json={"status": "confirmed"},
        headers={"Authorization": f"Bearer {token}"},
    )

    summary_resp = await client.get(
        f"/api/v1/inventory/campaigns/{campaign_id}/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    # admin + 2 created users = 3 total, 1 reviewed
    assert summary["total"] == 3
    assert summary["reviewed"] == 1
    assert summary["completion_rate"] == pytest.approx(33.33, rel=0.1)


@pytest.mark.asyncio
async def test_inactive_accounts(client: AsyncClient, db_session: AsyncSession):
    _, token = await _create_admin(db_session)
    now = datetime.now(UTC).replace(tzinfo=None)
    users_data = [
        ("ACT001", "active1", "active1@example.com", now - timedelta(days=10)),
        ("ACT002", "inactive1", "inactive1@example.com", now - timedelta(days=200)),
        ("ACT003", "inactive2", "inactive2@example.com", now - timedelta(days=100)),
    ]
    for emp_id, uname, email, last_login in users_data:
        db_session.add(User(
            employee_id=emp_id,
            username=uname,
            email=email,
            display_name=uname,
            hashed_password=get_password_hash("pass123"),
            user_type="regular",
            status="active",
            last_login_at=last_login,
        ))
    await db_session.commit()

    response = await client.get(
        "/api/v1/inventory/inactive-accounts?days=90",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    usernames = {u["username"] for u in data}
    assert "inactive1" in usernames
    assert "inactive2" in usernames
    assert "active1" not in usernames


@pytest.mark.asyncio
async def test_cancel_campaign(client: AsyncClient, db_session: AsyncSession):
    _, token = await _create_admin(db_session)
    await _create_users(db_session, count=1)

    create_resp = await client.post(
        "/api/v1/inventory/campaigns",
        json={
            "name": "Cancel Test",
            "review_period_start": "2026-04-01",
            "review_period_end": "2026-04-30",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_id = create_resp.json()["id"]

    cancel_resp = await client.post(
        f"/api/v1/inventory/campaigns/{campaign_id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "cancelled"
