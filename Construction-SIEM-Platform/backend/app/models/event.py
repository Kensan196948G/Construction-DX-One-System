import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SecurityEvent(Base):
    """Raw security event ingested from log sources (syslog, CEF, JSON, etc.)."""

    __tablename__ = "security_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Event identification
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(
        String(16), nullable=False, default="info", index=True
    )  # info / low / medium / high / critical
    source_ip: Mapped[str | None] = mapped_column(String(45), nullable=True, index=True)
    source_hostname: Mapped[str | None] = mapped_column(String(256), nullable=True)
    destination_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    destination_port: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Timestamps
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # Payload
    raw_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    log_source: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Risk scoring
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Correlation
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    is_processed: Mapped[bool] = mapped_column(default=False)
