import uuid
from datetime import UTC, date, datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    permissions: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    is_privileged: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    user_roles: Mapped[list["UserRole"]] = relationship("UserRole", back_populates="role")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    employee_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str | None] = mapped_column(String(100))
    user_type: Mapped[str] = mapped_column(String(20), nullable=False, default="regular")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    ad_object_id: Mapped[str | None] = mapped_column(String(100))
    entra_object_id: Mapped[str | None] = mapped_column(String(100))
    hengeone_user_id: Mapped[str | None] = mapped_column(String(100))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime)
    account_expiry_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    user_roles: Mapped[list["UserRole"]] = relationship(
        "UserRole", foreign_keys="[UserRole.user_id]", back_populates="user"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", foreign_keys="AuditLog.actor_id", back_populates="actor"
    )
    access_requests: Mapped[list["AccessRequest"]] = relationship(
        "AccessRequest", foreign_keys="AccessRequest.requester_id", back_populates="requester"
    )


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )
    granted_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"))
    granted_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="user_roles")
    role: Mapped["Role"] = relationship("Role", back_populates="user_roles")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"))
    actor_ip: Mapped[str | None] = mapped_column(String(45))
    target_type: Mapped[str | None] = mapped_column(String(100))
    target_id: Mapped[str | None] = mapped_column(String(200))
    payload: Mapped[dict | None] = mapped_column(JSON)
    result: Mapped[str | None] = mapped_column(String(20))
    prev_hash: Mapped[str | None] = mapped_column(String(64))
    hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    actor: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[actor_id], back_populates="audit_logs"
    )


class AccessRequest(Base):
    __tablename__ = "access_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    requester_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"))
    target_resource: Mapped[str] = mapped_column(String(200), nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    requested_role_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("roles.id"))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    approver_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    requester: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[requester_id], back_populates="access_requests"
    )
