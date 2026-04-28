"""Tests for GRC integration API endpoints."""
import json
import pytest

INTEGRATION_KEY = "dev-integration-key-change-in-prod"
HEADERS = {"HTTP_X_INTEGRATION_KEY": INTEGRATION_KEY}


@pytest.mark.django_db
def test_risk_items_requires_key(client):
    resp = client.get("/api/v1/integration/risk-items/")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_risk_items_wrong_key(client):
    resp = client.get("/api/v1/integration/risk-items/", HTTP_X_INTEGRATION_KEY="wrong")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_risk_items_empty(client):
    resp = client.get("/api/v1/integration/risk-items/", **HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_items"] == []
    assert data["total"] == 0


@pytest.mark.django_db
def test_risk_summary_requires_key(client):
    resp = client.get("/api/v1/integration/risk-summary/")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_risk_summary_empty(client):
    resp = client.get("/api/v1/integration/risk-summary/", **HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["high_risk_items"] == []
    assert "generated_at" in data


@pytest.mark.django_db
def test_security_events_requires_key(client):
    resp = client.post(
        "/api/v1/integration/security-events/",
        data=json.dumps({"alerts": []}),
        content_type="application/json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_security_events_low_severity_ignored(client):
    resp = client.post(
        "/api/v1/integration/security-events/",
        data=json.dumps({
            "alerts": [{"title": "Low Alert", "severity": "low", "description": "minor"}]
        }),
        content_type="application/json",
        **HEADERS,
    )
    assert resp.status_code == 201
    assert resp.json()["created_risks"] == 0


@pytest.mark.django_db
def test_security_events_high_severity_creates_risk(client):
    resp = client.post(
        "/api/v1/integration/security-events/",
        data=json.dumps({
            "alerts": [
                {"title": "Brute Force", "severity": "high", "description": "Login attacks"},
                {"title": "Ransomware", "severity": "critical", "description": "Encrypted files"},
            ]
        }),
        content_type="application/json",
        **HEADERS,
    )
    assert resp.status_code == 201
    assert resp.json()["created_risks"] == 2


@pytest.mark.django_db
def test_recovery_plan_sync_requires_key(client):
    resp = client.post(
        "/api/v1/integration/recovery-plans/sync/",
        data=json.dumps({"resolved_risk_ids": []}),
        content_type="application/json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_recovery_plan_sync_empty(client):
    resp = client.post(
        "/api/v1/integration/recovery-plans/sync/",
        data=json.dumps({"resolved_risk_ids": []}),
        content_type="application/json",
        **HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["updated_risks"] == 0


@pytest.mark.django_db
def test_risk_items_with_min_score_filter(client, risk_data):
    client.post("/api/v1/risks/", data=risk_data, content_type="application/json")
    resp = client.get(
        "/api/v1/integration/risk-items/?min_score=20",
        **HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 0
