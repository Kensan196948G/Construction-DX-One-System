import pytest


@pytest.mark.asyncio
async def test_list_incidents_empty(client):
    resp = await client.get("/api/v1/incidents")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"] == []
    assert body["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_create_incident(client):
    payload = {
        "title": "Database outage",
        "description": "Primary DB unreachable",
        "severity": "critical",
    }
    resp = await client.post("/api/v1/incidents", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Database outage"
    assert data["severity"] == "critical"
    assert data["status"] == "open"
    assert data["bcp_activated"] is False
    assert data["id"]


@pytest.mark.asyncio
async def test_get_incident(client):
    create_resp = await client.post(
        "/api/v1/incidents",
        json={"title": "Network issue", "description": "VPN down", "severity": "high"},
    )
    incident_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/incidents/{incident_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == incident_id


@pytest.mark.asyncio
async def test_get_incident_not_found(client):
    resp = await client.get("/api/v1/incidents/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_incident_status(client):
    create_resp = await client.post(
        "/api/v1/incidents",
        json={"title": "Storage failure", "description": "NAS offline", "severity": "medium"},
    )
    incident_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/incidents/{incident_id}/status",
        json={"status": "investigating"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "investigating"


@pytest.mark.asyncio
async def test_resolve_incident_sets_recovery_time(client):
    create_resp = await client.post(
        "/api/v1/incidents",
        json={"title": "App crash", "description": "Service unavailable", "severity": "high"},
    )
    incident_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/incidents/{incident_id}/status",
        json={"status": "resolved"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "resolved"
    assert data["recovery_time_minutes"] is not None


@pytest.mark.asyncio
async def test_activate_bcp(client):
    create_resp = await client.post(
        "/api/v1/incidents",
        json={"title": "Major outage", "description": "DC down", "severity": "critical"},
    )
    incident_id = create_resp.json()["id"]

    resp = await client.patch(f"/api/v1/incidents/{incident_id}/activate-bcp")
    assert resp.status_code == 200
    assert resp.json()["bcp_activated"] is True


@pytest.mark.asyncio
async def test_filter_incidents_by_severity(client):
    await client.post(
        "/api/v1/incidents",
        json={"title": "Low issue", "description": "minor", "severity": "low"},
    )
    await client.post(
        "/api/v1/incidents",
        json={"title": "Critical issue", "description": "major", "severity": "critical"},
    )

    resp = await client.get("/api/v1/incidents?severity=critical")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["severity"] == "critical"
