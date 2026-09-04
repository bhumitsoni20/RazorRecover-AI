import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.audit_log import AuditLog
from app.models.merchant import Merchant


class RazorpayMerchantVerificationService:
    """
    Clean abstraction service for Razorpay Merchant Connection & Verification lifecycle.
    Designed for seamless future plug-in of official Razorpay OAuth 2.0 & Partner Onboarding.
    """

    @classmethod
    async def connect_merchant(
        cls,
        db: AsyncSession,
        merchant_id: str,
        razorpay_account_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Connects a merchant's Razorpay account.
        In sandbox/demo mode, generates or associates a partner account ID.
        """
        result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
        merchant = result.scalar_one_or_none()
        if not merchant:
            raise ValueError(f"Merchant {merchant_id} not found")

        acc_id = razorpay_account_id or f"acc_rzp_{uuid.uuid4().hex[:10]}"
        merchant.razorpay_account_id = acc_id
        merchant.razorpay_connection_status = "CONNECTED"
        merchant.updated_at = datetime.now(timezone.utc)

        # Record audit log
        await cls._record_audit(
            db=db,
            merchant_id=str(merchant.id),
            action="merchant_razorpay_connected",
            reasoning_summary=f"Razorpay account {acc_id} connected successfully. Verification status: {merchant.verification_status}",
            input_data={"razorpay_account_id": acc_id},
            output_data={"connection_status": "CONNECTED", "verification_status": str(merchant.verification_status)},
            policy_result="CONNECTED",
            actor=str(merchant.email),
        )

        await db.commit()
        await db.refresh(merchant)

        logger.info(f"Merchant {merchant_id} connected Razorpay account {acc_id}")
        return {
            "merchant_id": str(merchant.id),
            "razorpay_account_id": merchant.razorpay_account_id,
            "razorpay_connection_status": str(merchant.razorpay_connection_status),
            "verification_status": str(merchant.verification_status),
        }

    @classmethod
    async def get_merchant_verification_status(
        cls,
        db: AsyncSession,
        merchant_id: str,
    ) -> dict[str, Any]:
        """
        Retrieve merchant's current verification and connection status.
        """
        result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
        merchant = result.scalar_one_or_none()
        if not merchant:
            raise ValueError(f"Merchant {merchant_id} not found")

        verification_status = str(merchant.verification_status)
        can_access = verification_status == "VERIFIED" and bool(merchant.is_active)

        messages = {
            "PENDING": "Your Razorpay account is currently under verification. Dashboard access will be enabled upon approval.",
            "VERIFIED": "Your Razorpay account is verified and active. Full autonomous recovery enabled.",
            "REJECTED": "Your Razorpay merchant verification was rejected. Please contact merchant support.",
            "SUSPENDED": "Your merchant account is temporarily suspended by compliance.",
        }

        return {
            "merchant_id": merchant.id,
            "business_name": merchant.business_name,
            "verification_status": verification_status,
            "razorpay_connection_status": merchant.razorpay_connection_status,
            "razorpay_account_id": merchant.razorpay_account_id,
            "can_access_dashboard": can_access,
            "message": messages.get(verification_status, "Status verification pending."),
        }

    @classmethod
    async def handle_verification_update(
        cls,
        db: AsyncSession,
        merchant_id: str,
        new_status: str,
        reason: str | None = None,
        actor: str = "system",
    ) -> dict[str, Any]:
        """
        Update merchant verification status and record an immutable cryptographic audit log entry.
        """
        result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
        merchant = result.scalar_one_or_none()
        if not merchant:
            raise ValueError(f"Merchant {merchant_id} not found")

        old_status = str(merchant.verification_status)
        merchant.verification_status = new_status
        merchant.updated_at = datetime.now(timezone.utc)

        reason_str = reason or f"Merchant verification status transition: {old_status} -> {new_status}"
        audit_summary = f"Merchant verification status changed: {old_status} -> {new_status}"
        if reason:
            audit_summary += f" ({reason})"

        # Record cryptographic audit log
        await cls._record_audit(
            db=db,
            merchant_id=merchant_id,
            action="merchant_verification_updated",
            reasoning_summary=audit_summary,
            input_data={"old_status": str(old_status), "new_status": new_status, "reason": reason_str},
            output_data={"verification_status": new_status, "updated_at": merchant.updated_at.isoformat()},
            policy_result=new_status,
            actor=actor,
        )

        await db.commit()
        await db.refresh(merchant)

        logger.info(f"Merchant {merchant_id} verification updated: {old_status} -> {new_status} by {actor}")
        return {
            "merchant_id": merchant.id,
            "old_status": old_status,
            "new_status": merchant.verification_status,
            "verification_status": merchant.verification_status,
            "reason": reason_str,
        }

    @classmethod
    async def _record_audit(
        cls,
        db: AsyncSession,
        merchant_id: str,
        action: str,
        reasoning_summary: str,
        input_data: dict[str, Any],
        output_data: dict[str, Any],
        policy_result: str,
        actor: str = "system",
    ) -> AuditLog:
        """
        Helper to append a cryptographically hashed audit log entry.
        """
        from app.services.audit_service import AuditService
        return await AuditService.record_event(
            db=db,
            agent_name="RazorpayMerchantVerificationService",
            action=action,
            reasoning_summary=reasoning_summary,
            input_data=input_data,
            output_data=output_data,
            policy_result=policy_result,
            actor=actor,
            merchant_id=merchant_id,
        )
