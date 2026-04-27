import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.schemas.entraid import BulkSyncResult, EntraIDSyncStatus, EntraIDUserSync
from app.services.entraid_service import EntraIDSync
from app.services.user_service import get_user_by_id

router = APIRouter(prefix="/external/entraid", tags=["entraid"])
bearer_scheme = HTTPBearer()


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> str:
    data = decode_token(credentials.credentials)
    sub = data.get("sub")
    if not sub or data.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return sub


@router.post("/sync/user/{user_id}", response_model=EntraIDUserSync)
async def sync_user(
    user_id: uuid.UUID,
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    sync = EntraIDSync()
    result = await sync.sync_user_create(db, str(user_id), actor_id=_user_id)
    if not result["synced"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("error"))
    return EntraIDUserSync(**result)


@router.get("/status/{user_id}", response_model=EntraIDSyncStatus)
async def sync_status(
    user_id: uuid.UUID,
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    sync = EntraIDSync()
    result = await sync.get_sync_status(db, str(user_id))
    return EntraIDSyncStatus(**result)


@router.post("/sync/bulk", response_model=BulkSyncResult)
async def bulk_sync(
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User))
    users = list(result.scalars().all())
    sync = EntraIDSync()
    results: list[dict] = []
    for user in users:
        r = await sync.sync_user_create(db, str(user.id), actor_id=_user_id)
        results.append(r)
    succeeded = sum(1 for r in results if r.get("synced"))
    failed = sum(1 for r in results if not r.get("synced"))
    return BulkSyncResult(
        total=len(users),
        succeeded=succeeded,
        failed=failed,
        results=[EntraIDUserSync(**r) for r in results],
    )


@router.get("/status", response_model=list[EntraIDSyncStatus])
async def overall_sync_status(
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User))
    users = list(result.scalars().all())
    sync = EntraIDSync()
    statuses: list[EntraIDSyncStatus] = []
    for user in users:
        s = await sync.get_sync_status(db, str(user.id))
        statuses.append(EntraIDSyncStatus(**s))
    return statuses
