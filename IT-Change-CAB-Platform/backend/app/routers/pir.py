from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.pir import (
    PIRCompleteReview,
    PIRCreate,
    PIRListResponse,
    PIRResponse,
    PIRSummary,
    PIRUpdate,
)
from app.services import pir_service

router = APIRouter()


@router.post("/pir", response_model=PIRResponse, status_code=201)
async def create_pir(payload: PIRCreate, db: AsyncSession = Depends(get_db)):
    existing = await pir_service.get_pir_by_rfc(db, payload.rfc_id)
    if existing:
        raise HTTPException(status_code=409, detail="PIR already exists for this RFC")
    pir = await pir_service.create_pir(db, payload.rfc_id)
    return PIRResponse.model_validate(pir)


@router.get("/pir", response_model=PIRListResponse)
async def list_pirs(
    status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    pirs = await pir_service.list_pirs(db, status_filter=status, skip=skip, limit=limit)
    return PIRListResponse(
        data=[PIRResponse.model_validate(p) for p in pirs],
        meta={"total": len(pirs)},
    )


@router.get("/pir/summary", response_model=PIRSummary)
async def get_pir_summary(db: AsyncSession = Depends(get_db)):
    summary = await pir_service.get_pir_summary(db)
    return PIRSummary(
        completion_rate=summary["completion_rate"],
        overdue_count=summary["overdue_count"],
        avg_review_time=summary["avg_review_time"],
        recent_pirs=[PIRResponse.model_validate(p) for p in summary["recent_pirs"]],
    )


@router.get("/pir/by-rfc/{rfc_id}", response_model=PIRResponse)
async def get_pir_by_rfc(rfc_id: str, db: AsyncSession = Depends(get_db)):
    pir = await pir_service.get_pir_by_rfc(db, rfc_id)
    if not pir:
        raise HTTPException(status_code=404, detail="PIR not found for this RFC")
    return PIRResponse.model_validate(pir)


@router.get("/pir/{pir_id}", response_model=PIRResponse)
async def get_pir(pir_id: str, db: AsyncSession = Depends(get_db)):
    pir = await pir_service.get_pir(db, pir_id)
    if not pir:
        raise HTTPException(status_code=404, detail="PIR not found")
    return PIRResponse.model_validate(pir)


@router.put("/pir/{pir_id}", response_model=PIRResponse)
async def update_pir(
    pir_id: str,
    payload: PIRUpdate,
    db: AsyncSession = Depends(get_db),
):
    pir = await pir_service.update_pir(db, pir_id, payload)
    if not pir:
        raise HTTPException(status_code=404, detail="PIR not found")
    return PIRResponse.model_validate(pir)


@router.post("/pir/{pir_id}/complete", response_model=PIRResponse)
async def complete_pir_review(
    pir_id: str,
    payload: PIRCompleteReview,
    db: AsyncSession = Depends(get_db),
):
    pir = await pir_service.get_pir(db, pir_id)
    if not pir:
        raise HTTPException(status_code=404, detail="PIR not found")
    if pir.review_status == "completed":
        raise HTTPException(status_code=409, detail="PIR review already completed")
    pir = await pir_service.complete_review(db, pir_id, payload.reviewer_id, payload)
    return PIRResponse.model_validate(pir)
