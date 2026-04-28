"""Tests for ZTIG integration API endpoints."""
import pytest
from httpx import AsyncClient

INTEGRATION_KEY = "dev-integration-key-change-in-prod"
HEADERS = {"X-Integration-Key": INTEGRATION_KEY}


@pytest.mark.anyio
async def test_identity_summary_requires_key(client: AsyncClient):
    resp = await client.get("/api/v1/integration/identity-summary")
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_identity_summary_wrong_key(client: AsyncClient):
    resp = await client.get(
        "/api/v1/integration/identity-summary",
        headers={"X-Integration-Key": "wrong-key"},
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_identity_summary_empty_db(client: AsyncClient):
    resp = await client.get("/api/v1/integration/identity-summary", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_users"] == 0
    assert data["active_users"] == 0
    assert data["privileged_users"] == 0
    assert "generated_at" in data


@pytest.mark.anyio
async def test_auth_events_recent_requires_key(client: AsyncClient):
    resp = await client.get("/api/v1/integration/auth-events/recent")
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_auth_events_recent_empty(client: AsyncClient):
    resp = await client.get("/api/v1/integration/auth-events/recent", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["events"] == []
    assert data["total_count"] == 0
    assert data["period_hours"] == 1


@pytest.mark.anyio
async def test_auth_events_recent_custom_hours(client: AsyncClient):
    resp = await client.get(
        "/api/v1/integration/auth-events/recent?hours=6", headers=HEADERS
    )
    assert resp.status_code == 200
    assert resp.json()["period_hours"] == 6


@pytest.mark.anyio
async def test_auth_events_recent_hours_out_of_range(client: AsyncClient):
    resp = await client.get(
        "/api/v1/integration/auth-events/recent?hours=99", headers=HEADERS
    )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_webhook_notify_requires_key(client: AsyncClient):
    resp = await client.post("/api/v1/integration/webhook/notify", json={"event": "test"})
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_webhook_notify_success(client: AsyncClient):
    resp = await client.post(
        "/api/v1/integration/webhook/notify",
        json={"event": "test", "source": "SIEM"},
        headers=HEADERS,
    )
    assert resp.status_code == 204
