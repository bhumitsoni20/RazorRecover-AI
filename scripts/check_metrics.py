import asyncio
import os
import sys

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.core.database import AsyncSessionLocal
from app.services.dashboard_service import DashboardService
from app.models.transaction import Transaction
from app.models.recovery_action import RecoveryAction
from sqlalchemy import select


async def main():
    async with AsyncSessionLocal() as s:
        res = await DashboardService.get_summary(s)
        print(f"Revenue at Risk: Rs. {res.metrics.revenue_at_risk:,.2f}")
        print(f"Recovered Revenue: Rs. {res.metrics.recovered_revenue:,.2f}")
        print(f"Total Transactions: {res.metrics.total_transactions_analyzed}")
        print(f"Recovery Rate: {res.metrics.recovery_rate}%")

        txns = await s.execute(select(Transaction).where(Transaction.id.in_(["txn_4999_upi", "txn_high_value"])))
        for t in txns.scalars().all():
            print(f"Transaction: {t.id}, Status: {t.status}, Amount: {t.amount}")

        actions = await s.execute(select(RecoveryAction).where(RecoveryAction.transaction_id.in_(["txn_4999_upi", "txn_high_value"])))
        for a in actions.scalars().all():
            print(f"Action for {a.transaction_id}: Status={a.status}, Amount Recovered={a.amount_recovered}, ExtRef={a.external_reference}")


if __name__ == "__main__":
    asyncio.run(main())
