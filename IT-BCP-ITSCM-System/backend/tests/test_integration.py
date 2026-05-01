"""Tests for BCP integration API endpoints."""
import pytest
from httpx import AsyncClient

INTEGRATION_KEY = "dev-integration-key-change-in-prod"
HEADERS = {"X-Integration-Key": INTEGRATION_KEY}


@pytest.mark.anyio
async def test_recovery_plans_requires_key(client: AsyncClient):
    resp = await client.get("/api/v1/integration/recovery-plans")
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_recovery_plans_empty(client: AsyncClient):
    resp = await client.get("/api/v1/integration/recovery-plans", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["plans"] == []
    assert data["active_incidents"] == 0
    assert "generated_at" in data


@pytest.mark.anyio
async def test_recovery_plans_with_tier_filter(client: AsyncClient):
    resp = await client.get(
        "/api/v1/integration/recovery-plans?tier=tier1", headers=HEADERS
    )
    assert resp.status_code == 200
    assert "plans" in resp.json()


@pytest.mark.anyio
async def test_risk_alert_requires_key(client: AsyncClient):
    resp = await client.post("/api/v1/integration/risk-alerts", json={})
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_risk_alert_below_threshold(client: AsyncClient):
    resp = await client.post(
        "/api/v1/integration/risk-alerts",
        json={
            "risk_id": "risk-001",
            "title": "Low Risk Item",
            "risk_score": 6.0,
            "category": "operational",
        },
        headers=HEADERS,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["created"] is False
    assert "threshold" in data["reason"]


@pytest.mark.anyio
async def test_risk_alert_high_score_creates_incident(client: AsyncClient):
    resp = await client.post(
        "/api/v1/integration/risk-alerts",
        json={
            "risk_id": "risk-002",
            "title": "Major Cyber Risk",
            "risk_score": 16.0,
            "category": "cyber_security",
        },
        headers=HEADERS,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["created"] is True
    assert "incident_id" in data
    assert data["severity"] == "high"


@pytest.mark.anyio
async def test_risk_alert_critical_score(client: AsyncClient):
    resp = await client.post(
        "/api/v1/integration/risk-alerts",
        json={
            "risk_id": "risk-003",
            "title": "Critical Infrastructure Risk",
            "risk_score": 25.0,
            "category": "physical",
        },
        headers=HEADERS,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["created"] is True
    assert data["severity"] == "critical"


@pytest.mark.anyio
async def test_change_notification_requires_key(client: AsyncClient):
    resp = await client.post("/api/v1/integration/change-notifications", json={})
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_change_notification_low_risk_ignored(client: AsyncClient):
    resp = await client.post(
        "/api/v1/integration/change-notifications",
        json={
            "change_id": "chg-001",
            "title": "Minor DB Patch",
            "risk_level": "low",
            "affected_systems": ["db-server-01"],
        },
        headers=HEADERS,
    )
    assert resp.status_code == 204


@pytest.mark.anyio
async def test_change_notification_high_risk_creates_incident(client: AsyncClient):
    resp = await client.post(
        "/api/v1/integration/change-notifications",
        json={
            "change_id": "chg-002",
            "title": "Core Network Firewall Update",
            "risk_level": "high",
            "affected_systems": ["firewall-01", "core-switch"],
        },
        headers=HEADERS,
    )
    assert resp.status_code == 204
