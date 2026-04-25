import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Alert(Base):
    """Correlated SIEM alert generated from one or more SecurityEvents."""

    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Severity / status
    severity: Mapped[str] = mapped_column(
        String(16), nullable=False, default="medium", index=True
    )  # low / medium / high / critical
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="open", index=True
    )  # open / investigating / resolved / false_positive

    # Risk
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    event_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Correlation
    rule_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    # Assignment
    assigned_to: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Timestamps
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # MITRE ATT&CK
    mitre_technique: Mapped[str | None] = mapped_column(String(32), nullable=True)
    mitre_tactic: Mapped[str | None] = mapped_column(String(64), nullable=True)
