import threading
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

IDLE_TIMEOUT = timedelta(minutes=30)
ABSOLUTE_TIMEOUT = timedelta(hours=8)


class SessionRecord:
    def __init__(self, user_id: str, ip: str | None, user_agent: str | None):
        self.session_id = uuid.uuid4().hex
        self.user_id = user_id
        self.ip = ip
        self.user_agent = user_agent
        self.created_at = datetime.now(UTC)
        self.last_activity = self.created_at
        self.is_active = True

    @property
    def expired(self) -> bool:
        now = datetime.now(UTC)
        idle_expired = (now - self.last_activity) > IDLE_TIMEOUT
        absolute_expired = (now - self.created_at) > ABSOLUTE_TIMEOUT
        return idle_expired or absolute_expired

    def touch(self) -> None:
        self.last_activity = datetime.now(UTC)


class SessionManager:
    _instance: "SessionManager | None" = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "SessionManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._sessions: dict[str, SessionRecord] = {}
        return cls._instance

    def create_session(
        self, user_id: str, ip: str | None = None, user_agent: str | None = None
    ) -> str:
        record = SessionRecord(user_id, ip, user_agent)
        self._sessions[record.session_id] = record
        return record.session_id

    def validate_session(self, session_id: str) -> bool:
        record = self._sessions.get(session_id)
        if not record:
            return False
        if not record.is_active or record.expired:
            record.is_active = False
            return False
        record.touch()
        return True

    def extend_session(self, session_id: str) -> bool:
        record = self._sessions.get(session_id)
        if not record or not record.is_active or record.expired:
            return False
        record.touch()
        return True

    def invalidate_session(self, session_id: str) -> None:
        record = self._sessions.get(session_id)
        if record:
            record.is_active = False

    def invalidate_user_sessions(self, user_id: str) -> None:
        for record in list(self._sessions.values()):
            if record.user_id == user_id:
                record.is_active = False

    def get_active_sessions(self, user_id: str) -> list[dict[str, Any]]:
        result = []
        for record in self._sessions.values():
            if record.user_id == user_id and record.is_active and not record.expired:
                result.append({
                    "session_id": record.session_id,
                    "ip": record.ip,
                    "user_agent": record.user_agent,
                    "created_at": record.created_at,
                    "last_activity": record.last_activity,
                })
        return result

    def cleanup_expired_sessions(self) -> int:
        expired_ids = [
            sid for sid, record in self._sessions.items()
            if not record.is_active or record.expired
        ]
        for sid in expired_ids:
            del self._sessions[sid]
        return len(expired_ids)


session_manager = SessionManager()
