import pytest


@pytest.mark.asyncio
async def test_create_pir(client):
    create_resp = await client.post(
        "/api/v1/rfcs",
        json={"title": "Test change", "description": "For PIR test"},
    )
    rfc_id = create_resp.json()["id"]

    resp = await client.post("/api/v1/pir", json={"rfc_id": rfc_id})
    assert resp.status_code == 201
    data = resp.json()
    assert data["rfc_id"] == rfc_id
    assert data["review_status"] == "pending"
    assert data["id"]


@pytest.mark.asyncio
async def test_create_pir_duplicate(client):
    create_resp = await client.post(
        "/api/v1/rfcs",
        json={"title": "Test change", "description": "For PIR duplicate test"},
    )
    rfc_id = create_resp.json()["id"]

    await client.post("/api/v1/pir", json={"rfc_id": rfc_id})
    resp = await client.post("/api/v1/pir", json={"rfc_id": rfc_id})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_list_pirs(client):
    create_resp = await client.post(
        "/api/v1/rfcs",
        json={"title": "Test change", "description": "For PIR list test"},
    )
    rfc_id = create_resp.json()["id"]
    await client.post("/api/v1/pir", json={"rfc_id": rfc_id})

    resp = await client.get("/api/v1/pir")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert len(body["data"]) >= 1
    assert body["meta"]["total"] >= 1


@pytest.mark.asyncio
async def test_get_pir(client):
    create_resp = await client.post(
        "/api/v1/rfcs",
        json={"title": "Test change", "description": "For PIR get test"},
    )
    rfc_id = create_resp.json()["id"]
    pir_resp = await client.post("/api/v1/pir", json={"rfc_id": rfc_id})
    pir_id = pir_resp.json()["id"]

    resp = await client.get(f"/api/v1/pir/{pir_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == pir_id
    assert resp.json()["rfc_id"] == rfc_id


@pytest.mark.asyncio
async def test_get_pir_not_found(client):
    resp = await client.get("/api/v1/pir/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_pir(client):
    create_resp = await client.post(
        "/api/v1/rfcs",
        json={"title": "Test change", "description": "For PIR update test"},
    )
    rfc_id = create_resp.json()["id"]
    pir_resp = await client.post("/api/v1/pir", json={"rfc_id": rfc_id})
    pir_id = pir_resp.json()["id"]

    resp = await client.put(
        f"/api/v1/pir/{pir_id}",
        json={"review_status": "in_review", "reviewer_id": "user-001"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["review_status"] == "in_review"
    assert data["reviewer_id"] == "user-001"


@pytest.mark.asyncio
async def test_complete_pir_review(client):
    create_resp = await client.post(
        "/api/v1/rfcs",
        json={"title": "Test change", "description": "For PIR complete test"},
    )
    rfc_id = create_resp.json()["id"]
    pir_resp = await client.post("/api/v1/pir", json={"rfc_id": rfc_id})
    pir_id = pir_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/pir/{pir_id}/complete",
        json={
            "reviewer_id": "reviewer-001",
            "was_successful": True,
            "issues_encountered": "Minor delay",
            "lessons_learned": "Plan better",
            "rollback_effectiveness": "full",
            "recommendation": "Proceed with caution",
            "follow_up_actions": [{"action": "Update docs", "owner": "team-a"}],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["review_status"] == "completed"
    assert data["was_successful"] is True
    assert data["reviewer_id"] == "reviewer-001"
    assert data["issues_encountered"] == "Minor delay"
    assert data["follow_up_actions"]["items"][0]["action"] == "Update docs"


@pytest.mark.asyncio
async def test_pir_summary(client):
    create_resp = await client.post(
        "/api/v1/rfcs",
        json={"title": "Test change", "description": "For PIR summary test"},
    )
    rfc_id = create_resp.json()["id"]
    pir_resp = await client.post("/api/v1/pir", json={"rfc_id": rfc_id})
    pir_id = pir_resp.json()["id"]
    await client.post(
        f"/api/v1/pir/{pir_id}/complete",
        json={
            "reviewer_id": "reviewer-001",
            "was_successful": True,
        },
    )

    resp = await client.get("/api/v1/pir/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "completion_rate" in data
    assert "overdue_count" in data
    assert "recent_pirs" in data
    assert data["overdue_count"] == 0


@pytest.mark.asyncio
async def test_get_by_rfc(client):
    create_resp = await client.post(
        "/api/v1/rfcs",
        json={"title": "Test change", "description": "For PIR by-rfc test"},
    )
    rfc_id = create_resp.json()["id"]
    pir_resp = await client.post("/api/v1/pir", json={"rfc_id": rfc_id})
    pir_id = pir_resp.json()["id"]

    resp = await client.get(f"/api/v1/pir/by-rfc/{rfc_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == pir_id

    resp2 = await client.get("/api/v1/pir/by-rfc/nonexistent-rfc")
    assert resp2.status_code == 404
