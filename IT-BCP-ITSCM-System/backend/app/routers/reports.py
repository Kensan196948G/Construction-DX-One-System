from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.report import BCPReadinessReport, ExecutiveSummary, IncidentReport, WeeklyKPIReport
from app.services import report_service

router = APIRouter()


@router.get("/reports/executive-summary", response_model=ExecutiveSummary)
async def get_executive_summary(db: AsyncSession = Depends(get_db)):
    data = await report_service.generate_executive_summary(db)
    return ExecutiveSummary(**data)


@router.get("/reports/incident/{incident_id}", response_model=IncidentReport)
async def get_incident_report(incident_id: str, db: AsyncSession = Depends(get_db)):
    data = await report_service.generate_incident_report(db, incident_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return IncidentReport(**data)


@router.get("/reports/weekly-kpi", response_model=WeeklyKPIReport)
async def get_weekly_kpi_report(db: AsyncSession = Depends(get_db)):
    data = await report_service.generate_weekly_kpi_report(db)
    return WeeklyKPIReport(**data)


@router.get("/reports/bcp-readiness", response_model=BCPReadinessReport)
async def get_bcp_readiness_report(db: AsyncSession = Depends(get_db)):
    data = await report_service.generate_bcp_readiness_report(db)
    return BCPReadinessReport(**data)
