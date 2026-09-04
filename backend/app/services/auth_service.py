from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.core.security import create_access_token, hash_password, verify_password
from app.models.merchant import Merchant
from app.schemas.auth import LoginRequest, SignupRequest
from app.services.audit_service import AuditService


class AuthService:
    """
    Core authentication service handling merchant registration, secure login, and session tokens.
    """

    @classmethod
    async def signup(cls, db: AsyncSession, data: SignupRequest) -> tuple[Merchant, str, str]:
        """
        Register a new merchant account.
        Initial status: verification_status = PENDING, razorpay_connection_status = NOT_CONNECTED.
        """
        # 1. Check if email already exists
        existing_res = await db.execute(select(Merchant).where(Merchant.email == data.email.lower()))
        if existing_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A merchant account with this email address already exists",
            )

        # 2. Hash password securely
        pwd_hash = hash_password(data.password)

        # 3. Create merchant record
        merchant = Merchant(
            business_name=data.business_name.strip(),
            owner_name=data.owner_name.strip(),
            email=data.email.lower().strip(),
            password_hash=pwd_hash,
            role="merchant",
            currency="INR",
            razorpay_connection_status="NOT_CONNECTED",
            verification_status="PENDING",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db.add(merchant)
        await db.commit()
        await db.refresh(merchant)

        # 4. Record cryptographic audit log
        await AuditService.record_event(
            db=db,
            agent_name="AuthService",
            action="merchant_signup",
            reasoning_summary=f"New merchant account created: {merchant.business_name} ({merchant.email}). Status: PENDING.",
            input_data={"email": merchant.email, "business_name": merchant.business_name},
            output_data={"merchant_id": merchant.id, "verification_status": "PENDING"},
            policy_result="PENDING",
            actor=merchant.email,
            merchant_id=merchant.id,
        )

        # 5. Issue access token
        token = create_access_token(data={"sub": merchant.id, "email": merchant.email, "role": merchant.role})
        redirect_url = "/onboarding/razorpay"

        logger.info(f"Merchant signed up successfully: {merchant.id} ({merchant.email})")
        return merchant, token, redirect_url

    @classmethod
    async def login(cls, db: AsyncSession, data: LoginRequest) -> tuple[Merchant, str, str]:
        """
        Authenticate merchant credentials and issue session token.
        Always returns generic error on failure to prevent user enumeration.
        """
        generic_error = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

        result = await db.execute(select(Merchant).where(Merchant.email == data.email.lower().strip()))
        merchant = result.scalar_one_or_none()

        if not merchant:
            raise generic_error

        if not verify_password(data.password, merchant.password_hash):
            raise generic_error

        if not merchant.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Merchant account is disabled. Please contact support.",
            )

        # Update last login timestamp
        merchant.last_login = datetime.utcnow()
        await db.commit()
        await db.refresh(merchant)

        # Issue access token
        token = create_access_token(data={"sub": merchant.id, "email": merchant.email, "role": merchant.role})

        # Determine redirect URL based on verification status
        if merchant.verification_status == "VERIFIED":
            redirect_url = "/dashboard"
        elif merchant.razorpay_connection_status == "NOT_CONNECTED":
            redirect_url = "/onboarding/razorpay"
        else:
            redirect_url = "/verification-pending"

        logger.info(f"Merchant logged in: {merchant.id} ({merchant.email}) -> redirecting to {redirect_url}")
        return merchant, token, redirect_url
