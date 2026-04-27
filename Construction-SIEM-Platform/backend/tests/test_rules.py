import pytest

RULE_PAYLOAD = {
    "rule_id": "TEST-001",
    "name": "テストルール",
    "description": "テスト用の検知ルール",
    "rule_type": "sigma",
    "severity": "high",
    "category": "test",
    "mitre_attack_id": "T9999",
    "rule_content": "detection:\n  field: event_type\n  pattern: test_event\n  condition: severity == 'high'\n",
}

SIGMA_RULE_CONTENT = (
    "detection:\n  field: event_type\n  pattern: login_failed\n  condition: count > 5\n"
)


@pytest.mark.asyncio
async def test_create_rule(client):
    resp = await client.post("/api/v1/rules", json=RULE_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()
    assert data["rule_id"] == "TEST-001"
    assert data["name"] == "テストルール"
    assert data["severity"] == "high"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_rule_duplicate_id(client):
    await client.post("/api/v1/rules", json=RULE_PAYLOAD)
    resp = await client.post("/api/v1/rules", json=RULE_PAYLOAD)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_list_rules_empty(client):
    resp = await client.get("/api/v1/rules")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["data"] == []
    assert body["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_list_rules(client):
    await client.post("/api/v1/rules", json=RULE_PAYLOAD)
    await client.post("/api/v1/rules", json={**RULE_PAYLOAD, "rule_id": "TEST-002", "severity": "low"})
    resp = await client.get("/api/v1/rules")
    assert resp.status_code == 200
    assert resp.json()["meta"]["total"] == 2


@pytest.mark.asyncio
async def test_list_rules_filter_severity(client):
    await client.post("/api/v1/rules", json=RULE_PAYLOAD)
    await client.post("/api/v1/rules", json={**RULE_PAYLOAD, "rule_id": "TEST-002", "severity": "low"})
    resp = await client.get("/api/v1/rules?severity=high")
    assert resp.status_code == 200
    assert resp.json()["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_get_rule(client):
    create_resp = await client.post("/api/v1/rules", json=RULE_PAYLOAD)
    rule_id = create_resp.json()["id"]
    resp = await client.get(f"/api/v1/rules/{rule_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == rule_id


@pytest.mark.asyncio
async def test_get_rule_not_found(client):
    resp = await client.get("/api/v1/rules/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_rule(client):
    create_resp = await client.post("/api/v1/rules", json=RULE_PAYLOAD)
    rule_id = create_resp.json()["id"]
    resp = await client.put(f"/api/v1/rules/{rule_id}", json={"name": "更新後ルール", "severity": "critical"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "更新後ルール"
    assert resp.json()["severity"] == "critical"


@pytest.mark.asyncio
async def test_delete_rule(client):
    create_resp = await client.post("/api/v1/rules", json=RULE_PAYLOAD)
    rule_id = create_resp.json()["id"]
    resp = await client.delete(f"/api/v1/rules/{rule_id}")
    assert resp.status_code == 204
    get_resp = await client.get(f"/api/v1/rules/{rule_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_toggle_rule_active(client):
    create_resp = await client.post("/api/v1/rules", json=RULE_PAYLOAD)
    rule_id = create_resp.json()["id"]
    resp = await client.post(f"/api/v1/rules/{rule_id}/toggle")
    assert resp.status_code == 200
    assert resp.json()["data"]["is_active"] is False
    resp2 = await client.post(f"/api/v1/rules/{rule_id}/toggle")
    assert resp2.json()["data"]["is_active"] is True


@pytest.mark.asyncio
async def test_test_rule_match(client):
    resp = await client.post(
        "/api/v1/rules/test",
        json={
            "rule_content": SIGMA_RULE_CONTENT,
            "rule_type": "sigma",
            "event_data": {"event_type": "login_failed", "count": 10},
        },
    )
    assert resp.status_code == 200
    assert resp.json()["matched"] is True


@pytest.mark.asyncio
async def test_test_rule_no_match(client):
    resp = await client.post(
        "/api/v1/rules/test",
        json={
            "rule_content": SIGMA_RULE_CONTENT,
            "rule_type": "sigma",
            "event_data": {"event_type": "login_success", "count": 10},
        },
    )
    assert resp.status_code == 200
    assert resp.json()["matched"] is False


@pytest.mark.asyncio
async def test_rule_stats_summary(client):
    await client.post("/api/v1/rules", json=RULE_PAYLOAD)
    await client.post("/api/v1/rules", json={**RULE_PAYLOAD, "rule_id": "TEST-002", "severity": "low", "category": "test2"})
    resp = await client.get("/api/v1/rules/stats/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_rules"] == 2
    assert data["active_rules"] == 2
    severities = {s["severity"]: s["count"] for s in data["by_severity"]}
    assert severities.get("high") == 1
    assert severities.get("low") == 1
