import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.schemas.ad import ADBulkSyncResult, ADSyncStatus, ADUserSync
from app.services.ad_service import ADClient
from app.services.user_service import get_user_by_id

router = APIRouter(prefix="/external/ad", tags=["ad"])
bearer_scheme = HTTPBearer()


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> str:
    data = decode_token(credentials.credentials)
    sub = data.get("sub")
    if not sub or data.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return sub


@router.post("/sync/user/{user_id}", response_model=ADUserSync)
async def sync_user(
    user_id: uuid.UUID,
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    ad = ADClient()
    result = await ad.sync_user_create(db, str(user_id), actor_id=_user_id)
    if not result["synced"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("error"))
    return ADUserSync(**result)


@router.get("/status/{user_id}", response_model=ADSyncStatus)
async def sync_status(
    user_id: uuid.UUID,
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    ad = ADClient()
    result = await ad.get_sync_status(db, str(user_id))
    return ADSyncStatus(**result)


@router.post("/sync/bulk", response_model=ADBulkSyncResult)
async def bulk_sync(
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User))
    users = list(result.scalars().all())
    ad = ADClient()
    results: list[dict] = []
    for user in users:
        r = await ad.sync_user_create(db, str(user.id), actor_id=_user_id)
        results.append(r)
    succeeded = sum(1 for r in results if r.get("synced"))
    failed = sum(1 for r in results if not r.get("synced"))
    return ADBulkSyncResult(
        total=len(users),
        succeeded=succeeded,
        failed=failed,
        results=[ADUserSync(**r) for r in results],
    )
