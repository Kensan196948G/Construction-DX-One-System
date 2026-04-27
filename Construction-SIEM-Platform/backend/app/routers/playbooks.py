from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.playbook import (
    PlaybookExecuteRequest,
    PlaybookExecutionResult,
    PlaybookLogRead,
    PlaybookRead,
)
from app.services.playbook_service import (
    execute_playbook,
    get_available_playbooks,
    get_execution_logs,
    get_playbook,
)

router = APIRouter(prefix="/playbooks", tags=["playbooks"])


@router.get("", response_model=list[PlaybookRead])
async def list_playbooks():
    return [PlaybookRead(**p) for p in get_available_playbooks()]


@router.get("/{playbook_id}", response_model=PlaybookRead)
async def get_playbook_detail(playbook_id: str):
    pb = get_playbook(playbook_id)
    if not pb:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return PlaybookRead(**pb)


@router.post("/{playbook_id}/execute", response_model=PlaybookExecutionResult)
async def execute_playbook_endpoint(
    playbook_id: str,
    payload: PlaybookExecuteRequest,
    db: AsyncSession = Depends(get_db),
):
    if payload.playbook_id != playbook_id:
        raise HTTPException(status_code=400, detail="Playbook ID mismatch")
    pb = get_playbook(playbook_id)
    if not pb:
        raise HTTPException(status_code=404, detail="Playbook not found")
    result = await execute_playbook(playbook_id, payload.event_data, db)
    return PlaybookExecutionResult(**result)


@router.get("/logs", response_model=list[PlaybookLogRead])
async def list_playbook_logs(limit: int = Query(50, ge=1, le=200)):
    logs = get_execution_logs(limit)
    return [PlaybookLogRead(**log) for log in logs]
