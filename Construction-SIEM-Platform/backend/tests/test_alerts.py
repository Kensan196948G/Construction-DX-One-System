import pytest

ALERT_PAYLOAD = {
    "title": "不審なポートスキャン検出",
    "severity": "critical",
    "source": "firewall",
    "description": "192.168.1.100 から複数ポートへのスキャンを検出",
    "mitre_tactic": "Discovery",
    "mitre_technique": "T1046",
    "site": "東京建設現場A",
}


@pytest.mark.asyncio
async def test_create_alert(client):
    resp = await client.post("/api/v1/alerts", json=ALERT_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == ALERT_PAYLOAD["title"]
    assert data["severity"] == "critical"
    assert data["acknowledged"] is False
    assert data["status"] == "open"


@pytest.mark.asyncio
async def test_list_alerts_empty(client):
    resp = await client.get("/api/v1/alerts")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["data"] == []
    assert body["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_list_alerts(client):
    await client.post("/api/v1/alerts", json=ALERT_PAYLOAD)
    await client.post("/api/v1/alerts", json={**ALERT_PAYLOAD, "severity": "high"})
    resp = await client.get("/api/v1/alerts")
    assert resp.status_code == 200
    assert resp.json()["meta"]["total"] == 2


@pytest.mark.asyncio
async def test_list_alerts_filter_severity(client):
    await client.post("/api/v1/alerts", json=ALERT_PAYLOAD)
    await client.post("/api/v1/alerts", json={**ALERT_PAYLOAD, "severity": "high"})
    resp = await client.get("/api/v1/alerts?severity=critical")
    assert resp.status_code == 200
    assert resp.json()["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_get_alert(client):
    create_resp = await client.post("/api/v1/alerts", json=ALERT_PAYLOAD)
    alert_id = create_resp.json()["id"]
    resp = await client.get(f"/api/v1/alerts/{alert_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == alert_id


@pytest.mark.asyncio
async def test_get_alert_not_found(client):
    resp = await client.get("/api/v1/alerts/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_alert_status(client):
    create_resp = await client.post("/api/v1/alerts", json=ALERT_PAYLOAD)
    alert_id = create_resp.json()["id"]
    resp = await client.patch(f"/api/v1/alerts/{alert_id}/status", json={"status": "processing"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "processing"


@pytest.mark.asyncio
async def test_acknowledge_alert(client):
    create_resp = await client.post("/api/v1/alerts", json=ALERT_PAYLOAD)
    alert_id = create_resp.json()["id"]
    resp = await client.patch(f"/api/v1/alerts/{alert_id}/acknowledge?acknowledged_by=analyst01")
    assert resp.status_code == 200
    data = resp.json()
    assert data["acknowledged"] is True
    assert data["acknowledged_by"] == "analyst01"
    assert data["acknowledged_at"] is not None


@pytest.mark.asyncio
async def test_alert_summary_by_severity(client):
    await client.post("/api/v1/alerts", json=ALERT_PAYLOAD)
    await client.post("/api/v1/alerts", json={**ALERT_PAYLOAD, "severity": "high"})
    await client.post("/api/v1/alerts", json={**ALERT_PAYLOAD, "severity": "high"})
    resp = await client.get("/api/v1/alerts/summary/by-severity")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    summary = {item["severity"]: item["count"] for item in data["data"]}
    assert summary.get("critical") == 1
    assert summary.get("high") == 2


@pytest.mark.asyncio
async def test_ingest_alert(client):
    resp = await client.post("/api/v1/alerts/ingest", json=ALERT_PAYLOAD)
    assert resp.status_code == 201
    assert resp.json()["title"] == ALERT_PAYLOAD["title"]


@pytest.mark.asyncio
async def test_list_alerts_filter_acknowledged(client):
    create_resp = await client.post("/api/v1/alerts", json=ALERT_PAYLOAD)
    alert_id = create_resp.json()["id"]
    await client.patch(f"/api/v1/alerts/{alert_id}/acknowledge")
    await client.post("/api/v1/alerts", json=ALERT_PAYLOAD)

    resp = await client.get("/api/v1/alerts?acknowledged=true")
    assert resp.status_code == 200
    assert resp.json()["meta"]["total"] == 1
