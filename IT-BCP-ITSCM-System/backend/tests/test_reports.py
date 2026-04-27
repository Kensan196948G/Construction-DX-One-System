import pytest


@pytest.mark.asyncio
async def test_executive_summary_empty(client):
    resp = await client.get("/api/v1/reports/executive-summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["active_incidents"]["total"] == 0
    assert data["system_health"]["total"] == 0
    assert data["readiness_score"] == 100


@pytest.mark.asyncio
async def test_executive_summary_with_data(client):
    await client.post(
        "/api/v1/incidents",
        json={"title": "Critical outage", "description": "DB down", "severity": "critical"},
    )
    await client.post(
        "/api/v1/incidents",
        json={"title": "Low issue", "description": "Minor", "severity": "low"},
    )
    create_resp = await client.post(
        "/api/v1/incidents",
        json={
            "title": "Resolved issue", "description": "Fixed",
            "severity": "medium", "rto_deadline": "2026-12-31T23:59:59Z",
        },
    )
    inc_id = create_resp.json()["id"]
    await client.patch(f"/api/v1/incidents/{inc_id}/status", json={"status": "resolved"})

    await client.post("/api/v1/systems", json={"name": "ERP", "tier": "tier1"})
    await client.post("/api/v1/systems", json={"name": "CRM", "tier": "tier2"})

    resp = await client.get("/api/v1/reports/executive-summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["active_incidents"]["total"] == 2
    assert data["active_incidents"]["critical_high"] == 1
    assert data["system_health"]["total"] == 2
    assert data["rto_compliance_rate"] > 0
    assert 0 <= data["readiness_score"] <= 100


@pytest.mark.asyncio
async def test_incident_report_not_found(client):
    resp = await client.get("/api/v1/reports/incident/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_incident_report_with_timeline(client):
    create_resp = await client.post(
        "/api/v1/incidents",
        json={
            "title": "Network outage", "description": "Main switch down",
            "severity": "high", "affected_systems": "ERP, CRM",
        },
    )
    inc_id = create_resp.json()["id"]
    await client.patch(f"/api/v1/incidents/{inc_id}/status", json={"status": "resolved"})

    resp = await client.get(f"/api/v1/reports/incident/{inc_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["incident_id"] == inc_id
    assert data["systems_affected"] == ["ERP", "CRM"]
    assert len(data["timeline"]) >= 2
    assert data["root_cause_analysis"] != ""


@pytest.mark.asyncio
async def test_weekly_kpi_empty(client):
    resp = await client.get("/api/v1/reports/weekly-kpi")
    assert resp.status_code == 200
    data = resp.json()
    assert data["incident_trends"] == []
    assert data["drill_completion_rate"] == 1.0


@pytest.mark.asyncio
async def test_weekly_kpi_with_data(client):
    await client.post(
        "/api/v1/incidents",
        json={"title": "Bug", "description": "App error", "severity": "medium"},
    )
    await client.post(
        "/api/v1/systems", json={"name": "App Server", "tier": "tier1"},
    )

    resp = await client.get("/api/v1/reports/weekly-kpi")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["incident_trends"]) > 0
    assert data["system_availability_rate"] == 1.0


@pytest.mark.asyncio
async def test_bcp_readiness_empty(client):
    resp = await client.get("/api/v1/reports/bcp-readiness")
    assert resp.status_code == 200
    data = resp.json()
    assert data["plan_coverage"]["total_systems"] == 0


@pytest.mark.asyncio
async def test_bcp_readiness_with_gaps(client):
    sys_resp = await client.post(
        "/api/v1/systems", json={"name": "Critical App", "tier": "tier1"},
    )
    sys_id = sys_resp.json()["id"]
    await client.patch(f"/api/v1/systems/{sys_id}/status?status=offline")

    resp = await client.get("/api/v1/reports/bcp-readiness")
    assert resp.status_code == 200
    data = resp.json()
    assert data["plan_coverage"]["total_systems"] == 1
    assert len(data["gaps_and_recommendations"]) > 0
