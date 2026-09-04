from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_verified_merchant
from app.core.database import get_db
from app.models.merchant import Merchant
from app.schemas.common import APIResponse
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/summary", response_model=APIResponse[DashboardSummaryResponse])
async def get_dashboard_summary(
    current_merchant: Merchant = Depends(get_current_verified_merchant),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve real-time revenue recovery metrics strictly isolated for the authenticated merchant.
    Requires verified Razorpay merchant status.
    """
    data = await DashboardService.get_summary(db=db, merchant_id=current_merchant.id)
    return APIResponse(success=True, data=data)
