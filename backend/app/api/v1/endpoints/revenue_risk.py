from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models.revenue_risk import RevenueRisk
from app.models.transaction import Transaction
from app.models.customer import Customer
from app.schemas.revenue_risk import (
    RevenueRiskSummaryResponse,
    PaginatedTransactionRiskResponse,
    RevenueRiskItem,
)
from app.schemas.common import APIResponse
from app.services.revenue_risk import RevenueRiskService

router = APIRouter()


@router.get("", response_model=APIResponse[RevenueRiskSummaryResponse])
@router.get("/summary", response_model=APIResponse[RevenueRiskSummaryResponse])
async def get_revenue_risk_summary(db: AsyncSession = Depends(get_db)):
    """
    Primary Phase 4 Revenue at Risk Summary Endpoint.
    Returns aggregated revenue at risk, average loss probability, leakage sources, and active anomaly alerts.
    """
    summary = await RevenueRiskService.get_revenue_risk_summary(db)
    return APIResponse(success=True, data=summary)


@router.get("/transactions", response_model=APIResponse[PaginatedTransactionRiskResponse])
async def get_transaction_risks(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level: LOW, MEDIUM, HIGH, CRITICAL"),
    db: AsyncSession = Depends(get_db),
):
    """
    Transaction-level risk scoring endpoint.
    Exposes individual transaction loss probabilities, expected loss amounts, risk levels, and explainable reasons.
    """
    result = await RevenueRiskService.get_transaction_risks(
        db=db,
        page=page,
        limit=limit,
        risk_level_filter=risk_level,
    )
    return APIResponse(success=True, data=result)


@router.get("/items", response_model=APIResponse[List[RevenueRiskItem]])
async def list_legacy_revenue_risks(db: AsyncSession = Depends(get_db)):
    """
    Legacy items endpoint for backward compatibility with existing components.
    """
    query = (
        select(RevenueRisk, Transaction, Customer)
        .join(Transaction, Transaction.id == RevenueRisk.transaction_id)
        .join(Customer, Customer.id == Transaction.customer_id)
        .order_by(desc(RevenueRisk.created_at))
        .limit(50)
    )
    results = (await db.execute(query)).all()

    items: List[RevenueRiskItem] = []
    for risk, txn, cust in results:
        items.append(
            RevenueRiskItem(
                id=risk.id,
                transaction_id=risk.transaction_id,
                amount=txn.amount,
                currency=txn.currency,
                customer_name=cust.name,
                payment_method=txn.payment_method,
                risk_type=risk.risk_type,
                risk_score=risk.risk_score,
                detected_reason=risk.detected_reason,
                recovery_probability=risk.recovery_probability,
                expected_recovery=risk.expected_recovery,
                status=risk.status,
                created_at=risk.created_at.strftime("%Y-%m-%d %H:%M:%S") if risk.created_at else "",
            )
        )

    return APIResponse(success=True, data=items)
