
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.merchant import Merchant

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)


async def get_token_from_request(request: Request, bearer_token: str | None = Depends(oauth2_scheme)) -> str | None:
    """
    Extract token from Authorization header (Bearer) or HTTP-only cookie.
    """
    if bearer_token:
        return bearer_token
    cookie_token = request.cookies.get(settings.COOKIE_NAME)
    if cookie_token:
        return cookie_token
    return None


async def get_current_merchant(
    token: str | None = Depends(get_token_from_request),
    db: AsyncSession = Depends(get_db),
) -> Merchant:
    """
    Validate session/JWT and return the authenticated merchant.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    merchant_id: str | None = payload.get("sub")
    if not merchant_id:
        raise credentials_exception

    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalar_one_or_none()

    if not merchant:
        raise credentials_exception

    if not merchant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Merchant account is disabled",
        )

    return merchant


async def get_current_verified_merchant(
    current_merchant: Merchant = Depends(get_current_merchant),
) -> Merchant:
    """
    Enforce that the merchant has a VERIFIED Razorpay verification status.
    """
    if current_merchant.verification_status != "VERIFIED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Merchant verification is not complete. Access denied.",
                "verification_status": current_merchant.verification_status,
                "razorpay_connection_status": current_merchant.razorpay_connection_status,
                "redirect_url": "/verification-pending",
            },
        )
    return current_merchant


async def get_current_admin(
    current_merchant: Merchant = Depends(get_current_merchant),
) -> Merchant:
    """
    Enforce that the current user has the 'admin' role.
    """
    if current_merchant.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required",
        )
    return current_merchant
