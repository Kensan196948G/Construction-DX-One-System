import logging
from datetime import UTC, datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

SAMPLE_IOCS: list[dict[str, Any]] = [
    {"value": "185.220.101.0", "type": "ip", "threat_type": "C2 Server", "confidence": 0.85, "severity": "high", "description": "Known Cobalt Strike C2 server", "source": "AlienVault OTX", "first_seen": "2024-01-15", "last_seen": "2024-06-01"},
    {"value": "45.33.32.156", "type": "ip", "threat_type": "Scanner", "confidence": 0.75, "severity": "medium", "description": "Internet-wide scanner IP", "source": "Greynoise", "first_seen": "2024-02-01", "last_seen": "2024-06-01"},
    {"value": "malware.example.com", "type": "domain", "threat_type": "Malware Domain", "confidence": 0.9, "severity": "high", "description": "Domain associated with malware distribution", "source": "VirusTotal", "first_seen": "2024-03-10", "last_seen": "2024-06-01"},
    {"value": "phishing.example.net", "type": "domain", "threat_type": "Phishing", "confidence": 0.8, "severity": "high", "description": "Phishing domain targeting construction firms", "source": "PhishTank", "first_seen": "2024-04-20", "last_seen": "2024-06-01"},
    {"value": "e99a18c428cb38d5f260853678922e03", "type": "hash", "threat_type": "Ransomware", "confidence": 0.95, "severity": "critical", "description": "Known ransomware hash (ABC Ransomware variant)", "source": "MalwareBazaar", "first_seen": "2024-05-01", "last_seen": "2024-06-01"},
    {"value": "d41d8cd98f00b204e9800998ecf8427e", "type": "hash", "threat_type": "Trojan", "confidence": 0.7, "severity": "medium", "description": "Suspicious trojan downloader", "source": "MalwareBazaar", "first_seen": "2024-03-15", "last_seen": "2024-05-30"},
    {"value": "https://malicious-site.example.com/exploit", "type": "url", "threat_type": "Exploit Kit", "confidence": 0.88, "severity": "high", "description": "URL serving exploit kit payloads", "source": "URLhaus", "first_seen": "2024-04-01", "last_seen": "2024-06-01"},
    {"value": "http://evil-payload.example.net/dropper", "type": "url", "threat_type": "Malware Payload", "confidence": 0.82, "severity": "high", "description": "Drops remote access trojan", "source": "URLhaus", "first_seen": "2024-05-10", "last_seen": "2024-06-01"},
    {"value": "attacker@example.org", "type": "email", "threat_type": "Phishing Sender", "confidence": 0.78, "severity": "medium", "description": "Known phishing email sender targeting Japan construction sector", "source": "AbuseIPDB", "first_seen": "2024-02-15", "last_seen": "2024-06-01"},
    {"value": "scam.engineer@example.co.jp", "type": "email", "threat_type": "Social Engineering", "confidence": 0.72, "severity": "medium", "description": "Social engineering attempts impersonating site engineers", "source": "Community Reports", "first_seen": "2024-04-01", "last_seen": "2024-06-01"},
]

VALID_IOC_TYPES = frozenset({"ip", "domain", "hash", "url", "email"})

SEVERITY_SCORE_MAP = {"critical": 9.0, "high": 7.0, "medium": 5.0, "low": 2.0}


