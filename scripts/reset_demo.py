import asyncio
import os
import sys

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.core.database import AsyncSessionLocal
from app.models.recovery_action import RecoveryAction
from app.models.transaction import Transaction
from sqlalchemy import delete, update


async def main():
    async with AsyncSessionLocal() as session:
        # Reset txn_4999_upi
        await session.execute(
            delete(RecoveryAction).where(RecoveryAction.transaction_id == "txn_4999_upi")
        )
        await session.execute(
            update(Transaction)
            .where(Transaction.id == "txn_4999_upi")
            .values(status="failed")
        )

        # Reset txn_high_value
        await session.execute(
            delete(RecoveryAction).where(RecoveryAction.transaction_id == "txn_high_value")
        )
        await session.execute(
            update(Transaction)
            .where(Transaction.id == "txn_high_value")
            .values(status="failed")
        )

        await session.commit()
    print("SUCCESS: Reset txn_4999_upi and txn_high_value to fresh failed test state.")


if __name__ == "__main__":
    asyncio.run(main())
