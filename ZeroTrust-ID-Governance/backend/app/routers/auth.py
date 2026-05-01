from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from app.services.audit_service import log_action
from app.services.session_service import session_manager
from app.services.user_service import authenticate_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    actor_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    user = await authenticate_user(db, payload.username, payload.password)
    if not user:
        await log_action(
            db, action="login_failed", actor_ip=actor_ip,
            payload={"username": payload.username}, result="failure",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user.last_login_at = datetime.now(UTC).replace(tzinfo=None)
    await db.commit()
    session_id = session_manager.create_session(str(user.id), ip=actor_ip, user_agent=user_agent)
    await log_action(
        db, action="login", actor_id=str(user.id), actor_ip=actor_ip,
        target_type="user", target_id=str(user.id), payload={"session_id": session_id},
        result="success",
    )
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ")
        data = decode_token(token)
        user_id = data.get("sub")
        if user_id:
            session_manager.invalidate_user_sessions(user_id)
            await log_action(
                db, action="logout", actor_id=user_id,
                actor_ip=request.client.host if request.client else None,
                target_type="user", target_id=user_id, result="success",
            )
    return None


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshRequest):
    data = decode_token(payload.refresh_token)
    if not data or data.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    subject = data.get("sub")
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return TokenResponse(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
    )
