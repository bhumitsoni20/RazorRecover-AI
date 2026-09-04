from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.config import settings
from app.schemas.auth import DevVerifyRequest
from app.schemas.common import APIResponse
from app.services.razorpay_verification_service import RazorpayMerchantVerificationService

router = APIRouter()


@router.post("/merchants/{merchant_id}/verify", response_model=APIResponse[dict])
async def dev_verify_merchant(
    data: DevVerifyRequest,
    merchant_id: str = Path(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Development-only endpoint to simulate merchant verification status transitions.
    Strictly blocked in production environments.
    """
    if settings.ENVIRONMENT != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dev verification simulator is disabled outside development environment.",
        )

    target_status = data.get_status()
    target_reason = data.get_reason()

    result = await RazorpayMerchantVerificationService.handle_verification_update(
        db=db,
        merchant_id=merchant_id,
        new_status=target_status,
        reason=target_reason,
        actor="dev_admin",
    )

    return APIResponse(
        success=True,
        data=result,
        message=f"Merchant verification status updated to {target_status}",
    )

