import pytest


@pytest.mark.asyncio
async def test_list_processes_empty(client):
    resp = await client.get("/api/v1/bia/processes")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"] == []
    assert body["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_create_business_process(client):
    payload = {
        "process_name": "Payroll Processing",
        "description": "Monthly payroll run",
        "department": "Finance",
        "criticality": "critical",
        "rto_minutes": 120,
        "rpo_minutes": 30,
        "recovery_priority": 1,
        "legal_requirement": True,
        "financial_impact_per_hour": 50000.00,
    }
    resp = await client.post("/api/v1/bia/processes", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["process_name"] == "Payroll Processing"
    assert data["criticality"] == "critical"
    assert data["recovery_priority"] == 1
    assert data["rto_minutes"] == 120
    assert data["rpo_minutes"] == 30
    assert data["legal_requirement"] is True
    assert data["financial_impact_per_hour"] == 50000.00
    assert data["status"] == "active"
    assert data["id"]


@pytest.mark.asyncio
async def test_list_processes(client):
    await client.post("/api/v1/bia/processes", json={"process_name": "Process A", "criticality": "high"})
    await client.post("/api/v1/bia/processes", json={"process_name": "Process B", "criticality": "medium"})

    resp = await client.get("/api/v1/bia/processes")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 2


@pytest.mark.asyncio
async def test_list_processes_filter_criticality(client):
    await client.post("/api/v1/bia/processes", json={"process_name": "Critical Proc", "criticality": "critical"})
    await client.post("/api/v1/bia/processes", json={"process_name": "Low Proc", "criticality": "low"})

    resp = await client.get("/api/v1/bia/processes?criticality=critical")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["criticality"] == "critical"


@pytest.mark.asyncio
async def test_get_process(client):
    create_resp = await client.post(
        "/api/v1/bia/processes", json={"process_name": "Order Fulfillment", "criticality": "high"}
    )
    process_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/bia/processes/{process_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == process_id


@pytest.mark.asyncio
async def test_get_process_not_found(client):
    resp = await client.get("/api/v1/bia/processes/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_process(client):
    create_resp = await client.post(
        "/api/v1/bia/processes", json={"process_name": "Legacy Process", "criticality": "low", "rto_minutes": 480}
    )
    process_id = create_resp.json()["id"]

    resp = await client.put(
        f"/api/v1/bia/processes/{process_id}",
        json={"rto_minutes": 120, "criticality": "high"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["rto_minutes"] == 120
    assert data["criticality"] == "high"
    assert data["process_name"] == "Legacy Process"


@pytest.mark.asyncio
async def test_delete_process(client):
    create_resp = await client.post(
        "/api/v1/bia/processes", json={"process_name": "Temp Process", "criticality": "low"}
    )
    process_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/v1/bia/processes/{process_id}")
    assert resp.status_code == 204

    get_resp = await client.get(f"/api/v1/bia/processes/{process_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_bia_summary_stats(client):
    await client.post(
        "/api/v1/bia/processes",
        json={"process_name": "Core Banking", "criticality": "critical", "department": "Finance", "recovery_priority": 1},
    )
    await client.post(
        "/api/v1/bia/processes",
        json={"process_name": "CRM System", "criticality": "high", "department": "Sales", "recovery_priority": 2},
    )
    await client.post(
        "/api/v1/bia/processes",
        json={"process_name": "Email Service", "criticality": "low", "department": "IT", "recovery_priority": 5},
    )

    resp = await client.get("/api/v1/bia/processes/stats/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_processes"] == 3
    assert data["critical_count"] == 1
    assert data["high_count"] == 1
    assert "Finance" in data["by_department"]
    assert data["by_department"]["Finance"] == 1


@pytest.mark.asyncio
async def test_dependency_chain(client):
    await client.post(
        "/api/v1/bia/processes",
        json={"process_name": "Payroll", "criticality": "critical", "dependencies": ["HR Database", "Bank Integration"]},
    )
    await client.post(
        "/api/v1/bia/processes",
        json={"process_name": "HR Database", "criticality": "critical"},
    )
    await client.post(
        "/api/v1/bia/processes",
        json={"process_name": "Bank Integration", "criticality": "high"},
    )

    payroll_resp = await client.get("/api/v1/bia/processes")
    payroll_id = None
    for p in payroll_resp.json()["data"]:
        if p["process_name"] == "Payroll":
            payroll_id = p["id"]
            break

    dep_resp = await client.get(f"/api/v1/bia/processes/{payroll_id}/dependencies")
    assert dep_resp.status_code == 200
    dep_data = dep_resp.json()["data"]
    assert len(dep_data) == 2
    names = {d["process_name"] for d in dep_data}
    assert "HR Database" in names
    assert "Bank Integration" in names


@pytest.mark.asyncio
async def test_dependency_chain_no_deps(client):
    create_resp = await client.post(
        "/api/v1/bia/processes", json={"process_name": "Standalone", "criticality": "low"}
    )
    process_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/bia/processes/{process_id}/dependencies")
    assert resp.status_code == 200
    assert resp.json()["data"] == []


@pytest.mark.asyncio
async def test_dependency_chain_not_found(client):
    resp = await client.get("/api/v1/bia/processes/nonexistent/dependencies")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_revision(client):
    payload = {
        "version": 1,
        "reviewed_by": "John Doe",
        "review_date": "2025-01-15",
        "changes_summary": "Initial BIA assessment",
        "next_review_date": "2026-01-15",
    }
    resp = await client.post("/api/v1/bia/revisions", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["version"] == 1
    assert data["reviewed_by"] == "John Doe"
    assert data["changes_summary"] == "Initial BIA assessment"
    assert data["id"]


@pytest.mark.asyncio
async def test_list_revisions(client):
    await client.post(
        "/api/v1/bia/revisions",
        json={"version": 1, "reviewed_by": "Alice", "review_date": "2025-01-01", "next_review_date": "2026-01-01"},
    )
    await client.post(
        "/api/v1/bia/revisions",
        json={"version": 2, "reviewed_by": "Bob", "review_date": "2025-06-01", "next_review_date": "2026-06-01"},
    )

    resp = await client.get("/api/v1/bia/revisions")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 2
    assert data[0]["version"] == 2