class ThreatIntelService:
    def __init__(self) -> None:
        self._iocs: list[dict[str, Any]] = list(SAMPLE_IOCS)
        self._recent_updates: list[dict[str, Any]] = []

    def check_ioc(self, value: str, ioc_type: str) -> dict:
        if ioc_type not in VALID_IOC_TYPES:
            return {"status": "error", "error": f"Invalid ioc_type: {ioc_type}. Valid: {', '.join(sorted(VALID_IOC_TYPES))}"}

        matches: list[dict[str, Any]] = []
        value_lower = value.lower()
        for ioc in self._iocs:
            if ioc["type"] == ioc_type and ioc["value"].lower() == value_lower:
                matches.append({
                    "ioc_value": ioc["value"],
                    "ioc_type": ioc["type"],
                    "threat_type": ioc["threat_type"],
                    "confidence": ioc["confidence"],
                    "severity": ioc["severity"],
                    "description": ioc["description"],
                    "source": ioc["source"],
                    "first_seen": ioc["first_seen"],
                    "last_seen": ioc["last_seen"],
                })

        malicious = len(matches) > 0
        risk_score = 0.0
        if matches:
            risk_score = sum(
                match["confidence"] * SEVERITY_SCORE_MAP.get(match["severity"], 5.0)
                for match in matches
            ) / len(matches)

        self._recent_updates.append({
            "type": "check",
            "ioc_value": value,
            "ioc_type": ioc_type,
            "malicious": malicious,
            "timestamp": datetime.now(UTC).isoformat(),
        })

        return {
            "status": "success",
            "ioc_value": value,
            "ioc_type": ioc_type,
            "malicious": malicious,
            "matches": matches,
            "risk_score": round(risk_score, 2),
        }

    def get_ioc_report(self, ioc_value: str) -> dict:
        value_lower = ioc_value.lower()
        matches: list[dict[str, Any]] = []
        for ioc in self._iocs:
            if ioc["value"].lower() == value_lower:
                matches.append({
                    "ioc_value": ioc["value"],
                    "ioc_type": ioc["type"],
                    "threat_type": ioc["threat_type"],
                    "confidence": ioc["confidence"],
                    "severity": ioc["severity"],
                    "description": ioc["description"],
                    "source": ioc["source"],
                    "first_seen": ioc["first_seen"],
                    "last_seen": ioc["last_seen"],
                })

        risk_score = 0.0
        if matches:
            risk_score = sum(
                m["confidence"] * SEVERITY_SCORE_MAP.get(m["severity"], 5.0)
                for m in matches
            ) / len(matches)

        summary = "No threats found"
        if matches:
            types = list({m["threat_type"] for m in matches})
            summary = f"Found {len(matches)} match(es): {', '.join(types)}"

        ioc_type = matches[0]["ioc_type"] if matches else "unknown"

        return {
            "status": "success",
            "ioc_value": ioc_value,
            "ioc_type": ioc_type,
            "risk_score": round(risk_score, 2),
            "total_matches": len(matches),
            "matches": matches,
            "summary": summary,
        }

    def correlate_event_with_iocs(self, event_data: dict) -> list[dict]:
        matches: list[dict[str, Any]] = []
        searchable_fields = {
            "source_ip": "ip",
            "destination_ip": "ip",
            "source": "domain",
            "domain": "domain",
            "url": "url",
            "email": "email",
            "hash": "hash",
            "file_hash": "hash",
            "md5": "hash",
            "sha1": "hash",
            "sha256": "hash",
        }

        for field, ioc_type in searchable_fields.items():
            value = event_data.get(field)
            if not value or not isinstance(value, str):
                continue
            for ioc in self._iocs:
                if ioc["type"] == ioc_type and ioc["value"].lower() == value.lower():
                    matches.append({
                        "field": field,
                        "value": value,
                        "ioc_type": ioc_type,
                        "match": {
                            "ioc_value": ioc["value"],
                            "ioc_type": ioc["type"],
                            "threat_type": ioc["threat_type"],
                            "confidence": ioc["confidence"],
                            "severity": ioc["severity"],
                            "description": ioc["description"],
                            "source": ioc["source"],
                            "first_seen": ioc["first_seen"],
                            "last_seen": ioc["last_seen"],
                        },
                    })

        self._recent_updates.append({
            "type": "correlate",
            "fields_checked": len(searchable_fields),
            "matches_found": len(matches),
            "timestamp": datetime.now(UTC).isoformat(),
        })

        return matches

    def get_recent_threats(self, hours: int = 24) -> list[dict]:
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        recent: list[dict[str, Any]] = []
        for update in self._recent_updates:
            ts_str = update.get("timestamp", "")
            try:
                ts = datetime.fromisoformat(ts_str)
            except (ValueError, TypeError):
                continue
            if ts >= cutoff:
                recent.append({
                    "ioc_value": update.get("ioc_value", ""),
                    "ioc_type": update.get("ioc_type", ""),
                    "threat_type": "check" if update.get("malicious") else "benign",
                    "confidence": 0.5,
                    "severity": "medium",
                    "last_seen": ts_str,
                })
        return recent[-100:]

    def add_ioc(self, value: str, ioc_type: str, threat_type: str = "unknown",
                confidence: float = 0.5, severity: str = "medium",
                description: str = "", source: str = "internal") -> dict:
        if ioc_type not in VALID_IOC_TYPES:
            return {"status": "error", "error": f"Invalid type: {ioc_type}"}
        entry = {
            "value": value, "type": ioc_type, "threat_type": threat_type,
            "confidence": confidence, "severity": severity, "description": description,
            "source": source, "first_seen": datetime.now(UTC).strftime("%Y-%m-%d"),
            "last_seen": datetime.now(UTC).strftime("%Y-%m-%d"),
        }
        self._iocs.append(entry)
        self._recent_updates.append({
            "type": "add_ioc",
            "ioc_value": value,
            "ioc_type": ioc_type,
            "timestamp": datetime.now(UTC).isoformat(),
        })
        return {"status": "success", "ioc_value": value, "ioc_type": ioc_type}

    @property
    def ioc_count(self) -> int:
        return len(self._iocs)


_threat_intel_instance: ThreatIntelService | None = None


def get_threat_intel_service() -> ThreatIntelService:
    global _threat_intel_instance
    if _threat_intel_instance is None:
        _threat_intel_instance = ThreatIntelService()
    return _threat_intel_instance
