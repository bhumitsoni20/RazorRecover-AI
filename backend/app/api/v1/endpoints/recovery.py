from typing import List, Optional, Dict, Any
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
from app.integrations.razorpay_service import razorpay_service

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
        if status == "pending_approval":
            query = query.where(
                RecoveryAction.policy_decision == "HUMAN_APPROVAL_REQUIRED",
                RecoveryAction.status == "pending",
            )
        elif status == "automated":
            query = query.where(RecoveryAction.policy_decision == "APPROVED")
        elif status in ["recovered", "completed"]:
            query = query.where(RecoveryAction.status.in_(["completed", "recovered"]))
        else:
            query = query.where(RecoveryAction.status == status)

    if policy_decision and policy_decision != "all":
        query = query.where(RecoveryAction.policy_decision == policy_decision)

    query = query.order_by(desc(RecoveryAction.created_at)).limit(100)
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


@router.get("/{transaction_id}/status", response_model=APIResponse[Dict[str, Any]])
@router.get("/{transaction_id}", response_model=APIResponse[Dict[str, Any]])
async def get_recovery_status(
    transaction_id: str = Path(...),
    db: AsyncSession = Depends(get_db),
):
    result = await RecoveryService.get_recovery_status(db=db, transaction_id=transaction_id)
    return APIResponse(success=True, data=result)


@router.post("/analyze", response_model=APIResponse[AnalyzeResponse])
@router.post("/{transaction_id}/analyze", response_model=APIResponse[AnalyzeResponse])
async def analyze_transaction(
    transaction_id: Optional[str] = None,
    request: AnalyzeRequest = AnalyzeRequest(),
    db: AsyncSession = Depends(get_db),
):
    target_id = transaction_id or getattr(request, "transaction_id", None) or "txn_4999_upi"
    result = await RecoveryService.analyze_transaction(db=db, transaction_id=target_id)
    return APIResponse(success=True, data=result)


@router.post("/execute", response_model=APIResponse[ExecuteResponse])
@router.post("/{transaction_id}/execute", response_model=APIResponse[ExecuteResponse])
async def execute_recovery(
    transaction_id: Optional[str] = None,
    request: ExecuteRequest = ExecuteRequest(),
    db: AsyncSession = Depends(get_db),
):
    target_id = transaction_id or getattr(request, "transaction_id", None) or "txn_4999_upi"
    action_type = getattr(request, "action_type", None) or "payment_link"
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
    target_id = transaction_id or getattr(request, "transaction_id", None) or "txn_4999_upi"
    result = await RecoveryService.approve_action(
        db=db,
        transaction_id=target_id,
        approved=request.approved,
        approver_note=request.approver_note or "Approved by Merchant Admin",
    )
    return APIResponse(success=True, data=result)


@router.post("/{transaction_id}/create-order", response_model=APIResponse[Dict[str, Any]])
async def create_razorpay_order(
    transaction_id: str = Path(...),
    db: AsyncSession = Depends(get_db),
):
    txn_res = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    txn = txn_res.scalars().first()
    raw_amount = getattr(txn, "amount", None)
    amount: float = float(raw_amount) if raw_amount is not None else 4999.0
    raw_currency = getattr(txn, "currency", None)
    currency: str = str(raw_currency) if raw_currency else "INR"
    order = await razorpay_service.create_order(
        amount=amount,
        currency=currency,
        receipt=f"rcpt_{transaction_id}",
        notes={"transaction_id": transaction_id},
    )
    return APIResponse(
        success=True,
        data={
            "order_id": order.get("id"),
            "amount": int(amount * 100),
            "currency": currency,
            "key_id": razorpay_service.key_id,
        },
    )
