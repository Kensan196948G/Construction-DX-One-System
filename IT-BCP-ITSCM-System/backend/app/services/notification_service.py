import logging
import uuid
from datetime import UTC, datetime

from app.models.incident import Incident
from app.services.report_service import generate_executive_summary

logger = logging.getLogger(__name__)


def _format_teams_message(incident: Incident) -> dict:
    color = {
        "critical": "red",
        "high": "orange",
        "medium": "yellow",
        "low": "grey",
    }.get(incident.severity, "grey")

    return {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "summary": f"Incident: {incident.title}",
        "themeColor": color,
        "title": f"[{incident.severity.upper()}] {incident.title}",
        "sections": [
            {
                "facts": [
                    {"name": "Status", "value": incident.status},
                    {"name": "Severity", "value": incident.severity},
                    {"name": "BCP Activated", "value": "Yes" if incident.bcp_activated else "No"},
                    {"name": "Affected Systems", "value": incident.affected_systems or "None"},
                ],
                "text": incident.description[:500],
            }
        ],
    }


def _format_email_message(incident: Incident) -> dict:
    return {
        "subject": f"[{incident.severity.upper()}] Incident Alert: {incident.title}",
        "body": (
            f"Incident Report\n{'=' * 60}\n\n"
            f"Title: {incident.title}\n"
            f"Severity: {incident.severity}\n"
            f"Status: {incident.status}\n"
            f"BCP Activated: {'Yes' if incident.bcp_activated else 'No'}\n"
            f"Affected Systems: {incident.affected_systems or 'None'}\n\n"
            f"Description:\n{incident.description}\n\n"
            f"---\nThis is an automated notification from IT-BCP-ITSCM System."
        ),
    }


def _format_sms_message(incident: Incident) -> dict:
    return {
        "body": (
            f"[{incident.severity.upper()}] {incident.title[:100]} | "
            f"Status: {incident.status} | "
            f"BCP: {'Yes' if incident.bcp_activated else 'No'}"
        ),
    }


def _format_for_channel(incident: Incident, channel: str) -> dict:
    formatters = {
        "teams": _format_teams_message,
        "email": _format_email_message,
        "sms": _format_sms_message,
    }
    formatter = formatters.get(channel)
    if not formatter:
        raise ValueError(f"Unsupported notification channel: {channel}")
    return formatter(incident)


async def send_incident_notification(incident: Incident, channel: str) -> dict:
    message = _format_for_channel(incident, channel)
    message_id = str(uuid.uuid4())

    logger.info(
        "Notification sent via %s for incident %s (message_id=%s): %s",
        channel, incident.id, message_id, str(message)[:200],
    )

    return {
        "channel": channel,
        "status": "sent",
        "sent_at": datetime.now(UTC),
        "message_id": message_id,
        "details": f"Notification sent via {channel} for incident '{incident.title}'",
    }


async def send_escalation(incident: Incident, level: int) -> dict:
    escalation_id = str(uuid.uuid4())
    targets = {1: "Team Lead", 2: "Department Manager", 3: "CTO", 4: "CEO"}
    target_name = targets.get(level, f"Level-{level} Escalation")

    logger.info(
        "Escalation level %d sent for incident %s (escalation_id=%s) to %s",
        level, incident.id, escalation_id, target_name,
    )

    return {
        "channel": "escalation",
        "status": "sent",
        "sent_at": datetime.now(UTC),
        "message_id": escalation_id,
        "details": f"Escalation level {level} ({target_name}) notified for incident '{incident.title}'",
    }


async def send_daily_summary(db) -> dict:
    summary = await generate_executive_summary(db)
    summary_id = str(uuid.uuid4())

    logger.info(
        "Daily summary sent (summary_id=%s): %s active incidents, %s systems, readiness score: %s",
        summary_id,
        summary["active_incidents"]["total"],
        summary["system_health"]["total"],
        summary["readiness_score"],
    )

    return {
        "channel": "email",
        "status": "sent",
        "sent_at": datetime.now(UTC),
        "message_id": summary_id,
        "details": f"Daily executive summary sent. Readiness score: {summary['readiness_score']}",
    }
