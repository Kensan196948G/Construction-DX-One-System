import uuid
from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.user import User
from app.services.audit_service import log_action


class ADClient:
    def __init__(self):
        settings = get_settings()
        self.server = settings.ad_server
        self.port = settings.ad_port
        self.base_dn = settings.ad_base_dn
        self.bind_dn = settings.ad_bind_dn
        self.bind_password = settings.ad_bind_password
        self.simulated = not bool(self.server)

    def _build_ad_attrs(self, user: User) -> dict:
        return {
            "cn": user.display_name,
            "sAMAccountName": user.username,
            "mail": user.email,
            "department": user.department or "",
            "displayName": user.display_name,
            "userPrincipalName": user.email,
            "employeeID": user.employee_id,
            "givenName": user.display_name.split(" ")[0] if " " in user.display_name else user.display_name,
            "sn": user.display_name.split(" ")[-1] if " " in user.display_name else "",
        }

    async def _call_ldap(self, operation: str, dn: str, attrs: dict | None = None) -> dict:
        if self.simulated:
            return {
                "simulated": True,
                "operation": operation,
                "dn": dn,
                "status": "success",
                "timestamp": datetime.now(UTC).isoformat(),
            }
        async with httpx.AsyncClient() as client:
            url = f"ldaps://{self.server}:{self.port}"
            payload = {
                "operation": operation,
                "dn": dn,
                "attributes": attrs or {},
                "bind_dn": self.bind_dn,
            }
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()

    async def create_user(self, user: User) -> dict:
        dn = f"CN={user.display_name},{self.base_dn}"
        attrs = self._build_ad_attrs(user)
        return await self._call_ldap("add", dn, attrs)

    async def disable_user(self, username: str) -> dict:
        dn = f"CN={username},{self.base_dn}"
        return await self._call_ldap("modify", dn, {"userAccountControl": "514"})

    async def delete_user(self, username: str) -> dict:
        dn = f"CN={username},{self.base_dn}"
        return await self._call_ldap("delete", dn)

    async def update_user(self, username: str, attrs: dict) -> dict:
        dn = f"CN={username},{self.base_dn}"
        return await self._call_ldap("modify", dn, attrs)

    async def find_user(self, username: str) -> dict:
        dn = f"CN={username},{self.base_dn}"
        return await self._call_ldap("search", dn, {"filter": f"(sAMAccountName={username})"})

    async def list_ou_users(self, ou: str) -> list:
        ou_dn = f"OU={ou},{self.base_dn}"
        result = await self._call_ldap("search", ou_dn, {"scope": "onelevel"})
        if self.simulated:
            return []
        return result.get("entries", [])

    async def reset_password(self, username: str) -> dict:
        dn = f"CN={username},{self.base_dn}"
        return await self._call_ldap("modify", dn, {"password": "reset_required"})

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
        ad_id = f"ad_{uuid.uuid4().hex}"
        user.ad_object_id = ad_id
        await db.commit()

        await log_action(
            db,
            action="ad_sync_create",
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
            "ad_object_id": ad_id,
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

        result = await self.disable_user(user.username)
        await log_action(
            db,
            action="ad_sync_disable",
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

        result = await self.delete_user(user.username)
        await log_action(
            db,
            action="ad_sync_delete",
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
            "ad_object_id": user.ad_object_id,
            "sync_status": "synced" if user.ad_object_id else "pending",
            "last_synced_at": user.updated_at,
            "errors": [],
        }
