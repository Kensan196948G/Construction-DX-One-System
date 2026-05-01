import pytest

from apps.audits.models import Audit, Finding


@pytest.mark.django_db
def test_audit_list_empty(client):
    response = client.get("/api/v1/audits/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.django_db
def test_audit_create(client, audit_data):
    response = client.post("/api/v1/audits/", data=audit_data, content_type="application/json")
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == audit_data["title"]
    assert data["findings_count"] == 0
    assert "id" in data


@pytest.mark.django_db
def test_audit_detail_get(client, audit_data):
    create_resp = client.post("/api/v1/audits/", data=audit_data, content_type="application/json")
    audit_id = create_resp.json()["id"]
    response = client.get(f"/api/v1/audits/{audit_id}/")
    assert response.status_code == 200
    assert response.json()["id"] == audit_id


@pytest.mark.django_db
def test_audit_detail_update(client, audit_data):
    create_resp = client.post("/api/v1/audits/", data=audit_data, content_type="application/json")
    audit_id = create_resp.json()["id"]
    updated = {**audit_data, "status": "completed"}
    response = client.put(
        f"/api/v1/audits/{audit_id}/", data=updated, content_type="application/json"
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


@pytest.mark.django_db
def test_audit_detail_delete(client, audit_data):
    create_resp = client.post("/api/v1/audits/", data=audit_data, content_type="application/json")
    audit_id = create_resp.json()["id"]
    response = client.delete(f"/api/v1/audits/{audit_id}/")
    assert response.status_code == 204
    assert not Audit.objects.filter(pk=audit_id).exists()


@pytest.mark.django_db
def test_finding_create(client, audit_data):
    create_resp = client.post("/api/v1/audits/", data=audit_data, content_type="application/json")
    audit_id = create_resp.json()["id"]

    finding_data = {
        "audit": audit_id,
        "title": "Missing access control",
        "description": "Access control policy not enforced",
        "severity": "high",
        "status": "open",
        "recommendation": "Implement RBAC",
    }
    response = client.post(
        f"/api/v1/audits/{audit_id}/findings/",
        data=finding_data,
        content_type="application/json",
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == finding_data["title"]
    assert data["severity"] == "high"


@pytest.mark.django_db
def test_finding_list(client, audit_data):
    create_resp = client.post("/api/v1/audits/", data=audit_data, content_type="application/json")
    audit_id = create_resp.json()["id"]

    for i in range(3):
        finding_data = {
            "audit": audit_id,
            "title": f"Finding {i}",
            "severity": "medium",
            "status": "open",
        }
        client.post(
            f"/api/v1/audits/{audit_id}/findings/",
            data=finding_data,
            content_type="application/json",
        )

    response = client.get(f"/api/v1/audits/{audit_id}/findings/")
    assert response.status_code == 200
    assert len(response.json()) == 3


@pytest.mark.django_db
def test_audit_includes_findings_count(client, audit_data):
    create_resp = client.post("/api/v1/audits/", data=audit_data, content_type="application/json")
    audit_id = create_resp.json()["id"]

    finding_data = {
        "audit": audit_id,
        "title": "Test Finding",
        "severity": "low",
        "status": "open",
    }
    client.post(
        f"/api/v1/audits/{audit_id}/findings/",
        data=finding_data,
        content_type="application/json",
    )

    response = client.get(f"/api/v1/audits/{audit_id}/")
    data = response.json()
    assert data["findings_count"] == 1
    assert len(data["findings"]) == 1


@pytest.mark.django_db
def test_finding_filter_by_severity(client, audit_data):
    create_resp = client.post("/api/v1/audits/", data=audit_data, content_type="application/json")
    audit_id = create_resp.json()["id"]

    for severity in ["critical", "high", "low"]:
        client.post(
            f"/api/v1/audits/{audit_id}/findings/",
            data={
                "audit": audit_id,
                "title": f"{severity} finding",
                "severity": severity,
                "status": "open",
            },
            content_type="application/json",
        )

    response = client.get(f"/api/v1/audits/{audit_id}/findings/?severity=critical")
    assert response.status_code == 200
    results = response.json()
    assert all(r["severity"] == "critical" for r in results)


@pytest.mark.django_db
def test_audit_not_found(client):
    import uuid

    response = client.get(f"/api/v1/audits/{uuid.uuid4()}/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_finding_delete(client, audit_data):
    create_resp = client.post("/api/v1/audits/", data=audit_data, content_type="application/json")
    audit_id = create_resp.json()["id"]

    finding_resp = client.post(
        f"/api/v1/audits/{audit_id}/findings/",
        data={"audit": audit_id, "title": "To Delete", "severity": "low", "status": "open"},
        content_type="application/json",
    )
    finding_id = finding_resp.json()["id"]

    response = client.delete(f"/api/v1/audits/{audit_id}/findings/{finding_id}/")
    assert response.status_code == 204
    assert not Finding.objects.filter(pk=finding_id).exists()


# --- Additional tests with task-specified function names ---


@pytest.mark.django_db
def test_list_audits_empty(client):
    """GET /api/v1/audits/ returns empty list when no audits exist."""
    response = client.get("/api/v1/audits/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.django_db
def test_create_audit(client, audit_data):
    """POST /api/v1/audits/ creates a new audit and returns 201."""
    response = client.post("/api/v1/audits/", data=audit_data, content_type="application/json")
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == audit_data["title"]
    assert "id" in data


@pytest.mark.django_db
def test_get_audit_detail(client, audit_data):
    """GET /api/v1/audits/{id}/ returns audit detail with 200."""
    create_resp = client.post("/api/v1/audits/", data=audit_data, content_type="application/json")
    audit_id = create_resp.json()["id"]
    response = client.get(f"/api/v1/audits/{audit_id}/")
    assert response.status_code == 200
    assert response.json()["id"] == audit_id


@pytest.mark.django_db
def test_update_audit_status(client, audit_data):
    """PATCH/PUT /api/v1/audits/{id}/ updates audit status and returns 200."""
    create_resp = client.post("/api/v1/audits/", data=audit_data, content_type="application/json")
    audit_id = create_resp.json()["id"]
    updated = {**audit_data, "status": "in_progress"}
    response = client.put(
        f"/api/v1/audits/{audit_id}/", data=updated, content_type="application/json"
    )
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


@pytest.mark.django_db
def test_audit_findings(client, audit_data):
    """GET /api/v1/audits/{id}/findings/ returns findings list with 200."""
    create_resp = client.post("/api/v1/audits/", data=audit_data, content_type="application/json")
    audit_id = create_resp.json()["id"]

    # Create a finding first
    client.post(
        f"/api/v1/audits/{audit_id}/findings/",
        data={
            "audit": audit_id,
            "title": "Sample Finding",
            "severity": "medium",
            "status": "open",
        },
        content_type="application/json",
    )

    response = client.get(f"/api/v1/audits/{audit_id}/findings/")
    assert response.status_code == 200
    assert len(response.json()) == 1
