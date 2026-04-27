import uuid
from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.user import User
from app.services.audit_service import log_action


class EntraIDSync:
    def __init__(self):
        settings = get_settings()
        self.base_url = settings.entraid_base_url
        self.tenant_id = settings.entraid_tenant_id
        self.client_id = settings.entraid_client_id
        self.client_secret = settings.entraid_client_secret
        self.simulated = not bool(self.base_url)

    async def _call_api(self, method: str, path: str, **kwargs) -> dict:
        if self.simulated:
            return {
                "simulated": True,
                "method": method,
                "path": path,
                "status": "success",
                "timestamp": datetime.now(UTC).isoformat(),
            }
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url.rstrip('/')}{path}"
            headers = {"Authorization": f"Bearer {await self._get_token()}"}
            resp = await client.request(method, url, headers=headers, **kwargs)
            resp.raise_for_status()
            return resp.json()

    async def _get_token(self) -> str:
        return f"simulated_token_{uuid.uuid4().hex}"

    async def sync_user_create(
        self, db: AsyncSession, user_id: str, actor_id: str | None = None
    ) -> dict:
        user = await db.execute(select(User).where(User.id == user_id))
        user = user.scalar_one_or_none()
        if not user:
            return {
                "user_id": user_id,
                "synced": False,
                "sync_status": "failed",
                "error": "User not found",
            }

        result = await self._call_api("POST", f"/users/{user_id}")
        user.entra_object_id = f"entra_{user_id}"
        await db.commit()

        await log_action(
            db,
            action="entraid_sync_create",
            actor_id=actor_id,
            target_type="user",
            target_id=user_id,
            payload={"username": user.username, "email": user.email},
            result="success",
        )
        return {
            "user_id": user_id,
            "synced": True,
            "sync_status": "synced",
            "synced_at": datetime.now(UTC),
            "details": result,
        }

    async def sync_user_update(
        self, db: AsyncSession, user_id: str, actor_id: str | None = None
    ) -> dict:
        user = await db.execute(select(User).where(User.id == user_id))
        user = user.scalar_one_or_none()
        if not user:
            return {
                "user_id": user_id,
                "synced": False,
                "sync_status": "failed",
                "error": "User not found",
            }

        result = await self._call_api("PATCH", f"/users/{user_id}")
        await log_action(
            db,
            action="entraid_sync_update",
            actor_id=actor_id,
            target_type="user",
            target_id=user_id,
            payload={"username": user.username, "status": user.status},
            result="success",
        )
        return {
            "user_id": user_id,
            "synced": True,
            "sync_status": "synced",
            "details": result,
        }

    async def sync_user_disable(
        self, db: AsyncSession, user_id: str, actor_id: str | None = None
    ) -> dict:
        result = await self._call_api("PATCH", f"/users/{user_id}/disable")
        await log_action(
            db,
            action="entraid_sync_disable",
            actor_id=actor_id,
            target_type="user",
            target_id=user_id,
            result="success",
        )
        return {
            "user_id": user_id,
            "synced": True,
            "sync_status": "synced",
            "details": result,
        }

    async def sync_user_delete(
        self, db: AsyncSession, user_id: str, actor_id: str | None = None
    ) -> dict:
        result = await self._call_api("DELETE", f"/users/{user_id}")
        await log_action(
            db,
            action="entraid_sync_delete",
            actor_id=actor_id,
            target_type="user",
            target_id=user_id,
            result="success",
        )
        return {
            "user_id": user_id,
            "synced": True,
            "sync_status": "deleted",
            "details": result,
        }

    async def get_sync_status(self, db: AsyncSession, user_id: str) -> dict:
        user = await db.execute(select(User).where(User.id == user_id))
        user = user.scalar_one_or_none()
        if not user:
            return {"user_id": user_id, "sync_status": "unknown", "errors": ["User not found"]}

        return {
            "user_id": user_id,
            "entra_object_id": user.entra_object_id,
            "sync_status": "synced" if user.entra_object_id else "pending",
            "last_synced_at": user.updated_at,
            "errors": [],
        }
