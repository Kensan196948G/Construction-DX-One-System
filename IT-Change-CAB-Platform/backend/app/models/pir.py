import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PIR(Base):
    __tablename__ = "pirs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rfc_id: Mapped[str] = mapped_column(String(36), unique=True)
    review_status: Mapped[str] = mapped_column(String(20), default="pending")
    reviewer_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    review_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    actual_start_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    actual_end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    was_successful: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    issues_encountered: Mapped[str | None] = mapped_column(Text, nullable=True)
    lessons_learned: Mapped[str | None] = mapped_column(Text, nullable=True)
    rollback_effectiveness: Mapped[str | None] = mapped_column(String(20), nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_actions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
