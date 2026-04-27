from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.schemas.inventory import (
    CampaignSummary,
    InventoryCampaignCreate,
    InventoryCampaignRead,
    InventoryCampaignUpdate,
    InventoryItemRead,
    InventoryItemUpdate,
)
from app.schemas.user import UserResponse
from app.services.audit_service import log_action
from app.services.inventory_service import (
    cancel_campaign,
    complete_campaign,
    create_campaign,
    get_campaign,
    get_campaign_items,
    get_campaign_summary,
    identify_inactive_accounts,
    list_campaigns,
    review_item,
    start_campaign,
    update_campaign,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])
bearer_scheme = HTTPBearer()


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> str:
    data = decode_token(credentials.credentials)
    sub = data.get("sub")
    if not sub or data.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return sub


@router.post("/campaigns", response_model=InventoryCampaignRead, status_code=status.HTTP_201_CREATED)
async def create_campaign_endpoint(
    payload: InventoryCampaignCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    campaign = await create_campaign(db, payload, user_id)
    return InventoryCampaignRead.model_validate(campaign)


@router.get("/campaigns", response_model=list[InventoryCampaignRead])
async def list_campaigns_endpoint(
    status: str | None = Query(None),
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    campaigns = await list_campaigns(db, status_filter=status)
    return [InventoryCampaignRead.model_validate(c) for c in campaigns]


@router.get("/campaigns/{campaign_id}", response_model=InventoryCampaignRead)
async def get_campaign_endpoint(
    campaign_id: str,
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    campaign = await get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return InventoryCampaignRead.model_validate(campaign)


@router.put("/campaigns/{campaign_id}", response_model=InventoryCampaignRead)
async def update_campaign_endpoint(
    campaign_id: str,
    payload: InventoryCampaignUpdate,
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    campaign = await get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    campaign = await update_campaign(db, campaign, payload)
    return InventoryCampaignRead.model_validate(campaign)


@router.post("/campaigns/{campaign_id}/start", response_model=InventoryCampaignRead)
async def start_campaign_endpoint(
    campaign_id: str,
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    campaign = await start_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign not found or not in draft status",
        )
    return InventoryCampaignRead.model_validate(campaign)


@router.post("/campaigns/{campaign_id}/complete", response_model=InventoryCampaignRead)
async def complete_campaign_endpoint(
    campaign_id: str,
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    campaign = await complete_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign not found or not in active status",
        )
    return InventoryCampaignRead.model_validate(campaign)


@router.post("/campaigns/{campaign_id}/cancel", response_model=InventoryCampaignRead)
async def cancel_campaign_endpoint(
    campaign_id: str,
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    campaign = await cancel_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign not found or already completed/cancelled",
        )
    return InventoryCampaignRead.model_validate(campaign)


@router.get("/campaigns/{campaign_id}/items", response_model=list[InventoryItemRead])
async def get_campaign_items_endpoint(
    campaign_id: str,
    status: str | None = Query(None),
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    campaign = await get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    items = await get_campaign_items(db, campaign_id, status_filter=status)
    return [InventoryItemRead.model_validate(i) for i in items]


@router.put(
    "/campaigns/{campaign_id}/items/{item_id}/review",
    response_model=InventoryItemRead,
)
async def review_item_endpoint(
    campaign_id: str,
    item_id: str,
    payload: InventoryItemUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    item = await review_item(db, item_id, payload, user_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    await log_action(
        db, action="inventory_item_review", actor_id=user_id,
        target_type="inventory_item", target_id=item_id,
        payload={"status": payload.status, "campaign_id": campaign_id},
        result="success",
    )
    return InventoryItemRead.model_validate(item)


@router.get("/campaigns/{campaign_id}/summary", response_model=CampaignSummary)
async def campaign_summary_endpoint(
    campaign_id: str,
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    summary = await get_campaign_summary(db, campaign_id)
    if not summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return CampaignSummary(**summary)


@router.get("/inactive-accounts", response_model=list[UserResponse])
async def inactive_accounts_endpoint(
    days: int = Query(90, ge=1),
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    users = await identify_inactive_accounts(db, days)
    return [UserResponse.model_validate(u) for u in users]
