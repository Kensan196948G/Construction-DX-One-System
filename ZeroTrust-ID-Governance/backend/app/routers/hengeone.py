import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.schemas.hengeone import SCIMGroupSync, SCIMSyncStatus, SCIMUserSync
from app.services.hengeone_service import SCIMClient
from app.services.user_service import get_user_by_id

router = APIRouter(prefix="/external/hengeone", tags=["hengeone"])
bearer_scheme = HTTPBearer()


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> str:
    data = decode_token(credentials.credentials)
    sub = data.get("sub")
    if not sub or data.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return sub


@router.post("/sync/user/{user_id}", response_model=SCIMUserSync)
async def sync_user(
    user_id: uuid.UUID,
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    client = SCIMClient()
    result = await client.sync_user_create(db, str(user_id), actor_id=_user_id)
    if not result["synced"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("error"))
    return SCIMUserSync(**result)


@router.get("/status/{user_id}", response_model=SCIMSyncStatus)
async def sync_status(
    user_id: uuid.UUID,
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    client = SCIMClient()
    result = await client.get_sync_status(db, str(user_id))
    return SCIMSyncStatus(**result)


@router.post("/sync/groups", response_model=SCIMGroupSync)
async def sync_groups(
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    from app.models.user import User

    result = await db.execute(
        select(User.department, User.id).where(User.department.isnot(None))
    )
    rows = result.all()
    departments: dict[str, list[str]] = {}
    for dept, uid in rows:
        departments.setdefault(dept, []).append(str(uid))

    client = SCIMClient()
    results: list[dict] = []
    for dept_name, member_ids in departments.items():
        group_payload = {
            "displayName": dept_name,
            "members": [{"value": mid} for mid in member_ids],
        }
        r = await client.sync_groups([group_payload])
        results.append({
            "group_name": dept_name,
            "synced": True,
            "members_synced": len(member_ids),
            "details": r,
        })

    succeeded = sum(1 for r in results if r["synced"])
    failed = sum(1 for r in results if not r["synced"])
    return SCIMGroupSync(
        total=len(results),
        succeeded=succeeded,
        failed=failed,
        results=results,
    )
