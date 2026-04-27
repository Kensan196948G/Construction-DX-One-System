import uuid
from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.user import User
from app.services.audit_service import log_action


class SCIMClient:
    def __init__(self):
        settings = get_settings()
        self.base_url = settings.hengeone_base_url
        self.api_key = settings.hengeone_api_key
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
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/scim+json",
            }
            resp = await client.request(method, url, headers=headers, **kwargs)
            resp.raise_for_status()
            return resp.json()

    def _build_scim_user(self, user: User) -> dict:
        return {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": user.username,
            "name": {"formatted": user.display_name},
            "displayName": user.display_name,
            "emails": [{"value": user.email, "type": "work", "primary": True}],
            "active": user.status == "active",
            "externalId": str(user.id),
            "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User": {
                "employeeNumber": user.employee_id,
                "department": user.department or "",
            },
        }

    async def create_user(self, user: User) -> dict:
        payload = self._build_scim_user(user)
        return await self._call_api("POST", "/Users", json=payload)

    async def update_user(self, user: User) -> dict:
        payload = self._build_scim_user(user)
        return await self._call_api("PUT", f"/Users/{user.hengeone_user_id}", json=payload)

    async def disable_user(self, user_id: str) -> dict:
        payload = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [{"op": "replace", "value": {"active": False}}],
        }
        return await self._call_api("PATCH", f"/Users/{user_id}", json=payload)

    async def delete_user(self, user_id: str) -> dict:
        return await self._call_api("DELETE", f"/Users/{user_id}")

    async def get_user(self, user_id: str) -> dict:
        return await self._call_api("GET", f"/Users/{user_id}")

    async def list_users(self, filter: str = "") -> dict:
        path = f"/Users?filter={filter}" if filter else "/Users"
        return await self._call_api("GET", path)

    async def sync_groups(self, department_groups: list[dict]) -> dict:
        payload = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "members": department_groups,
        }
        return await self._call_api("POST", "/Groups", json=payload)

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

        result = await self.create_user(user)
        scim_id = result.get("id", f"scim_{uuid.uuid4().hex}")
        user.hengeone_user_id = scim_id
        await db.commit()

        await log_action(
            db,
            action="hengeone_sync_create",
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
            "scim_id": scim_id,
            "synced_at": datetime.now(UTC),
            "details": result,
        }

    async def sync_user_disable(
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
        scim_id = user.hengeone_user_id
        if not scim_id:
            return {
                "user_id": user_id,
                "synced": False,
                "sync_status": "failed",
                "error": "No SCIM ID - user not previously synced",
            }

        result = await self.disable_user(scim_id)
        await log_action(
            db,
            action="hengeone_sync_disable",
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
        user = await db.execute(select(User).where(User.id == user_id))
        user = user.scalar_one_or_none()
        if not user:
            return {
                "user_id": user_id,
                "synced": False,
                "sync_status": "failed",
                "error": "User not found",
            }
        scim_id = user.hengeone_user_id
        if not scim_id:
            return {
                "user_id": user_id,
                "synced": False,
                "sync_status": "failed",
                "error": "No SCIM ID - user not previously synced",
            }

        result = await self.delete_user(scim_id)
        await log_action(
            db,
            action="hengeone_sync_delete",
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
            "hengeone_user_id": user.hengeone_user_id,
            "sync_status": "synced" if user.hengeone_user_id else "pending",
            "last_synced_at": user.updated_at,
            "errors": [],
        }
