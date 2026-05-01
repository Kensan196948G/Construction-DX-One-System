import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.bia import BIARevision, BusinessProcess
from app.schemas.bia import (
    BIADashboardSummary,
    BIARevisionCreate,
    BIARevisionListResponse,
    BIARevisionRead,
    BusinessProcessCreate,
    BusinessProcessListResponse,
    BusinessProcessRead,
    BusinessProcessUpdate,
)

router = APIRouter()


@router.post("/bia/processes", response_model=BusinessProcessRead, status_code=201)
async def create_business_process(payload: BusinessProcessCreate, db: AsyncSession = Depends(get_db)):
    process = BusinessProcess(
        id=str(uuid.uuid4()),
        process_name=payload.process_name,
        description=payload.description,
        department=payload.department,
        criticality=payload.criticality,
        rto_minutes=payload.rto_minutes,
        rpo_minutes=payload.rpo_minutes,
        recovery_priority=payload.recovery_priority,
        dependencies=payload.dependencies,
        peak_business_hours=payload.peak_business_hours,
        legal_requirement=payload.legal_requirement,
        financial_impact_per_hour=payload.financial_impact_per_hour,
        status=payload.status,
        last_reviewed_at=payload.last_reviewed_at,
    )
    db.add(process)
    await db.commit()
    await db.refresh(process)
    return BusinessProcessRead.model_validate(process)


@router.get("/bia/processes", response_model=BusinessProcessListResponse)
async def list_business_processes(
    criticality: str | None = Query(None),
    department: str | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(BusinessProcess).order_by(BusinessProcess.recovery_priority.asc(), BusinessProcess.process_name.asc())
    if criticality:
        query = query.where(BusinessProcess.criticality == criticality)
    if department:
        query = query.where(BusinessProcess.department == department)
    if status:
        query = query.where(BusinessProcess.status == status)

    result = await db.execute(query)
    processes = result.scalars().all()

    return BusinessProcessListResponse(
        data=[BusinessProcessRead.model_validate(p) for p in processes],
        meta={"total": len(processes)},
    )


@router.get("/bia/processes/{process_id}", response_model=BusinessProcessRead)
async def get_business_process(process_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BusinessProcess).where(BusinessProcess.id == process_id))
    process = result.scalar_one_or_none()
    if not process:
        raise HTTPException(status_code=404, detail="Business process not found")
    return BusinessProcessRead.model_validate(process)


@router.put("/bia/processes/{process_id}", response_model=BusinessProcessRead)
async def update_business_process(
    process_id: str,
    payload: BusinessProcessUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(BusinessProcess).where(BusinessProcess.id == process_id))
    process = result.scalar_one_or_none()
    if not process:
        raise HTTPException(status_code=404, detail="Business process not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(process, field, value)
    process.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(process)
    return BusinessProcessRead.model_validate(process)


@router.delete("/bia/processes/{process_id}", status_code=204)
async def delete_business_process(process_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BusinessProcess).where(BusinessProcess.id == process_id))
    process = result.scalar_one_or_none()
    if not process:
        raise HTTPException(status_code=404, detail="Business process not found")
    await db.delete(process)
    await db.commit()


@router.get("/bia/processes/stats/summary", response_model=BIADashboardSummary)
async def get_bia_summary(db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count(BusinessProcess.id)))).scalar() or 0

    critical = (
        await db.execute(
            select(func.count(BusinessProcess.id)).where(BusinessProcess.criticality == "critical")
        )
    ).scalar() or 0

    high = (
        await db.execute(
            select(func.count(BusinessProcess.id)).where(BusinessProcess.criticality == "high")
        )
    ).scalar() or 0

    dept_result = await db.execute(
        select(BusinessProcess.department, func.count(BusinessProcess.id))
        .where(BusinessProcess.department.isnot(None))
        .group_by(BusinessProcess.department)
    )
    by_department = {row[0]: row[1] for row in dept_result.all()}

    priority_result = await db.execute(
        select(BusinessProcess.recovery_priority, func.count(BusinessProcess.id))
        .group_by(BusinessProcess.recovery_priority)
        .order_by(BusinessProcess.recovery_priority)
    )
    by_priority = {str(row[0]): row[1] for row in priority_result.all()}

    return BIADashboardSummary(
        total_processes=total,
        critical_count=critical,
        high_count=high,
        by_department=by_department,
        by_priority=by_priority,
    )


@router.get("/bia/processes/{process_id}/dependencies", response_model=BusinessProcessListResponse)
async def get_process_dependencies(process_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BusinessProcess).where(BusinessProcess.id == process_id))
    process = result.scalar_one_or_none()
    if not process:
        raise HTTPException(status_code=404, detail="Business process not found")

    deps = process.dependencies or []
    if not deps:
        return BusinessProcessListResponse(data=[], meta={"process_id": process_id, "dependency_count": 0})

    stmt = select(BusinessProcess).where(BusinessProcess.process_name.in_(deps))
    result = await db.execute(stmt)
    related = result.scalars().all()

    return BusinessProcessListResponse(
        data=[BusinessProcessRead.model_validate(p) for p in related],
        meta={"process_id": process_id, "dependency_count": len(related)},
    )


@router.post("/bia/revisions", response_model=BIARevisionRead, status_code=201)
async def create_bia_revision(payload: BIARevisionCreate, db: AsyncSession = Depends(get_db)):
    revision = BIARevision(
        id=str(uuid.uuid4()),
        version=payload.version,
        reviewed_by=payload.reviewed_by,
        review_date=payload.review_date,
        changes_summary=payload.changes_summary,
        next_review_date=payload.next_review_date,
    )
    db.add(revision)
    await db.commit()
    await db.refresh(revision)
    return BIARevisionRead.model_validate(revision)


@router.get("/bia/revisions", response_model=BIARevisionListResponse)
async def list_bia_revisions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BIARevision).order_by(BIARevision.version.desc()))
    revisions = result.scalars().all()
    return BIARevisionListResponse(
        data=[BIARevisionRead.model_validate(r) for r in revisions],
        meta={"total": len(revisions)},
    )
