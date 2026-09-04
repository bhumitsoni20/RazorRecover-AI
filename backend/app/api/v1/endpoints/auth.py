from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_merchant
from app.core.config import settings
from app.core.database import get_db
from app.models.merchant import Merchant
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    MerchantResponse,
    SignupRequest,
)
from app.schemas.common import APIResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/signup", response_model=APIResponse[AuthResponse], status_code=status.HTTP_201_CREATED)
async def signup(
    data: SignupRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new merchant account with verification_status = PENDING and razorpay_connection_status = NOT_CONNECTED.
    Sets secure session cookie and returns access token.
    """
    merchant, token, redirect_url = await AuthService.signup(db, data)

    # Set HTTP-only cookie for session security
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite=settings.COOKIE_SAMESITE,  # "none" in production for cross-origin HTTPS, "lax" in dev
        secure=settings.COOKIE_SECURE,
        path="/",
    )

    return APIResponse(
        success=True,
        data=AuthResponse(
            merchant=MerchantResponse.model_validate(merchant),
            access_token=token,
            token_type="bearer",
            redirect_url=redirect_url,
        ),
        message="Merchant registered successfully. Verification pending.",
    )


@router.post("/login", response_model=APIResponse[AuthResponse])
async def login(
    data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate merchant email and password.
    Returns session token and routes merchant based on verification_status.
    """
    merchant, token, redirect_url = await AuthService.login(db, data)

    # Set HTTP-only cookie
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        path="/",
    )

    return APIResponse(
        success=True,
        data=AuthResponse(
            merchant=MerchantResponse.model_validate(merchant),
            access_token=token,
            token_type="bearer",
            redirect_url=redirect_url,
        ),
        message="Logged in successfully",
    )


@router.post("/logout", response_model=APIResponse[dict])
async def logout(response: Response):
    """
    Log out merchant by clearing the session cookie.
    """
    response.delete_cookie(
        key=settings.COOKIE_NAME,
        path="/",
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
    )
    return APIResponse(success=True, data={"logged_out": True}, message="Successfully logged out")


@router.get("/me", response_model=APIResponse[MerchantResponse])
async def get_me(
    current_merchant: Merchant = Depends(get_current_merchant),
):
    """
    Retrieve authenticated merchant's profile and verification status.
    """
    return APIResponse(
        success=True,
        data=MerchantResponse.model_validate(current_merchant),
    )
