from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_verified_merchant
from app.core.database import get_db
from app.models.merchant import Merchant
from app.schemas.audit import AuditLogItem
from app.schemas.common import APIResponse
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("", response_model=APIResponse[list[AuditLogItem]])
async def list_audit_logs(
    agent_name: str | None = Query(None),
    transaction_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    current_merchant: Merchant = Depends(get_current_verified_merchant),
    db: AsyncSession = Depends(get_db),
):
    """
    List cryptographic audit logs strictly for the authenticated verified merchant.
    """
    items = await AuditService.list_audit_logs(
        db=db,
        merchant_id=current_merchant.id,
        agent_name=agent_name,
        transaction_id=transaction_id,
        limit=limit,
    )
    return APIResponse(success=True, data=items)


@router.get("/verify", response_model=APIResponse[dict[str, Any]])
async def verify_audit_chain(
    current_merchant: Merchant = Depends(get_current_verified_merchant),
    db: AsyncSession = Depends(get_db),
):
    """
    Cryptographically verifies the append-only hash chain of the merchant's audit trail.
    """
    result = await AuditService.verify_audit_chain(db=db, merchant_id=current_merchant.id)
    return APIResponse(success=True, data=result)
