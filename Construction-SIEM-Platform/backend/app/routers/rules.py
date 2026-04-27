from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.rule import DetectionRule
from app.schemas.rule import (
    RuleCreate,
    RuleListResponse,
    RuleResponse,
    RuleStatsCategory,
    RuleStatsSeverity,
    RuleStatsSummary,
    RuleTest,
    RuleTestResult,
    RuleToggleResponse,
    RuleUpdate,
)
from app.services.rule_engine import check_rule

router = APIRouter(prefix="/rules", tags=["rules"])


@router.post("", response_model=RuleResponse, status_code=201)
async def create_rule(payload: RuleCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(DetectionRule).where(DetectionRule.rule_id == payload.rule_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Rule ID already exists")
    rule = DetectionRule(**payload.model_dump())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return RuleResponse.model_validate(rule)


@router.get("", response_model=RuleListResponse)
async def list_rules(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    severity: str | None = None,
    category: str | None = None,
    rule_type: str | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(DetectionRule)
    count_query = select(func.count()).select_from(DetectionRule)

    if severity:
        query = query.where(DetectionRule.severity == severity)
        count_query = count_query.where(DetectionRule.severity == severity)
    if category:
        query = query.where(DetectionRule.category == category)
        count_query = count_query.where(DetectionRule.category == category)
    if rule_type:
        query = query.where(DetectionRule.rule_type == rule_type)
        count_query = count_query.where(DetectionRule.rule_type == rule_type)
    if is_active is not None:
        query = query.where(DetectionRule.is_active == is_active)
        count_query = count_query.where(DetectionRule.is_active == is_active)

    total = (await db.execute(count_query)).scalar_one()
    offset = (page - 1) * per_page
    result = await db.execute(
        query.order_by(DetectionRule.created_at.desc()).offset(offset).limit(per_page)
    )
    rules = result.scalars().all()

    return RuleListResponse(
        data=[RuleResponse.model_validate(r) for r in rules],
        meta={"page": page, "per_page": per_page, "total": total, "total_pages": (total + per_page - 1) // per_page},
    )


@router.get("/stats/summary", response_model=RuleStatsSummary)
async def rule_stats_summary(db: AsyncSession = Depends(get_db)):
    total_result = await db.execute(select(func.count()).select_from(DetectionRule))
    total_rules = total_result.scalar_one()

    active_result = await db.execute(
        select(func.count()).select_from(DetectionRule).where(DetectionRule.is_active)
    )
    active_rules = active_result.scalar_one()

    severity_result = await db.execute(
        select(DetectionRule.severity, func.count().label("count"))
        .group_by(DetectionRule.severity)
    )
    by_severity = [RuleStatsSeverity(severity=r[0], count=r[1]) for r in severity_result.all()]

    category_result = await db.execute(
        select(DetectionRule.category, func.count().label("count"))
        .group_by(DetectionRule.category)
    )
    by_category = [RuleStatsCategory(category=r[0], count=r[1]) for r in category_result.all()]

    return RuleStatsSummary(
        total_rules=total_rules,
        active_rules=active_rules,
        by_severity=by_severity,
        by_category=by_category,
    )


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(rule_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DetectionRule).where(DetectionRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return RuleResponse.model_validate(rule)


@router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(rule_id: str, payload: RuleUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DetectionRule).where(DetectionRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)
    rule.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(rule)
    return RuleResponse.model_validate(rule)


@router.delete("/{rule_id}", status_code=204)
async def delete_rule(rule_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DetectionRule).where(DetectionRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    await db.delete(rule)
    await db.commit()


@router.post("/{rule_id}/toggle", response_model=RuleToggleResponse)
async def toggle_rule_active(rule_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DetectionRule).where(DetectionRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule.is_active = not rule.is_active
    rule.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(rule)
    return RuleToggleResponse(data=RuleResponse.model_validate(rule))


@router.post("/test", response_model=RuleTestResult)
async def test_rule_endpoint(payload: RuleTest):
    matched = check_rule(payload.rule_content, payload.rule_type, payload.event_data)
    return RuleTestResult(matched=matched, details="Rule matched" if matched else "No match")
