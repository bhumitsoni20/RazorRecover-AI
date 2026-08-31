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
from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.transaction import Transaction
from app.models.recovery_action import RecoveryAction
from app.models.revenue_risk import RevenueRisk
from app.models.audit_log import AuditLog
import app.models  # noqa


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Merchant
        mch = Merchant(id="mch_razorpay_demo", name="Fintech Merchant Global", currency="INR")
        session.add(mch)

        # 2. Customers
        cust1 = Customer(
            id="cust_001",
            merchant_id="mch_razorpay_demo",
            name="Aditya Verma",
            email="aditya.verma@example.com",
            phone="+919876543210",
            total_transactions=15,
            successful_transactions=13,
            failed_transactions=2,
            lifetime_value=54000.0,
        )
        cust2 = Customer(
            id="cust_002",
            merchant_id="mch_razorpay_demo",
            name="Priya Sharma",
            email="priya.sharma@example.com",
            phone="+919876543211",
            total_transactions=20,
            successful_transactions=18,
            failed_transactions=2,
            lifetime_value=120000.0,
        )
        cust3 = Customer(
            id="cust_003",
            merchant_id="mch_razorpay_demo",
            name="Rahul Nair",
            email="rahul.nair@example.com",
            phone="+919876543212",
            total_transactions=8,
            successful_transactions=4,
            failed_transactions=4,
            lifetime_value=15000.0,
        )
        cust4 = Customer(
            id="cust_004",
            merchant_id="mch_razorpay_demo",
            name="Sneha Patel",
            email="sneha.patel@example.com",
            phone="+919876543213",
            total_transactions=25,
            successful_transactions=24,
            failed_transactions=1,
            lifetime_value=95000.0,
        )
        session.add_all([cust1, cust2, cust3, cust4])

        # 3. Test Transactions
        # CASE 1: txn_4999_upi (₹4,999 failed UPI -> APPROVED)
        t1 = Transaction(
            id="txn_4999_upi",
            merchant_id="mch_razorpay_demo",
            customer_id="cust_001",
            amount=4999.0,
            currency="INR",
            payment_method="upi",
            payment_gateway="razorpay",
            bank="HDFC",
            status="failed",
            failure_reason="upi_timeout",
            attempt_number=1,
            created_at=datetime.utcnow() - timedelta(minutes=10),
        )

        # CASE 2: txn_high_value (₹50,000 -> HUMAN_APPROVAL_REQUIRED)
        t2 = Transaction(
            id="txn_high_value",
            merchant_id="mch_razorpay_demo",
            customer_id="cust_002",
            amount=50000.0,
            currency="INR",
            payment_method="card",
            payment_gateway="razorpay",
            bank="ICICI",
            status="failed",
            failure_reason="gateway_timeout",
            attempt_number=1,
            created_at=datetime.utcnow() - timedelta(minutes=20),
        )

        # CASE 3: txn_retry_exceeded (₹2,000, attempt=3 -> BLOCKED)
        t3 = Transaction(
            id="txn_retry_exceeded",
            merchant_id="mch_razorpay_demo",
            customer_id="cust_003",
            amount=2000.0,
            currency="INR",
            payment_method="upi",
            payment_gateway="razorpay",
            bank="SBI",
            status="failed",
            failure_reason="upi_timeout",
            attempt_number=3,
            created_at=datetime.utcnow() - timedelta(minutes=30),
        )

        # CASE 4: txn_already_recovered (₹3,499 -> RECOVERED)
        t4 = Transaction(
            id="txn_already_recovered",
            merchant_id="mch_razorpay_demo",
            customer_id="cust_004",
            amount=3499.0,
            currency="INR",
            payment_method="upi",
            payment_gateway="razorpay",
            bank="Axis",
            status="recovered",
            failure_reason="upi_timeout",
            attempt_number=1,
            created_at=datetime.utcnow() - timedelta(hours=1),
        )

        session.add_all([t1, t2, t3, t4])

        # Add an initial audit log entry
        now = datetime.utcnow()
        init_id = "aud_init_test"
        init_prev = "0" * 64
        init_hash = AuditLog.calculate_hash(
            id_str=init_id,
            transaction_id="txn_4999_upi",
            agent_name="SystemInit",
            action="system_initialize",
            reasoning_summary="Test database initialized",
            policy_result="PASSED",
            previous_hash=init_prev,
            created_at_str=now.isoformat(),
        )
        session.add(AuditLog(
            id=init_id,
            transaction_id="txn_4999_upi",
            agent_name="SystemInit",
            actor="SystemInit",
            action="system_initialize",
            reasoning_summary="Test database initialized",
            policy_result="PASSED",
            previous_hash=init_prev,
            event_hash=init_hash,
            created_at=now,
        ))

        await session.commit()

    yield


@pytest_asyncio.fixture
async def async_client():
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
