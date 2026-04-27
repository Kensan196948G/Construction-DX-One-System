from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import InventoryCampaign, InventoryItem
from app.models.user import User
from app.schemas.inventory import (
    InventoryCampaignCreate,
    InventoryCampaignUpdate,
    InventoryItemUpdate,
)
from app.services.audit_service import log_action


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


async def create_campaign(
    db: AsyncSession, payload: InventoryCampaignCreate, created_by: str
) -> InventoryCampaign:
    campaign = InventoryCampaign(
        name=payload.name,
        description=payload.description,
        review_period_start=payload.review_period_start,
        review_period_end=payload.review_period_end,
        created_by=created_by,
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    await log_action(
        db, action="campaign_create", actor_id=created_by,
        target_type="inventory_campaign", target_id=campaign.id,
        payload={"name": campaign.name}, result="success",
    )
    return campaign


async def start_campaign(db: AsyncSession, campaign_id: str) -> InventoryCampaign | None:
    result = await db.execute(
        select(InventoryCampaign).where(InventoryCampaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        return None
    if campaign.status != "draft":
        return None

    users_result = await db.execute(
        select(User).where(User.status == "active")
    )
    active_users = list(users_result.scalars().all())

    now = _now()
    for user in active_users:
        last_login_days = None
        if user.last_login_at:
            last_login_days = (now.date() - user.last_login_at.date()).days

        risk_level = "low"
        if last_login_days is not None:
            if last_login_days > 180:
                risk_level = "high"
            elif last_login_days > 90:
                risk_level = "medium"

        item = InventoryItem(
            campaign_id=campaign.id,
            user_id=str(user.id),
            last_login_days=last_login_days,
            risk_level=risk_level,
        )
        db.add(item)

    campaign.status = "active"
    campaign.total_accounts = len(active_users)
    await db.commit()
    await db.refresh(campaign)
    await log_action(
        db, action="campaign_start", actor_id=campaign.created_by,
        target_type="inventory_campaign", target_id=campaign.id,
        payload={"total_accounts": len(active_users)}, result="success",
    )
    return campaign


async def get_campaign(db: AsyncSession, campaign_id: str) -> InventoryCampaign | None:
    result = await db.execute(
        select(InventoryCampaign).where(InventoryCampaign.id == campaign_id)
    )
    return result.scalar_one_or_none()


async def list_campaigns(
    db: AsyncSession, status_filter: str | None = None
) -> list[InventoryCampaign]:
    query = select(InventoryCampaign).order_by(InventoryCampaign.created_at.desc())
    if status_filter:
        query = query.where(InventoryCampaign.status == status_filter)
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_campaign(
    db: AsyncSession, campaign: InventoryCampaign, payload: InventoryCampaignUpdate
) -> InventoryCampaign:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(campaign, field, value)
    await db.commit()
    await db.refresh(campaign)
    await log_action(
        db, action="campaign_update", actor_id=campaign.created_by,
        target_type="inventory_campaign", target_id=campaign.id,
        payload=payload.model_dump(exclude_unset=True), result="success",
    )
    return campaign


async def get_campaign_items(
    db: AsyncSession, campaign_id: str, status_filter: str | None = None
) -> list[InventoryItem]:
    query = select(InventoryItem).where(
        InventoryItem.campaign_id == campaign_id
    )
    if status_filter:
        query = query.where(InventoryItem.status == status_filter)
    result = await db.execute(query)
    return list(result.scalars().all())


async def review_item(
    db: AsyncSession, item_id: str, payload: InventoryItemUpdate, reviewed_by: str
) -> InventoryItem | None:
    result = await db.execute(
        select(InventoryItem).where(InventoryItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        return None

    item.status = payload.status
    if payload.reviewer_notes is not None:
        item.reviewer_notes = payload.reviewer_notes
    if payload.risk_level is not None:
        item.risk_level = payload.risk_level
    item.reviewed_by = reviewed_by
    item.reviewed_at = _now()

    await db.commit()
    await db.refresh(item)

    campaign_result = await db.execute(
        select(InventoryCampaign).where(InventoryCampaign.id == item.campaign_id)
    )
    campaign = campaign_result.scalar_one()

    reviewed_result = await db.execute(
        select(func.count()).select_from(InventoryItem).where(
            InventoryItem.campaign_id == campaign.id,
            InventoryItem.status.in_(["confirmed", "flagged", "remediated"]),
        )
    )
    campaign.reviewed_count = reviewed_result.scalar_one()

    flagged_result = await db.execute(
        select(func.count()).select_from(InventoryItem).where(
            InventoryItem.campaign_id == campaign.id,
            InventoryItem.status == "flagged",
        )
    )
    campaign.flagged_count = flagged_result.scalar_one()
    await db.commit()

    return item


async def complete_campaign(db: AsyncSession, campaign_id: str) -> InventoryCampaign | None:
    result = await db.execute(
        select(InventoryCampaign).where(InventoryCampaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        return None
    if campaign.status != "active":
        return None

    campaign.status = "completed"
    campaign.completed_at = _now()
    await db.commit()
    await db.refresh(campaign)
    await log_action(
        db, action="campaign_complete", actor_id=campaign.created_by,
        target_type="inventory_campaign", target_id=campaign.id,
        payload={"total_accounts": campaign.total_accounts,
                 "reviewed": campaign.reviewed_count,
                 "flagged": campaign.flagged_count},
        result="success",
    )
    return campaign


async def cancel_campaign(db: AsyncSession, campaign_id: str) -> InventoryCampaign | None:
    result = await db.execute(
        select(InventoryCampaign).where(InventoryCampaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        return None
    if campaign.status in ("completed", "cancelled"):
        return None

    campaign.status = "cancelled"
    await db.commit()
    await db.refresh(campaign)
    await log_action(
        db, action="campaign_cancel", actor_id=campaign.created_by,
        target_type="inventory_campaign", target_id=campaign.id, result="success",
    )
    return campaign


async def get_campaign_summary(db: AsyncSession, campaign_id: str) -> dict | None:
    result = await db.execute(
        select(InventoryCampaign).where(InventoryCampaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        return None

    high_risk_result = await db.execute(
        select(func.count()).select_from(InventoryItem).where(
            InventoryItem.campaign_id == campaign_id,
            InventoryItem.risk_level == "high",
        )
    )
    high_risk_count = high_risk_result.scalar_one()

    total = campaign.total_accounts
    reviewed = campaign.reviewed_count
    completion_rate = (reviewed / total * 100) if total > 0 else 0.0

    return {
        "total": total,
        "reviewed": reviewed,
        "flagged": campaign.flagged_count,
        "completion_rate": round(completion_rate, 2),
        "high_risk_count": high_risk_count,
    }


async def identify_inactive_accounts(
    db: AsyncSession, days_threshold: int
) -> list[User]:
    cutoff = _now().date()
    result = await db.execute(
        select(User).where(
            User.status == "active",
            User.last_login_at.isnot(None),
        )
    )
    users = list(result.scalars().all())
    inactive = []
    for user in users:
        if user.last_login_at:
            days_since = (cutoff - user.last_login_at.date()).days
            if days_since >= days_threshold:
                inactive.append(user)
    return inactive
