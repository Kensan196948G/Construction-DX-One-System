import pytest


@pytest.mark.asyncio
async def _create_rfc(client, **kwargs):
    data = {"title": "Test RFC", "description": "test", "change_type": "normal"}
    data.update(kwargs)
    resp = await client.post("/api/v1/rfcs", json=data)
    assert resp.status_code == 201
    return resp.json()


@pytest.mark.asyncio
async def _update_status(client, rfc_id, status):
    resp = await client.patch(f"/api/v1/rfcs/{rfc_id}/status", json={"status": status})
    assert resp.status_code == 200
    return resp.json()


@pytest.mark.asyncio
async def _create_meeting(client, **kwargs):
    data = {"title": "CAB Meeting", "status": "scheduled"}
    data.update(kwargs)
    resp = await client.post("/api/v1/cab-meetings", json=data)
    assert resp.status_code == 201
    return resp.json()


@pytest.mark.asyncio
async def test_kpi_metrics(client):
    rfc1 = await _create_rfc(client, change_type="normal")
    await _update_status(client, rfc1["id"], "submitted")
    await _update_status(client, rfc1["id"], "approved")
    await _update_status(client, rfc1["id"], "implemented")
    await _update_status(client, rfc1["id"], "closed")

    rfc2 = await _create_rfc(client, change_type="normal")
    await _update_status(client, rfc2["id"], "submitted")
    await _update_status(client, rfc2["id"], "approved")
    await _update_status(client, rfc2["id"], "implemented")

    rfc3 = await _create_rfc(client, change_type="emergency")
    await _update_status(client, rfc3["id"], "submitted")

    rfc4 = await _create_rfc(client, change_type="emergency")
    await _update_status(client, rfc4["id"], "submitted")
    await _update_status(client, rfc4["id"], "approved")
    await _update_status(client, rfc4["id"], "implemented")
    await _update_status(client, rfc4["id"], "closed")

    resp = await client.get("/api/v1/kpi/metrics")
    assert resp.status_code == 200
    data = resp.json()

    assert data["change_success_rate"]["value"] == pytest.approx(66.67, rel=0.1)
    assert data["change_success_rate"]["status"] == "critical"

    assert data["emergency_change_ratio"]["value"] == pytest.approx(50.0, rel=0.1)
    assert data["emergency_change_ratio"]["status"] == "critical"

    assert data["rollback_rate"]["value"] == 0.0
    assert data["rollback_rate"]["status"] == "healthy"

    assert data["pir_completion_rate"]["value"] == 100.0
    assert data["pir_completion_rate"]["status"] == "healthy"


@pytest.mark.asyncio
async def test_kpi_alerts(client):
    rfc1 = await _create_rfc(client, change_type="normal")
    await _update_status(client, rfc1["id"], "submitted")
    await _update_status(client, rfc1["id"], "approved")
    await _update_status(client, rfc1["id"], "implemented")
    await _update_status(client, rfc1["id"], "closed")

    rfc2 = await _create_rfc(client, change_type="normal")
    await _update_status(client, rfc2["id"], "submitted")
    await _update_status(client, rfc2["id"], "approved")
    await _update_status(client, rfc2["id"], "implemented")

    rfc3 = await _create_rfc(client, change_type="emergency")
    await _update_status(client, rfc3["id"], "submitted")

    rfc4 = await _create_rfc(client, change_type="emergency")
    await _update_status(client, rfc4["id"], "submitted")
    await _update_status(client, rfc4["id"], "approved")
    await _update_status(client, rfc4["id"], "implemented")
    await _update_status(client, rfc4["id"], "closed")

    resp = await client.get("/api/v1/kpi/alerts")
    assert resp.status_code == 200
    alerts = resp.json()

    alert_metrics = {a["metric"] for a in alerts}
    assert "change_success_rate" in alert_metrics
    assert "emergency_change_ratio" in alert_metrics


@pytest.mark.asyncio
async def test_sla_compliance(client):
    rfc1 = await _create_rfc(client, change_type="normal")
    await _update_status(client, rfc1["id"], "submitted")
    await _update_status(client, rfc1["id"], "approved")
    await _update_status(client, rfc1["id"], "implemented")
    await _update_status(client, rfc1["id"], "closed")

    rfc2 = await _create_rfc(client, change_type="normal")
    await _update_status(client, rfc2["id"], "submitted")
    await _update_status(client, rfc2["id"], "approved")
    await _update_status(client, rfc2["id"], "implemented")

    rfc3 = await _create_rfc(client, change_type="emergency")
    await _update_status(client, rfc3["id"], "submitted")
    await _update_status(client, rfc3["id"], "approved")
    await _update_status(client, rfc3["id"], "implemented")
    await _update_status(client, rfc3["id"], "closed")

    resp = await client.get("/api/v1/kpi/sla")
    assert resp.status_code == 200
    data = resp.json()

    items = {i["change_type"]: i for i in data["items"]}
    assert items["normal"]["total"] == 2
    assert items["normal"]["met"] == 1
    assert items["normal"]["compliance_percent"] == pytest.approx(50.0, rel=0.1)

    assert items["emergency"]["total"] == 1
    assert items["emergency"]["met"] == 1
    assert items["emergency"]["compliance_percent"] == pytest.approx(100.0, rel=0.1)

    assert items["standard"]["total"] == 0
    assert items["standard"]["compliance_percent"] == 100.0

    assert data["overall"] == pytest.approx(66.67, rel=0.1)


@pytest.mark.asyncio
async def test_cab_efficiency(client):
    meeting = await _create_meeting(client)

    rfc1 = await _create_rfc(client)
    await _update_status(client, rfc1["id"], "submitted")
    await _update_status(client, rfc1["id"], "approved")
    await client.patch(f"/api/v1/rfcs/{rfc1['id']}/assign-meeting?meeting_id={meeting['id']}")

    rfc2 = await _create_rfc(client)
    await _update_status(client, rfc2["id"], "submitted")
    await _update_status(client, rfc2["id"], "approved")
    await client.patch(f"/api/v1/rfcs/{rfc2['id']}/assign-meeting?meeting_id={meeting['id']}")

    resp = await client.get("/api/v1/kpi/cab-efficiency")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_meetings"] == 1
    assert data["total_rfcs_reviewed"] == 2
    assert data["avg_rfcs_per_meeting"] == 2.0


@pytest.mark.asyncio
async def test_dashboard_summary(client):
    rfc1 = await _create_rfc(client, change_type="normal")
    await _update_status(client, rfc1["id"], "submitted")
    await _update_status(client, rfc1["id"], "approved")
    await _update_status(client, rfc1["id"], "implemented")
    await _update_status(client, rfc1["id"], "closed")

    rfc2 = await _create_rfc(client, change_type="emergency")
    await _update_status(client, rfc2["id"], "submitted")

    meeting = await _create_meeting(client)
    await client.patch(f"/api/v1/rfcs/{rfc1['id']}/assign-meeting?meeting_id={meeting['id']}")

    resp = await client.get("/api/v1/kpi/dashboard")
    assert resp.status_code == 200
    data = resp.json()

    assert "metrics" in data
    assert "alerts" in data
    assert "trends" in data
    assert "sla" in data
    assert "cab_efficiency" in data

    assert data["metrics"]["change_success_rate"]["value"] == 100.0
    assert data["cab_efficiency"]["total_meetings"] == 1
