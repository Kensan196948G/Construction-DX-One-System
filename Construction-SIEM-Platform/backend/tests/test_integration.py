"""Tests for SIEM integration API endpoints."""
import pytest
from httpx import AsyncClient

INTEGRATION_KEY = "dev-integration-key-change-in-prod"
HEADERS = {"X-Integration-Key": INTEGRATION_KEY}


@pytest.mark.anyio
async def test_ingest_auth_events_requires_key(client: AsyncClient):
    resp = await client.post("/api/v1/integration/events/ingest", json={"events": [], "source_system": "ZTIG"})
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_ingest_auth_events_empty(client: AsyncClient):
    resp = await client.post(
        "/api/v1/integration/events/ingest",
        json={"events": [], "source_system": "ZTIG"},
        headers=HEADERS,
    )
    assert resp.status_code == 201
    assert resp.json()["ingested"] == 0


@pytest.mark.anyio
async def test_ingest_auth_events_single(client: AsyncClient):
    resp = await client.post(
        "/api/v1/integration/events/ingest",
        json={
            "events": [
                {
                    "event_type": "login_failed",
                    "username": "test_user",
                    "actor_ip": "10.0.0.1",
                    "timestamp": "2026-04-28T10:00:00Z",
                    "severity": "high",
                    "details": {"attempts": 5},
                }
            ],
            "source_system": "ZTIG",
        },
        headers=HEADERS,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["ingested"] == 1
    assert len(data["event_ids"]) == 1


@pytest.mark.anyio
async def test_ingest_auth_events_multiple(client: AsyncClient):
    events = [
        {
            "event_type": "login_failed",
            "username": f"user{i}",
            "actor_ip": "10.0.0.1",
            "timestamp": "2026-04-28T10:00:00Z",
            "severity": "medium",
            "details": {},
        }
        for i in range(3)
    ]
    resp = await client.post(
        "/api/v1/integration/events/ingest",
        json={"events": events, "source_system": "ZTIG"},
        headers=HEADERS,
    )
    assert resp.status_code == 201
    assert resp.json()["ingested"] == 3


@pytest.mark.anyio
async def test_pending_incidents_requires_key(client: AsyncClient):
    resp = await client.get("/api/v1/integration/incidents/pending")
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_pending_incidents_empty(client: AsyncClient):
    resp = await client.get("/api/v1/integration/incidents/pending", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.anyio
async def test_escalate_incident_not_found(client: AsyncClient):
    resp = await client.post(
        "/api/v1/integration/incidents/nonexistent-id/escalate-to-cab",
        json={"incident_id": "nonexistent-id", "requested_by": "admin", "change_reason": "Critical issue"},
        headers=HEADERS,
    )
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_alert_summary_requires_key(client: AsyncClient):
    resp = await client.get("/api/v1/integration/alerts/summary")
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_alert_summary_empty(client: AsyncClient):
    resp = await client.get("/api/v1/integration/alerts/summary", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_open"] == 0
    assert data["critical_count"] == 0
    assert "generated_at" in data
