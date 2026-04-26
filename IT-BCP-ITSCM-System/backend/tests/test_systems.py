import pytest


@pytest.mark.asyncio
async def test_list_systems_empty(client):
    resp = await client.get("/api/v1/systems")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"] == []
    assert body["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_create_system(client):
    payload = {
        "name": "Core ERP",
        "tier": "tier1",
        "status": "operational",
        "rto_minutes": 60,
        "rpo_minutes": 15,
        "owner": "IT Team",
    }
    resp = await client.post("/api/v1/systems", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Core ERP"
    assert data["tier"] == "tier1"
    assert data["rto_minutes"] == 60


@pytest.mark.asyncio
async def test_get_system(client):
    create_resp = await client.post(
        "/api/v1/systems",
        json={"name": "Backup System", "tier": "tier2"},
    )
    system_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/systems/{system_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == system_id


@pytest.mark.asyncio
async def test_get_system_not_found(client):
    resp = await client.get("/api/v1/systems/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_system_status(client):
    create_resp = await client.post(
        "/api/v1/systems",
        json={"name": "File Server", "tier": "tier3"},
    )
    system_id = create_resp.json()["id"]

    resp = await client.patch(f"/api/v1/systems/{system_id}/status?status=degraded")
    assert resp.status_code == 200
    assert resp.json()["status"] == "degraded"


@pytest.mark.asyncio
async def test_update_system_status_invalid(client):
    create_resp = await client.post(
        "/api/v1/systems",
        json={"name": "Mail Server", "tier": "tier2"},
    )
    system_id = create_resp.json()["id"]

    resp = await client.patch(f"/api/v1/systems/{system_id}/status?status=unknown")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_filter_systems_by_tier(client):
    await client.post("/api/v1/systems", json={"name": "Sys A", "tier": "tier1"})
    await client.post("/api/v1/systems", json={"name": "Sys B", "tier": "tier3"})

    resp = await client.get("/api/v1/systems?tier=tier1")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["tier"] == "tier1"
