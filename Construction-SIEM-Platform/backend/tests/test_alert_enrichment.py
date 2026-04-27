import pytest

ALERT_PAYLOAD = {
    "title": "不審なポートスキャン検出",
    "severity": "high",
    "source": "firewall",
    "description": "192.168.1.100 から複数ポートへのスキャンを検出",
    "mitre_tactic": "Discovery",
    "mitre_technique": "T1046",
    "site": "東京建設現場A",
}

ANOTHER_ALERT = {
    "title": "関連アラート",
    "severity": "medium",
    "source": "firewall",
    "description": "同じソースからの別イベント",
    "mitre_technique": "T1046",
    "site": "東京建設現場A",
}

EVENT_PAYLOAD = {
    "event_type": "port_scan",
    "source": "firewall",
    "source_ip": "192.168.1.100",
    "severity": "high",
    "description": "Port scan from 192.168.1.100",
    "site": "東京建設現場A",
}


@pytest.mark.asyncio
async def test_enrich_alert(client):
    create_resp = await client.post("/api/v1/alerts", json=ALERT_PAYLOAD)
    assert create_resp.status_code == 201
    alert_id = create_resp.json()["id"]

    await client.post("/api/v1/events", json=EVENT_PAYLOAD)

    enrich_resp = await client.post(f"/api/v1/alerts/{alert_id}/enrich")
    assert enrich_resp.status_code == 200
    data = enrich_resp.json()
    assert data["alert_id"] == alert_id
    assert data["related_events_count"] >= 0
    assert "calculated_severity" in data
    assert "enrichment_timestamp" in data
    assert isinstance(data["entity_history"], list)
    assert isinstance(data["matched_rules"], list)


@pytest.mark.asyncio
async def test_enrich_alert_not_found(client):
    resp = await client.post("/api/v1/alerts/nonexistent/enrich")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_correlate_alerts(client):
    create_resp = await client.post("/api/v1/alerts", json=ALERT_PAYLOAD)
    alert_id = create_resp.json()["id"]

    await client.post("/api/v1/alerts", json=ANOTHER_ALERT)

    corr_resp = await client.get(f"/api/v1/alerts/{alert_id}/correlations")
    assert corr_resp.status_code == 200
    data = corr_resp.json()
    assert isinstance(data, list)
    if data:
        assert data[0]["correlation_reason"] in ("same_source", "same_mitre_technique", "same_site",
                                                  "same_source_and_technique")


@pytest.mark.asyncio
async def test_correlate_alerts_not_found(client):
    resp = await client.get("/api/v1/alerts/nonexistent/correlations")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_alert_timeline(client):
    create_resp = await client.post("/api/v1/alerts", json=ALERT_PAYLOAD)
    alert_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/alerts/{alert_id}/timeline")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["event_type"] == "alert_created"


@pytest.mark.asyncio
async def test_execute_playbook_for_alert(client):
    create_resp = await client.post("/api/v1/alerts", json=ALERT_PAYLOAD)
    alert_id = create_resp.json()["id"]

    playbook_resp = await client.post(
        f"/api/v1/alerts/{alert_id}/playbook",
        json={"playbook_id": "brute_force_response", "event_data": {"rule_id": "GEN-001"}},
    )
    assert playbook_resp.status_code == 200
    data = playbook_resp.json()
    assert data["playbook_id"] == "brute_force_response"


@pytest.mark.asyncio
async def test_enrich_alert_with_correlation(client):
    r1 = await client.post("/api/v1/alerts", json=ALERT_PAYLOAD)
    alert_id = r1.json()["id"]

    await client.post("/api/v1/alerts", json=ANOTHER_ALERT)
    await client.post("/api/v1/alerts", json={**ANOTHER_ALERT, "severity": "high"})

    enrich_resp = await client.post(f"/api/v1/alerts/{alert_id}/enrich")
    data = enrich_resp.json()
    assert data["correlated_alerts_count"] >= 0
