import pytest

from apps.risks.models import Risk


@pytest.mark.django_db
def test_risk_list_empty(client):
    response = client.get("/api/v1/risks/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.django_db
def test_risk_create(client, risk_data):
    response = client.post("/api/v1/risks/", data=risk_data, content_type="application/json")
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == risk_data["title"]
    assert data["risk_score"] == 12.0  # likelihood=4 * impact=3
    assert "id" in data


@pytest.mark.django_db
def test_risk_score_auto_calculated(client, risk_data):
    risk_data["likelihood"] = 5
    risk_data["impact"] = 5
    response = client.post("/api/v1/risks/", data=risk_data, content_type="application/json")
    assert response.status_code == 201
    assert response.json()["risk_score"] == 25.0


@pytest.mark.django_db
def test_risk_score_readonly(client, risk_data):
    risk_data["risk_score"] = 999.0
    response = client.post("/api/v1/risks/", data=risk_data, content_type="application/json")
    assert response.status_code == 201
    assert response.json()["risk_score"] == 12.0


@pytest.mark.django_db
def test_risk_detail_get(client, risk_data):
    create_resp = client.post("/api/v1/risks/", data=risk_data, content_type="application/json")
    risk_id = create_resp.json()["id"]
    response = client.get(f"/api/v1/risks/{risk_id}/")
    assert response.status_code == 200
    assert response.json()["id"] == risk_id


@pytest.mark.django_db
def test_risk_detail_update(client, risk_data):
    create_resp = client.post("/api/v1/risks/", data=risk_data, content_type="application/json")
    risk_id = create_resp.json()["id"]
    updated = {**risk_data, "status": "mitigated"}
    response = client.put(
        f"/api/v1/risks/{risk_id}/", data=updated, content_type="application/json"
    )
    assert response.status_code == 200
    assert response.json()["status"] == "mitigated"


@pytest.mark.django_db
def test_risk_detail_delete(client, risk_data):
    create_resp = client.post("/api/v1/risks/", data=risk_data, content_type="application/json")
    risk_id = create_resp.json()["id"]
    response = client.delete(f"/api/v1/risks/{risk_id}/")
    assert response.status_code == 204
    assert not Risk.objects.filter(pk=risk_id).exists()


@pytest.mark.django_db
def test_risk_filter_by_status(client, risk_data):
    client.post("/api/v1/risks/", data=risk_data, content_type="application/json")
    closed_data = {**risk_data, "title": "Closed Risk", "status": "closed"}
    client.post("/api/v1/risks/", data=closed_data, content_type="application/json")

    response = client.get("/api/v1/risks/?status=open")
    assert response.status_code == 200
    results = response.json()
    assert all(r["status"] == "open" for r in results)


@pytest.mark.django_db
def test_risk_not_found(client):
    import uuid

    response = client.get(f"/api/v1/risks/{uuid.uuid4()}/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_risk_create_invalid(client):
    response = client.post("/api/v1/risks/", data={}, content_type="application/json")
    assert response.status_code == 400
