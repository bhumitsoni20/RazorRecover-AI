import os
import sys
from datetime import datetime, timedelta
import pytest
import pytest_asyncio

# Ensure backend root is on sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.core.database import engine, Base, AsyncSessionLocal
from app.core.config import settings
from app.core.security import hash_password
from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.transaction import Transaction
from app.models.recovery_action import RecoveryAction
from app.models.revenue_risk import RevenueRisk
@pytest_asyncio.fixture(scope="function", autouse=True)
async def reset_test_states():
    async with AsyncSessionLocal() as session:
        from sqlalchemy import update, delete
        from app.models.webhook_event import WebhookEvent
        
        # Delete test webhook events & test signups
        await session.execute(delete(WebhookEvent))
        await session.execute(delete(Merchant).where(~Merchant.id.in_(["mch_admin_global", "mch_razorpay_demo", "mch_demo_fashion"])))
        
        # Reset standard test merchants
        await session.execute(
            update(Merchant)
            .where(Merchant.id == "mch_razorpay_demo")
            .values(verification_status="VERIFIED", is_active=True)
        )
        await session.execute(
            update(Merchant)
            .where(Merchant.id == "mch_demo_fashion")
            .values(
                verification_status="PENDING",
                is_active=True,
                razorpay_account_id=None,
                razorpay_connection_status="NOT_CONNECTED",
            )
        )
        
        # Reset transactions and recovery actions
        await session.execute(
            update(Transaction)
            .where(Transaction.id.in_(["txn_4999_upi", "txn_high_value", "txn_retry_exceeded"]))
            .values(status="failed")
        )
        await session.execute(
            update(RecoveryAction)
            .where(RecoveryAction.transaction_id == "txn_high_value")
            .values(status="pending", policy_decision="HUMAN_APPROVAL_REQUIRED")
        )
        await session.execute(
            update(RecoveryAction)
            .where(RecoveryAction.transaction_id == "txn_4999_upi")
            .values(status="executed", policy_decision="APPROVED")
        )
        await session.commit()
    yield






@pytest_asyncio.fixture
async def unauthenticated_client():
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def async_client():
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    from app.core.security import create_access_token
    from app.core.config import settings
    token = create_access_token(
        data={"sub": "mch_razorpay_demo", "email": settings.DEMO_MERCHANT_1_EMAIL, "role": "merchant"}
    )
    cookies = {settings.COOKIE_NAME: token}
    headers = {"Authorization": f"Bearer {token}"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", cookies=cookies, headers=headers) as ac:
        yield ac


@pytest_asyncio.fixture
async def merchant2_client():
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    from app.core.security import create_access_token
    from app.core.config import settings
    token = create_access_token(
        data={"sub": "mch_demo_fashion", "email": settings.DEMO_MERCHANT_2_EMAIL, "role": "merchant"}
    )
    cookies = {settings.COOKIE_NAME: token}
    headers = {"Authorization": f"Bearer {token}"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", cookies=cookies, headers=headers) as ac:
        yield ac

