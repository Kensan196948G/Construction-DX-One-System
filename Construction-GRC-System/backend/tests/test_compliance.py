import pytest

from apps.compliance.models import Control


@pytest.mark.django_db
def test_control_list_empty(client):
    response = client.get("/api/v1/compliance/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.django_db
def test_control_create(client, control_data):
    response = client.post(
        "/api/v1/compliance/", data=control_data, content_type="application/json"
    )
    assert response.status_code == 201
    data = response.json()
    assert data["control_number"] == control_data["control_number"]
    assert data["title"] == control_data["title"]
    assert "id" in data


@pytest.mark.django_db
def test_control_unique_number(client, control_data):
    client.post("/api/v1/compliance/", data=control_data, content_type="application/json")
    response = client.post(
        "/api/v1/compliance/", data=control_data, content_type="application/json"
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_control_detail_get(client, control_data):
    create_resp = client.post(
        "/api/v1/compliance/", data=control_data, content_type="application/json"
    )
    control_id = create_resp.json()["id"]
    response = client.get(f"/api/v1/compliance/{control_id}/")
    assert response.status_code == 200
    assert response.json()["id"] == control_id


@pytest.mark.django_db
def test_control_detail_update(client, control_data):
    create_resp = client.post(
        "/api/v1/compliance/", data=control_data, content_type="application/json"
    )
    control_id = create_resp.json()["id"]
    updated = {**control_data, "implementation_status": "implemented"}
    response = client.put(
        f"/api/v1/compliance/{control_id}/",
        data=updated,
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json()["implementation_status"] == "implemented"


@pytest.mark.django_db
def test_control_detail_delete(client, control_data):
    create_resp = client.post(
        "/api/v1/compliance/", data=control_data, content_type="application/json"
    )
    control_id = create_resp.json()["id"]
    response = client.delete(f"/api/v1/compliance/{control_id}/")
    assert response.status_code == 204
    assert not Control.objects.filter(pk=control_id).exists()


@pytest.mark.django_db
def test_control_filter_by_status(client, control_data):
    client.post("/api/v1/compliance/", data=control_data, content_type="application/json")
    implemented_data = {
        **control_data,
        "control_number": "A.5.2",
        "title": "Implemented Control",
        "implementation_status": "implemented",
    }
    client.post("/api/v1/compliance/", data=implemented_data, content_type="application/json")

    response = client.get("/api/v1/compliance/?implementation_status=not_started")
    assert response.status_code == 200
    results = response.json()
    assert all(r["implementation_status"] == "not_started" for r in results)


@pytest.mark.django_db
def test_control_not_found(client):
    import uuid

    response = client.get(f"/api/v1/compliance/{uuid.uuid4()}/")
    assert response.status_code == 404


def _seed_controls():
    from apps.compliance.models import Control

    domains = {
        "Organizational Controls": [
            ("A.5.1", "Policies for information security"),
            ("A.5.2", "Information security roles"),
            ("A.5.3", "Segregation of duties"),
        ],
        "People Controls": [
            ("A.6.1", "Screening"),
            ("A.6.2", "Terms and conditions of employment"),
        ],
        "Physical Controls": [
            ("A.7.1", "Physical security perimeters"),
            ("A.7.2", "Physical entry controls"),
        ],
        "Technological Controls": [
            ("A.8.1", "User endpoint devices"),
            ("A.8.2", "Privileged access rights"),
            ("A.8.3", "Information access restriction"),
        ],
    }
    statuses = ["implemented", "in_progress", "not_started", "verified", "implemented"]
    idx = 0
    for domain, controls in domains.items():
        for cid, title in controls:
            Control.objects.create(
                control_number=cid,
                title=title,
                domain=domain,
                applicability="applicable",
                implementation_status=statuses[idx % len(statuses)],
            )
            idx += 1


@pytest.mark.django_db
def test_soa_generation(client):
    _seed_controls()
    response = client.get("/api/v1/compliance/soa/")
    assert response.status_code == 200
    data = response.json()
    assert data["framework"] == "ISO 27001:2022"
    assert data["total_controls"] == 93
    assert "Organizational Controls" in data["domains"]
    assert "People Controls" in data["domains"]
    assert "Physical Controls" in data["domains"]
    assert "Technological Controls" in data["domains"]
    assert len(data["domains"]) == 4
    org = data["domains"]["Organizational Controls"]
    assert len(org["controls"]) == 37
    assert "compliance" in org
    assert "compliance_rate" in org["compliance"]


@pytest.mark.django_db
def test_soa_domain_compliance(client):
    _seed_controls()
    response = client.get("/api/v1/compliance/soa/")
    data = response.json()

    for domain_name, domain_data in data["domains"].items():
        compliance = domain_data["compliance"]
        assert compliance["total"] == len(domain_data["controls"])
        assert compliance["applicable"] >= 0
        assert compliance["implemented"] >= 0
        assert compliance["in_progress"] >= 0
        assert compliance["not_started"] >= 0
        rate = compliance["compliance_rate"]
        assert 0 <= rate <= 100

    overall = data["overall_compliance"]
    assert 0 <= overall["compliance_rate"] <= 100
    assert overall["total"] == 93


@pytest.mark.django_db
def test_soa_download(client):
    _seed_controls()
    response = client.get("/api/v1/compliance/soa/download/")
    assert response.status_code == 200
    assert response["Content-Disposition"] == 'attachment; filename="soa_report.json"'
    data = response.json()
    assert data["report_title"] == "Statement of Applicability"
    assert "domains" in data
    assert "overall_compliance_rate" in data
    assert len(data["domains"]) == 4


@pytest.mark.django_db
def test_nist_mapping(client):
    _seed_controls()
    response = client.get("/api/v1/compliance/nist-csf/")
    assert response.status_code == 200
    data = response.json()
    assert data["framework"] == "NIST CSF 2.0"
    assert data["total_functions"] == 6
    assert "GOVERN" in data["functions"]
    assert "IDENTIFY" in data["functions"]
    assert "PROTECT" in data["functions"]
    assert "DETECT" in data["functions"]
    assert "RESPOND" in data["functions"]
    assert "RECOVER" in data["functions"]

    govern = data["functions"]["GOVERN"]
    assert govern["id"] == "GV"
    assert "categories" in govern
    assert "GV.OC" in govern["categories"]
    assert govern["categories"]["GV.OC"]["name"] == "Organizational Context"


@pytest.mark.django_db
def test_nist_heatmap(client):
    _seed_controls()
    response = client.get("/api/v1/compliance/nist-csf/heatmap/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    for entry in data:
        assert "function" in entry
        assert "category_id" in entry
        assert "category_name" in entry
        assert "implementation_score" in entry
        assert "risk_level" in entry
        assert 0 <= entry["implementation_score"] <= 100
        assert entry["risk_level"] in ("low", "medium", "high", "critical")


@pytest.mark.django_db
def test_framework_compliance_rates(client):
    _seed_controls()
    response = client.get("/api/v1/compliance/frameworks/")
    assert response.status_code == 200
    data = response.json()
    assert "frameworks" in data
    assert len(data["frameworks"]) == 2

    iso = data["frameworks"][0]
    assert iso["framework"] == "ISO 27001:2022"
    assert "compliance_rate" in iso
    assert "domain_breakdown" in iso
    assert 0 <= iso["compliance_rate"] <= 100

    nist = data["frameworks"][1]
    assert nist["framework"] == "NIST CSF 2.0"
    assert "compliance_rate" in nist
    assert "function_breakdown" in nist
    assert 0 <= nist["compliance_rate"] <= 100


# --- Additional tests with task-specified function names ---


@pytest.mark.django_db
def test_list_controls_empty(client):
    """GET /api/v1/compliance/ returns 200 when no controls exist."""
    response = client.get("/api/v1/compliance/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.django_db
def test_create_control(client, control_data):
    """POST /api/v1/compliance/ creates a new control and returns 201."""
    response = client.post(
        "/api/v1/compliance/", data=control_data, content_type="application/json"
    )
    assert response.status_code == 201
    data = response.json()
    assert data["control_number"] == control_data["control_number"]
    assert data["title"] == control_data["title"]
    assert "id" in data


@pytest.mark.django_db
def test_assess_control(client, control_data):
    """PUT /api/v1/compliance/{id}/ updates implementation status (assess) and returns 200."""
    create_resp = client.post(
        "/api/v1/compliance/", data=control_data, content_type="application/json"
    )
    assert create_resp.status_code == 201
    control_id = create_resp.json()["id"]

    # Assess the control by updating its implementation status to "implemented"
    assessed = {**control_data, "implementation_status": "implemented"}
    response = client.put(
        f"/api/v1/compliance/{control_id}/",
        data=assessed,
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["implementation_status"] == "implemented"


@pytest.mark.django_db
def test_soa_export(client):
    """GET /api/v1/compliance/soa/ returns SOA data with 200."""
    _seed_controls()
    response = client.get("/api/v1/compliance/soa/")
    assert response.status_code == 200
    data = response.json()
    assert "framework" in data
    assert "domains" in data
    assert data["framework"] == "ISO 27001:2022"
