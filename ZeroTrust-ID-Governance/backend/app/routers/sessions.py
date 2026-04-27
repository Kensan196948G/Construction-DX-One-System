from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.services.session_service import session_manager

router = APIRouter(prefix="/auth/sessions", tags=["sessions"])
bearer_scheme = HTTPBearer()


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> str:
    data = decode_token(credentials.credentials)
    sub = data.get("sub")
    if not sub or data.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return sub


@router.get("")
async def list_active_sessions(
    _user_id: str = Depends(get_current_user_id),
    _db: AsyncSession = Depends(get_db),
):
    sessions = session_manager.get_active_sessions(_user_id)
    return {"sessions": sessions, "total": len(sessions)}


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def invalidate_session(
    session_id: str,
    _user_id: str = Depends(get_current_user_id),
    _db: AsyncSession = Depends(get_db),
):
    session_manager.invalidate_session(session_id)
    return None


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def invalidate_all_sessions(
    _user_id: str = Depends(get_current_user_id),
    _db: AsyncSession = Depends(get_db),
):
    session_manager.invalidate_user_sessions(_user_id)
    return None
