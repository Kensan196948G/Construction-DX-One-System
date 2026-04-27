import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RFC(Base):
    __tablename__ = "rfcs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text)
    change_type: Mapped[str] = mapped_column(String(30), default="normal")
    status: Mapped[str] = mapped_column(String(30), default="draft")
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    risk_level: Mapped[str] = mapped_column(String(20), default="medium")
    requester: Mapped[str | None] = mapped_column(String(200), nullable=True)
    affected_systems: Mapped[str | None] = mapped_column(Text, nullable=True)
    planned_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    planned_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cab_meeting_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
