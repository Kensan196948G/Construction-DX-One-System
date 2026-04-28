"""Tests for CAB integration API endpoints."""
import pytest
from httpx import AsyncClient

INTEGRATION_KEY = "dev-integration-key-change-in-prod"
HEADERS = {"X-Integration-Key": INTEGRATION_KEY}


@pytest.mark.anyio
async def test_create_rfc_from_incident_requires_key(client: AsyncClient):
    resp = await client.post("/api/v1/integration/rfcs/from-incident", json={})
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_create_rfc_from_critical_incident(client: AsyncClient):
    resp = await client.post(
        "/api/v1/integration/rfcs/from-incident",
        json={
            "incident_id": "inc-001",
            "incident_title": "Ransomware Detected",
            "incident_severity": "critical",
            "incident_description": "Ransomware detected on file server",
            "requested_by": "SIEM-AutoEscalation",
        },
        headers=HEADERS,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["risk_level"] == "high"
    assert data["incident_reference"] == "inc-001"
    assert "RFC created" in data["message"]
    assert data["status"] == "draft"


@pytest.mark.anyio
async def test_create_rfc_from_high_incident(client: AsyncClient):
    resp = await client.post(
        "/api/v1/integration/rfcs/from-incident",
        json={
            "incident_id": "inc-002",
            "incident_title": "Brute Force Attack",
            "incident_severity": "high",
            "incident_description": "Brute force login attempts detected",
        },
        headers=HEADERS,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["risk_level"] == "high"


@pytest.mark.anyio
async def test_create_rfc_from_medium_incident(client: AsyncClient):
    resp = await client.post(
        "/api/v1/integration/rfcs/from-incident",
        json={
            "incident_id": "inc-003",
            "incident_title": "Suspicious Login",
            "incident_severity": "medium",
            "incident_description": "Suspicious login from unknown IP",
        },
        headers=HEADERS,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["risk_level"] == "medium"


@pytest.mark.anyio
async def test_pending_changes_requires_key(client: AsyncClient):
    resp = await client.get("/api/v1/integration/changes/pending")
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_pending_changes_empty(client: AsyncClient):
    resp = await client.get("/api/v1/integration/changes/pending", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.anyio
async def test_changes_summary_requires_key(client: AsyncClient):
    resp = await client.get("/api/v1/integration/changes/summary")
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_changes_summary_empty(client: AsyncClient):
    resp = await client.get("/api/v1/integration/changes/summary", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["pending_count"] == 0
    assert data["approved_count"] == 0
    assert data["high_risk_count"] == 0
    assert data["emergency_count"] == 0
    assert "generated_at" in data


@pytest.mark.anyio
async def test_create_rfc_then_appears_in_pending(client: AsyncClient):
    await client.post(
        "/api/v1/integration/rfcs/from-incident",
        json={
            "incident_id": "inc-004",
            "incident_title": "Critical Breach",
            "incident_severity": "critical",
            "incident_description": "Security breach detected",
        },
        headers=HEADERS,
    )
    resp = await client.get("/api/v1/integration/changes/summary", headers=HEADERS)
    data = resp.json()
    assert data["pending_count"] == 1
    assert data["high_risk_count"] == 1
    assert data["emergency_count"] == 1
