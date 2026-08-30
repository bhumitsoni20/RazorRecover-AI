from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.audit import AuditLogItem
from app.schemas.common import APIResponse
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("", response_model=APIResponse[List[AuditLogItem]])
async def list_audit_logs(
    agent_name: Optional[str] = Query(None),
    transaction_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    items = await AuditService.list_audit_logs(
        db=db,
        agent_name=agent_name,
        transaction_id=transaction_id,
        limit=limit,
    )
    return APIResponse(success=True, data=items)


@router.get("/verify", response_model=APIResponse[Dict[str, Any]])
async def verify_audit_chain(db: AsyncSession = Depends(get_db)):
    """
    Cryptographically verifies the append-only hash chain of all audit events.
    """
    result = await AuditService.verify_audit_chain(db)
    return APIResponse(success=True, data=result)
