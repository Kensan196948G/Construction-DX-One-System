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
