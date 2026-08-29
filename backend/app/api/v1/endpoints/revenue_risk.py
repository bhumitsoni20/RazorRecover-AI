from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models.revenue_risk import RevenueRisk
from app.models.transaction import Transaction
from app.models.customer import Customer
from app.schemas.revenue_risk import RevenueRiskItem
from app.schemas.common import APIResponse

router = APIRouter()


@router.get("", response_model=APIResponse[List[RevenueRiskItem]])
async def list_revenue_risks(db: AsyncSession = Depends(get_db)):
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
                created_at=risk.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            )
        )

    return APIResponse(success=True, data=items)
