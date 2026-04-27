from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.kpi import CABEfficiency, DashboardSummary, SLACompliance
from app.services import kpi_service as svc

router = APIRouter()


@router.get("/kpi/dashboard", response_model=DashboardSummary)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    return await svc.get_dashboard_summary(db)


@router.get("/kpi/metrics")
async def get_metrics(db: AsyncSession = Depends(get_db)):
    return await svc.calculate_kpi_metrics(db)


@router.get("/kpi/trends")
async def get_trends(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    return await svc.get_kpi_trend(db, days)


@router.get("/kpi/alerts")
async def get_alerts(db: AsyncSession = Depends(get_db)):
    return await svc.get_kpi_alerts(db)


@router.get("/kpi/sla", response_model=SLACompliance)
async def get_sla(db: AsyncSession = Depends(get_db)):
    return await svc.get_sla_compliance(db)


@router.get("/kpi/cab-efficiency", response_model=CABEfficiency)
async def get_cab_efficiency(db: AsyncSession = Depends(get_db)):
    return await svc.get_cab_efficiency_metrics(db)
