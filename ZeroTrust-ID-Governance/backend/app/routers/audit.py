from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import AuditLog
from app.schemas.audit import AuditLogRead, ChainStats, ChainVerificationResult
from app.services.audit_service import get_audit_logs, get_chain_stats, verify_chain, verify_entry

router = APIRouter(prefix="/audit", tags=["audit"])
bearer_scheme = HTTPBearer()


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> str:
    data = decode_token(credentials.credentials)
    sub = data.get("sub")
    if not sub or data.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return sub


@router.get("/logs", response_model=list[AuditLogRead])
async def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    action: str | None = Query(None),
    actor: str | None = Query(None),
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    logs = await get_audit_logs(
        db, skip=skip, limit=limit, action_filter=action, actor_filter=actor
    )
    return [AuditLogRead.model_validate(log) for log in logs]


@router.get("/logs/{log_id}", response_model=AuditLogRead)
async def get_audit_log(
    log_id: int,
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AuditLog).where(AuditLog.id == log_id))
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit log not found")
    return AuditLogRead.model_validate(log)


@router.get("/verify/chain", response_model=ChainVerificationResult)
async def verify_chain_endpoint(
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await verify_chain(db)
    return ChainVerificationResult(**result)


@router.get("/verify/{log_id}")
async def verify_entry_endpoint(
    log_id: int,
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await verify_entry(db, log_id)


@router.get("/stats", response_model=ChainStats)
async def chain_stats_endpoint(
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    stats = await get_chain_stats(db)
    return ChainStats(**stats)
