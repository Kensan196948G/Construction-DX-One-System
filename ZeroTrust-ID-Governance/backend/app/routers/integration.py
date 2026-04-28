"""Integration API router for cross-system communication."""
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.models.user import AuditLog, Role, User, UserRole

router = APIRouter(prefix="/integration", tags=["integration"])

_api_key_header = APIKeyHeader(name="X-Integration-Key", auto_error=False)


async def verify_integration_key(
    api_key: Annotated[str | None, Depends(_api_key_header)],
) -> None:
    settings = get_settings()
    expected = getattr(settings, "integration_api_key", "dev-integration-key-change-in-prod")
    if not api_key or api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing integration API key",
        )


IntegrationAuth = Depends(verify_integration_key)


# ── Schemas ───────────────────────────────────────────────────────────────────

class AuthEvent(BaseModel):
    event_type: str          # login_success | login_failed | logout | mfa_failed
    user_id: str | None
    username: str | None
    actor_ip: str | None
    timestamp: datetime
    severity: str            # low | medium | high | critical
    details: dict


class AuthEventBatch(BaseModel):
    events: list[AuthEvent]
    source_system: str = "ZTIG"


class IdentitySummary(BaseModel):
    total_users: int
    active_users: int
    inactive_users: int
    privileged_users: int
    external_users: int
    users_with_expiry: int
    generated_at: datetime


class RecentAuthEventsResponse(BaseModel):
    events: list[AuthEvent]
    period_hours: int
    total_count: int


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/identity-summary",
    response_model=IdentitySummary,
    summary="Get identity summary for GRC integration",
)
async def get_identity_summary(
    _: None = IntegrationAuth,
    db: AsyncSession = Depends(get_db),
):
    """Provide aggregated identity/access data to GRC for compliance reporting."""
    result = await db.execute(select(User))
    users = result.scalars().all()

    total = len(users)
    active = sum(1 for u in users if u.status == "active")
    inactive = total - active
    external = sum(1 for u in users if u.user_type == "external")
    with_expiry = sum(1 for u in users if u.account_expiry_date is not None)

    priv_result = await db.execute(
        select(UserRole.user_id).join(Role, UserRole.role_id == Role.id).where(
            Role.is_privileged == True  # noqa: E712
        )
    )
    privileged_count = len(set(priv_result.scalars().all()))

    return IdentitySummary(
        total_users=total,
        active_users=active,
        inactive_users=inactive,
        privileged_users=privileged_count,
        external_users=external,
        users_with_expiry=with_expiry,
        generated_at=datetime.now(UTC),
    )


@router.get(
    "/auth-events/recent",
    response_model=RecentAuthEventsResponse,
    summary="Get recent auth events for SIEM integration",
)
async def get_recent_auth_events(
    hours: int = Query(1, ge=1, le=24, description="How many hours back to query"),
    event_type: str | None = Query(None, description="Filter by event type"),
    _: None = IntegrationAuth,
    db: AsyncSession = Depends(get_db),
):
    """Provide recent authentication events to SIEM for security monitoring."""
    cutoff = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=hours)
    stmt = select(AuditLog).where(AuditLog.created_at >= cutoff)
    if event_type:
        stmt = stmt.where(AuditLog.action == event_type)
    stmt = stmt.order_by(AuditLog.created_at.desc()).limit(500)

    result = await db.execute(stmt)
    logs = result.scalars().all()

    events = [
        AuthEvent(
            event_type=log.action,
            user_id=log.actor_id,
            username=log.payload.get("username") if log.payload else None,
            actor_ip=log.actor_ip,
            timestamp=log.created_at,
            severity=_classify_severity(log.action),
            details=log.payload or {},
        )
        for log in logs
    ]

    return RecentAuthEventsResponse(events=events, period_hours=hours, total_count=len(events))


@router.post(
    "/webhook/notify",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Receive notifications from other systems",
)
async def receive_notification(
    payload: dict,
    _: None = IntegrationAuth,
):
    """Receive event notifications from SIEM or other integrated systems."""
    # Log received notification (could be persisted to DB in production)
    return None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _classify_severity(action: str) -> str:
    critical = {"privilege_escalation", "admin_login", "account_lockout"}
    high = {"login_failed", "mfa_failed", "password_reset"}
    medium = {"logout", "session_expired", "token_refresh"}
    if action in critical:
        return "critical"
    if action in high:
        return "high"
    if action in medium:
        return "medium"
    return "low"
