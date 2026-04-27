import uuid
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BusinessProcess(Base):
    __tablename__ = "business_processes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    process_name: Mapped[str] = mapped_column(String(300), unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    department: Mapped[str | None] = mapped_column(String(200), nullable=True)
    criticality: Mapped[str] = mapped_column(String(20), default="medium")
    rto_minutes: Mapped[int] = mapped_column(Integer, default=240)
    rpo_minutes: Mapped[int] = mapped_column(Integer, default=60)
    recovery_priority: Mapped[int] = mapped_column(Integer, default=10)
    dependencies: Mapped[list | None] = mapped_column(JSON, nullable=True)
    peak_business_hours: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    legal_requirement: Mapped[bool] = mapped_column(Boolean, default=False)
    financial_impact_per_hour: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class BIARevision(Base):
    __tablename__ = "bia_revisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    version: Mapped[int] = mapped_column(Integer)
    reviewed_by: Mapped[str] = mapped_column(String(200))
    review_date: Mapped[date] = mapped_column(Date)
    changes_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_review_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
