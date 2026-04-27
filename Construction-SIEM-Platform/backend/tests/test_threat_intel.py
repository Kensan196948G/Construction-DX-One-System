import pytest

from app.services.threat_intel import ThreatIntelService


@pytest.fixture
def service():
    return ThreatIntelService()


class TestThreatIntel:
    def test_check_ioc_ip_malicious(self, service):
        result = service.check_ioc("185.220.101.0", "ip")
        assert result["status"] == "success"
        assert result["malicious"] is True
        assert len(result["matches"]) == 1
        assert result["matches"][0]["threat_type"] == "C2 Server"
        assert result["risk_score"] > 0

    def test_check_ioc_ip_clean(self, service):
        result = service.check_ioc("8.8.8.8", "ip")
        assert result["status"] == "success"
        assert result["malicious"] is False
        assert len(result["matches"]) == 0
        assert result["risk_score"] == 0.0

    def test_check_ioc_hash(self, service):
        result = service.check_ioc("e99a18c428cb38d5f260853678922e03", "hash")
        assert result["status"] == "success"
        assert result["malicious"] is True
        assert result["matches"][0]["threat_type"] == "Ransomware"
        assert result["matches"][0]["severity"] == "critical"

    def test_check_ioc_domain(self, service):
        result = service.check_ioc("malware.example.com", "domain")
        assert result["status"] == "success"
        assert result["malicious"] is True
        assert result["matches"][0]["threat_type"] == "Malware Domain"

    def test_check_ioc_url(self, service):
        result = service.check_ioc("https://malicious-site.example.com/exploit", "url")
        assert result["status"] == "success"
        assert result["malicious"] is True
        assert result["matches"][0]["threat_type"] == "Exploit Kit"

    def test_check_ioc_email(self, service):
        result = service.check_ioc("attacker@example.org", "email")
        assert result["status"] == "success"
        assert result["malicious"] is True
        assert result["matches"][0]["threat_type"] == "Phishing Sender"

    def test_check_ioc_invalid_type(self, service):
        result = service.check_ioc("test", "invalid_type")
        assert result["status"] == "error"
        assert "error" in result

    def test_correlate_event_with_iocs(self, service):
        event = {
            "source_ip": "185.220.101.0",
            "destination_ip": "10.0.0.1",
            "source": "malware.example.com",
            "description": "Suspicious connection",
        }
        matches = service.correlate_event_with_iocs(event)
        assert len(matches) == 2
        fields = {m["field"] for m in matches}
        assert "source_ip" in fields
        assert "source" in fields

    def test_correlate_event_no_match(self, service):
        event = {
            "source_ip": "192.168.1.1",
            "source": "legit-server.local",
        }
        matches = service.correlate_event_with_iocs(event)
        assert len(matches) == 0

    def test_correlate_event_hash(self, service):
        event = {
            "file_hash": "d41d8cd98f00b204e9800998ecf8427e",
            "source": "endpoint",
        }
        matches = service.correlate_event_with_iocs(event)
        assert len(matches) == 1
        assert matches[0]["field"] == "file_hash"

    def test_get_recent_threats(self, service):
        service.check_ioc("185.220.101.0", "ip")
        service.check_ioc("8.8.8.8", "ip")
        recent = service.get_recent_threats(hours=24)
        assert len(recent) >= 2

    def test_get_recent_threats_empty(self, service):
        recent = service.get_recent_threats(hours=1)
        assert len(recent) == 0  # no checks yet in this test

    def test_add_ioc(self, service):
        result = service.add_ioc(
            value="5.5.5.5",
            ioc_type="ip",
            threat_type="C2",
            confidence=0.9,
            severity="critical",
            description="New C2 server",
            source="internal",
        )
        assert result["status"] == "success"

        check = service.check_ioc("5.5.5.5", "ip")
        assert check["malicious"] is True
        assert check["matches"][0]["confidence"] == 0.9

    def test_get_ioc_report(self, service):
        report = service.get_ioc_report("185.220.101.0")
        assert report["status"] == "success"
        assert report["total_matches"] == 1
        assert "C2 Server" in report["summary"]

    def test_get_ioc_report_no_match(self, service):
        report = service.get_ioc_report("1.1.1.1")
        assert report["status"] == "success"
        assert report["total_matches"] == 0

    def test_ioc_count(self, service):
        assert service.ioc_count == 10
        service.add_ioc("6.6.6.6", "ip", threat_type="Scanner")
        assert service.ioc_count == 11


@pytest.mark.asyncio
async def test_check_ioc_api(client):
    resp = await client.post("/api/v1/threat-intel/check", json={
        "value": "185.220.101.0",
        "ioc_type": "ip",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["malicious"] is True
    assert data["ioc_value"] == "185.220.101.0"


@pytest.mark.asyncio
async def test_correlate_event_api(client):
    resp = await client.post("/api/v1/threat-intel/correlate", json={
        "event_data": {
            "source_ip": "185.220.101.0",
            "source": "malware.example.com",
        }
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_matches"] >= 1


@pytest.mark.asyncio
async def test_recent_threats_api(client):
    await client.post("/api/v1/threat-intel/check", json={
        "value": "185.220.101.0",
        "ioc_type": "ip",
    })
    resp = await client.get("/api/v1/threat-intel/recent?hours=24")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) >= 1
