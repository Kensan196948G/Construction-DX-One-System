import pytest
from django.test import Client


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def risk_data():
    return {
        "title": "Test Risk",
        "description": "A test risk description",
        "category": "security",
        "likelihood": 4,
        "impact": 3,
        "status": "open",
        "owner": "test-owner",
    }


@pytest.fixture
def control_data():
    return {
        "control_number": "A.5.1",
        "title": "Policies for information security",
        "domain": "Organizational Controls",
        "applicability": "applicable",
        "implementation_status": "not_started",
        "description": "Information security policy shall be defined.",
    }


@pytest.fixture
def audit_data():
    return {
        "title": "Annual ISO 27001 Audit",
        "scope": "Full organizational scope",
        "auditor": "External Auditor",
        "status": "planned",
    }
