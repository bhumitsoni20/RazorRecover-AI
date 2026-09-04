from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.auth import get_current_merchant
from app.models.merchant import Merchant
from app.schemas.auth import (
    ConnectRazorpayRequest,
    VerificationStatusResponse,
)
from app.schemas.common import APIResponse
from app.services.razorpay_verification_service import RazorpayMerchantVerificationService

router = APIRouter()


@router.post("/connect-razorpay", response_model=APIResponse[dict])
async def connect_razorpay(
    data: ConnectRazorpayRequest,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db),
):
    """
    Connect Razorpay Merchant Account to RazorRecover AI.
    Sets connection_status to CONNECTED and maintains verification_status as PENDING.
    """
    res = await RazorpayMerchantVerificationService.connect_merchant(
        db=db,
        merchant_id=current_merchant.id,
        razorpay_account_id=data.razorpay_account_id,
    )
    return APIResponse(
        success=True,
        data=res,
        message="Razorpay account connected successfully. Undergoing verification.",
    )


@router.get("/status", response_model=APIResponse[VerificationStatusResponse])
async def get_verification_status(
    current_merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db),
):
    """
    Get real-time verification and connection status for the authenticated merchant.
    """
    status_data = await RazorpayMerchantVerificationService.get_merchant_verification_status(
        db=db,
        merchant_id=current_merchant.id,
    )
    return APIResponse(
        success=True,
        data=VerificationStatusResponse(**status_data),
    )
