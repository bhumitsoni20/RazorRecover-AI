from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models.recovery_action import RecoveryAction
from app.models.transaction import Transaction
from app.models.customer import Customer
from app.schemas.recovery import (
    AnalyzeRequest,
    AnalyzeResponse,
    ExecuteRequest,
    ExecuteResponse,
    ApproveRequest,
    ApproveResponse,
    RecoveryActionItem,
)
from app.schemas.common import APIResponse
from app.services.recovery_service import RecoveryService

router = APIRouter()


@router.get("/actions", response_model=APIResponse[List[RecoveryActionItem]])
async def list_recovery_actions(
    status: Optional[str] = Query(None),
    policy_decision: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(RecoveryAction, Transaction, Customer)
        .join(Transaction, Transaction.id == RecoveryAction.transaction_id)
        .join(Customer, Customer.id == Transaction.customer_id)
    )

    if status and status != "all":
        query = query.where(RecoveryAction.status == status)
    if policy_decision and policy_decision != "all":
        query = query.where(RecoveryAction.policy_decision == policy_decision)

    query = query.order_by(desc(RecoveryAction.created_at)).limit(50)
    results = (await db.execute(query)).all()

    items: List[RecoveryActionItem] = []
    for action, txn, cust in results:
        items.append(
            RecoveryActionItem(
                id=action.id,
                transaction_id=action.transaction_id,
                customer_name=cust.name,
                amount=txn.amount,
                currency=txn.currency,
                action_type=action.action_type,
                reason=action.reason,
                confidence=action.confidence,
                policy_decision=action.policy_decision,
                status=action.status,
                amount_recovered=action.amount_recovered,
                external_reference=action.external_reference,
                created_at=action.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                completed_at=action.completed_at.strftime("%Y-%m-%d %H:%M:%S") if action.completed_at else None,
            )
        )

    return APIResponse(success=True, data=items)


@router.post("/analyze", response_model=APIResponse[AnalyzeResponse])
@router.post("/{transaction_id}/analyze", response_model=APIResponse[AnalyzeResponse])
async def analyze_transaction(
    transaction_id: Optional[str] = None,
    request: AnalyzeRequest = AnalyzeRequest(),
    db: AsyncSession = Depends(get_db),
):
    target_id = transaction_id or request.transaction_id or "txn_4999_upi"
    result = await RecoveryService.analyze_transaction(db=db, transaction_id=target_id)
    return APIResponse(success=True, data=result)


@router.post("/execute", response_model=APIResponse[ExecuteResponse])
@router.post("/{transaction_id}/execute", response_model=APIResponse[ExecuteResponse])
async def execute_recovery(
    transaction_id: Optional[str] = None,
    request: ExecuteRequest = ExecuteRequest(),
    db: AsyncSession = Depends(get_db),
):
    target_id = transaction_id or request.transaction_id or "txn_4999_upi"
    action_type = request.action_type or "payment_link"
    result = await RecoveryService.execute_recovery(
        db=db,
        transaction_id=target_id,
        action_type=action_type,
    )
    return APIResponse(success=True, data=result)


@router.post("/approve", response_model=APIResponse[ApproveResponse])
@router.post("/{transaction_id}/approve", response_model=APIResponse[ApproveResponse])
async def approve_recovery(
    transaction_id: Optional[str] = None,
    request: ApproveRequest = ApproveRequest(),
    db: AsyncSession = Depends(get_db),
):
    target_id = transaction_id or request.transaction_id or "txn_4999_upi"
    result = await RecoveryService.approve_action(
        db=db,
        transaction_id=target_id,
        approved=request.approved,
        approver_note=request.approver_note or "Approved by Merchant Admin",
    )
    return APIResponse(success=True, data=result)
