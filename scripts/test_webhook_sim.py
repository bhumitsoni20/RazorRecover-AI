import asyncio
import os
import sys

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.core.database import AsyncSessionLocal
from app.api.v1.endpoints.webhooks import simulate_demo_webhook, SimulateWebhookRequest


async def main():
    async with AsyncSessionLocal() as s:
        req = SimulateWebhookRequest(transaction_id="txn_high_value", event_type="payment_link.paid", amount=50000.0)
        try:
            res = await simulate_demo_webhook(req=req, db=s)
            print("SUCCESS:", res)
        except Exception as e:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
