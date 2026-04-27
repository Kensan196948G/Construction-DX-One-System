import pytest

from app.services.message_queue import EventNormalizer, MessageQueue


@pytest.fixture
def mq():
    q = MessageQueue()
    yield q
    q.clear()


@pytest.fixture
def normalizer():
    return EventNormalizer()


class TestMessageQueue:
    def test_publish_consume(self, mq):
        received = []
        mq.consume("security_events", lambda msg: received.append(msg))
        result = mq.publish("security_events", "test-key", {"data": "hello"})
        assert result["success"] is True
        assert len(received) == 1
        assert received[0]["key"] == "test-key"
        assert received[0]["value"]["data"] == "hello"

    def test_publish_invalid_topic(self, mq):
        result = mq.publish("invalid_topic", "k", "v")
        assert result["success"] is False
        assert "error" in result

    def test_consume_invalid_topic(self, mq):
        mq.consume("bad_topic", lambda msg: None)
        assert len(mq._subscriptions) == 0

    def test_topic_routing(self, mq):
        topics = ["security_events", "alerts", "anomaly_scores", "playbook_triggers"]
        received = {t: [] for t in topics}
        for t in topics:
            mq.consume(t, lambda msg, tt=t: received[tt].append(msg))
        mq.publish("security_events", "k1", {"event": "port_scan"})
        mq.publish("alerts", "k2", {"alert": "critical"})
        mq.publish("anomaly_scores", "k3", {"score": 0.95})
        mq.publish("playbook_triggers", "k4", {"playbook": "ransomware"})
        assert len(received["security_events"]) == 1
        assert len(received["alerts"]) == 1
        assert len(received["anomaly_scores"]) == 1
        assert len(received["playbook_triggers"]) == 1

    def test_get_messages(self, mq):
        mq.publish("security_events", "k1", {"a": 1})
        mq.publish("security_events", "k2", {"a": 2})
        messages = mq.get_messages("security_events")
        assert len(messages) == 2

    def test_audit_log(self, mq):
        mq.publish("security_events", "k1", {"a": 1})
        mq.publish("alerts", "k2", {"a": 2})
        logs = mq.get_audit_log()
        assert len(logs) == 2
        assert logs[0]["type"] == "publish"


class TestEventNormalizer:
    def test_normalize_syslog(self, normalizer):
        raw = "Mar  1 12:34:56 webserver sshd[1234]: Failed password for root from 10.0.0.1"
        result = normalizer.normalize_event(raw, "syslog")
        assert result["source_type"] == "syslog"
        assert result["severity"] == "low"
        assert "cef_formatted" in result
        assert "CEF:0" in result["cef_formatted"]

    def test_normalize_syslog_dict(self, normalizer):
        raw = {"host": "auth-server", "message": "Failed login attempt", "severity": "err"}
        result = normalizer.normalize_event(raw, "syslog")
        assert result["source"] == "auth-server"
        assert result["severity"] == "high"

    def test_normalize_windows_event(self, normalizer):
        raw = {"event_id": "4625", "computer": "DC01", "message": "Logon failure", "severity": "err"}
        result = normalizer.normalize_event(raw, "windows_event")
        assert result["source_type"] == "windows_event"
        assert "4625" in result["event_type"]
        assert result["source"] == "DC01"

    def test_normalize_graph_api(self, normalizer):
        raw = {
            "auditLog": {
                "activity": "SignInFailed",
                "initiatedBy": {"user": {"id": "user@contoso.com"}},
                "detail": "Invalid password",
                "severity": "high",
            }
        }
        result = normalizer.normalize_event(raw, "graph_api")
        assert result["source_type"] == "graph_api"
        assert "SignInFailed" in result["event_type"]
        assert result["source"] == "user@contoso.com"
        assert result["severity"] == "high"

    def test_normalize_snmp(self, normalizer):
        raw = {"oid": "1.3.6.1.4.1.9.9.117", "agent": "switch-01", "message": "Link down", "severity": "critical"}
        result = normalizer.normalize_event(raw, "snmp")
        assert result["source_type"] == "snmp"
        assert result["source"] == "switch-01"
        assert result["severity"] == "critical"

    def test_normalize_custom(self, normalizer):
        raw = {"event_type": "file_export", "source": "cad-server", "severity": "medium", "description": "Large BIM export"}
        result = normalizer.normalize_event(raw, "custom")
        assert result["source_type"] == "custom"
        assert result["event_type"] == "file_export"
        assert result["source"] == "cad-server"

    def test_normalize_unknown_source(self, normalizer):
        with pytest.raises(ValueError, match="Unknown source_type"):
            normalizer.normalize_event("test", "unknown_type")

    def test_cef_format(self, normalizer):
        result = normalizer.normalize_event("test message", "syslog")
        cef = result["cef_formatted"]
        assert cef.startswith("CEF:0|")
        parts = cef.split("|")
        assert len(parts) >= 7
