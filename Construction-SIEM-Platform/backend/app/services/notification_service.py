import logging
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.notification import NotificationLog

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, db: AsyncSession | None = None):
        self.db = db
        self._smtp_server = getattr(settings, "smtp_server", "smtp.example.com")
        self._smtp_port = getattr(settings, "smtp_port", 587)
        self._smtp_user = getattr(settings, "smtp_user", "notify@example.com")
        self._smtp_password = getattr(settings, "smtp_password", "")
        self._teams_webhook = getattr(settings, "teams_webhook", "https://outlook.office.com/webhook/example")
        self._twilio_account = getattr(settings, "twilio_account_sid", "ACxxxxxxxxxx")
        self._twilio_token = getattr(settings, "twilio_auth_token", "")
        self._twilio_from = getattr(settings, "twilio_phone_number", "+15551234567")

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: str | None = None,
    ) -> dict:
        try:
            logger.info("Sending email to %s: subject=%s", to, subject)
            simulated_message_id = str(uuid.uuid4())
            notification_id = await self._log_notification(
                channel="email",
                recipient=to,
                subject=subject,
                body=body,
                status="sent",
            )
            return {
                "success": True,
                "channel": "email",
                "recipient": to,
                "message_id": simulated_message_id,
                "notification_id": notification_id,
            }
        except Exception as e:
            logger.error("Failed to send email to %s: %s", to, e)
            await self._log_notification(
                channel="email",
                recipient=to,
                subject=subject,
                body=body,
                status="failed",
                error_message=str(e),
            )
            return {"success": False, "channel": "email", "error": str(e)}

    async def send_teams(
        self,
        webhook_url: str | None = None,
        title: str = "",
        message: str = "",
        severity: str = "low",
    ) -> dict:
        url = webhook_url or self._teams_webhook
        try:
            severity_colors = {"critical": "FF0000", "high": "FF6600", "medium": "FFCC00", "low": "00FF00"}
            color = severity_colors.get(severity, "00FF00")
            card = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "summary": title,
                "themeColor": color,
                "title": title,
                "text": message,
                "sections": [{"facts": [{"name": "Severity", "value": severity}]}],
            }
            logger.info("Sending Teams notification to %s: title=%s", url, title)
            notification_id = await self._log_notification(
                channel="teams",
                recipient=url,
                subject=title,
                body=message,
                status="sent",
            )
            return {
                "success": True,
                "channel": "teams",
                "card": card,
                "notification_id": notification_id,
            }
        except Exception as e:
            logger.error("Failed to send Teams notification: %s", e)
            await self._log_notification(
                channel="teams",
                recipient=url,
                subject=title,
                body=message,
                status="failed",
                error_message=str(e),
            )
            return {"success": False, "channel": "teams", "error": str(e)}

    async def send_sms(self, phone: str, message: str) -> dict:
        try:
            logger.info("Sending SMS to %s: %s", phone, message[:50])
            simulated_sid = f"SM{uuid.uuid4().hex[:34]}"
            notification_id = await self._log_notification(
                channel="sms",
                recipient=phone,
                subject=None,
                body=message,
                status="sent",
            )
            return {
                "success": True,
                "channel": "sms",
                "recipient": phone,
                "sid": simulated_sid,
                "notification_id": notification_id,
            }
        except Exception as e:
            logger.error("Failed to send SMS to %s: %s", phone, e)
            await self._log_notification(
                channel="sms",
                recipient=phone,
                subject=None,
                body=message,
                status="failed",
                error_message=str(e),
            )
            return {"success": False, "channel": "sms", "error": str(e)}

    async def send_alert_notification(self, alert, channels: list[str]) -> dict:
        results = {}
        for channel in channels:
            severity = getattr(alert, "severity", "low")
            title = f"Alert: {getattr(alert, 'title', 'Untitled')}"
            body = (
                f"Alert ID: {getattr(alert, 'id', 'N/A')}\n"
                f"Severity: {severity}\n"
                f"Source: {getattr(alert, 'source', 'N/A')}\n"
                f"Description: {getattr(alert, 'description', 'N/A')}\n"
                f"Site: {getattr(alert, 'site', 'N/A')}\n"
                f"Time: {datetime.utcnow().isoformat()}"
            )
            if channel == "email":
                recipient = getattr(settings, "alert_email_recipient", "admin@example.com")
                results[channel] = await self.send_email(to=recipient, subject=title, body=body)
            elif channel == "teams":
                results[channel] = await self.send_teams(title=title, message=body, severity=severity)
            elif channel == "sms":
                recipient = getattr(settings, "alert_sms_recipient", "+15551234567")
                results[channel] = await self.send_sms(phone=recipient, message=body)
            else:
                results[channel] = {"success": False, "error": f"Unknown channel: {channel}"}
        return results

    async def get_notification_history(
        self,
        entity_id: str | None = None,
        limit: int = 50,
    ) -> list[NotificationLog]:
        if self.db is None:
            return []
        query = select(NotificationLog).order_by(NotificationLog.created_at.desc()).limit(limit)
        if entity_id:
            query = query.where(
                (NotificationLog.related_entity_id == entity_id)
                | (NotificationLog.recipient.contains(entity_id))
            )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def _log_notification(
        self,
        channel: str,
        recipient: str,
        subject: str | None,
        body: str,
        status: str,
        error_message: str | None = None,
    ) -> str | None:
        if self.db is None:
            return None
        log = NotificationLog(
            channel=channel,
            recipient=recipient,
            subject=subject,
            body=body,
            status=status,
            error_message=error_message,
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log.id


def get_notification_service(db: AsyncSession) -> NotificationService:
    return NotificationService(db=db)
