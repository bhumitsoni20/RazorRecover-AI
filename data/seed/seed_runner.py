import asyncio
import sys
import os
from datetime import datetime, timedelta
import uuid
from sqlalchemy import select, func

# Ensure workspace root and backend path are in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from app.core.database import AsyncSessionLocal, init_db, engine, Base
from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.transaction import Transaction
from app.models.revenue_risk import RevenueRisk
from app.models.recovery_action import RecoveryAction
from app.models.audit_log import AuditLog
from app.models.agent_run import AgentRun
from app.models.merchant_policy import MerchantPolicy
from data.synthetic.dataset_generator import SyntheticDataGenerator, CUSTOMER_NAMES


async def seed_database(sample_size: int = 250, reset: bool = True):
    print(f"Initializing database tables (reset={reset})...")
    async with engine.begin() as conn:
        if reset:
            import app.models  # noqa
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        else:
            await init_db()

    async with AsyncSessionLocal() as session:
        print("Creating demo merchant...")
        merchant = Merchant(
            id="mch_razorpay_demo",
            name="Fintech Merchant Global",
            currency="INR",
        )
        session.add(merchant)

        # Add Merchant Policies
        policies = [
            MerchantPolicy(
                id="pol_retry_limit",
                merchant_id="mch_razorpay_demo",
                policy_name="Max Autonomous Retry Limit",
                policy_type="retry_limit",
                configuration={"max_retries": 2, "backoff_minutes": 15},
                active=True,
            ),
            MerchantPolicy(
                id="pol_amount_threshold",
                merchant_id="mch_razorpay_demo",
                policy_name="Autonomous Action Amount Threshold",
                policy_type="amount_threshold",
                configuration={"max_amount": 25000.0, "requires_approval_above": True},
                active=True,
            ),
            MerchantPolicy(
                id="pol_payment_link_rule",
                merchant_id="mch_razorpay_demo",
                policy_name="Autonomous Payment Link Dispatch",
                policy_type="payment_link_rule",
                configuration={"allowed_reasons": ["upi_timeout", "bank_degraded", "gateway_timeout"], "expiry_hours": 24},
                active=True,
            ),
        ]
        session.add_all(policies)

        # Add Customers
        customer_map = {}
        for idx, (c_name, c_email) in enumerate(CUSTOMER_NAMES):
            cust = Customer(
                id=f"cust_{idx + 1:03d}",
                merchant_id="mch_razorpay_demo",
                name=c_name,
                email=c_email,
                phone=f"+9198765{idx:05d}",
                total_transactions=15,
                successful_transactions=13,
                failed_transactions=2,
                lifetime_value=54000.0 + idx * 8500.0,
            )
            session.add(cust)
            customer_map[c_email] = cust

        await session.flush()

        # =========================================================
        # Specification 21: Key Test Transactions
        # =========================================================

        # CASE 1: Primary Demo Transaction (₹4,999 failed UPI -> APPROVED)
        txn_case1 = Transaction(
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
            razorpay_payment_id="pay_demo_upi_4999",
            razorpay_order_id="order_demo_4999",
            created_at=datetime.utcnow() - timedelta(minutes=14),
        )
        session.add(txn_case1)

        risk_case1 = RevenueRisk(
            id="risk_demo_4999",
            transaction_id="txn_4999_upi",
            risk_type="payment_failure",
            risk_score=0.13,
            detected_reason="UPI PSP timeout / payment degradation",
            recovery_probability=0.87,
            expected_recovery=4349.13,
            status="detected",
            created_at=datetime.utcnow() - timedelta(minutes=14),
        )
        session.add(risk_case1)

        # CASE 2: High Value Transaction (₹50,000 -> HUMAN_APPROVAL_REQUIRED)
        txn_case2 = Transaction(
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
            created_at=datetime.utcnow() - timedelta(minutes=25),
        )
        session.add(txn_case2)

        risk_case2 = RevenueRisk(
            id="risk_demo_high_val",
            transaction_id="txn_high_value",
            risk_type="payment_failure",
            risk_score=0.25,
            detected_reason="High-value gateway timeout",
            recovery_probability=0.79,
            expected_recovery=39500.0,
            status="detected",
            created_at=datetime.utcnow() - timedelta(minutes=25),
        )
        session.add(risk_case2)

        action_case2 = RecoveryAction(
            id="act_demo_high_val",
            transaction_id="txn_high_value",
            action_type="payment_link",
            reason="High-value checkout failure ($50,000 > $25,000) requires human approval",
            confidence=0.88,
            policy_decision="HUMAN_APPROVAL_REQUIRED",
            status="pending",
            created_at=datetime.utcnow() - timedelta(minutes=24),
        )
        session.add(action_case2)

        # CASE 3: Retry Exceeded Transaction (attempt=3 -> BLOCKED)
        txn_case3 = Transaction(
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
            created_at=datetime.utcnow() - timedelta(minutes=45),
        )
        session.add(txn_case3)

        risk_case3 = RevenueRisk(
            id="risk_demo_retry_exceeded",
            transaction_id="txn_retry_exceeded",
            risk_type="payment_failure",
            risk_score=0.45,
            detected_reason="Max retries reached (3 of 2)",
            recovery_probability=0.35,
            expected_recovery=700.0,
            status="detected",
            created_at=datetime.utcnow() - timedelta(minutes=45),
        )
        session.add(risk_case3)

        action_case3 = RecoveryAction(
            id="act_demo_retry_exceeded",
            transaction_id="txn_retry_exceeded",
            action_type="retry",
            reason="Automated recovery blocked: Maximum retry limit (3 > 2) reached",
            confidence=0.92,
            policy_decision="BLOCKED",
            status="failed",
            created_at=datetime.utcnow() - timedelta(minutes=44),
        )
        session.add(action_case3)

        # CASE 4: Already Recovered Transaction (status='recovered')
        txn_case4 = Transaction(
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
            created_at=datetime.utcnow() - timedelta(hours=2),
            updated_at=datetime.utcnow() - timedelta(hours=1, minutes=45),
        )
        session.add(txn_case4)

        risk_case4 = RevenueRisk(
            id="risk_demo_already_recov",
            transaction_id="txn_already_recovered",
            risk_type="payment_failure",
            risk_score=0.10,
            detected_reason="Recovered via payment link",
            recovery_probability=0.92,
            expected_recovery=3219.08,
            status="resolved",
            created_at=datetime.utcnow() - timedelta(hours=2),
        )
        session.add(risk_case4)

        action_case4 = RecoveryAction(
            id="act_demo_already_recov",
            transaction_id="txn_already_recovered",
            action_type="payment_link",
            reason="Autonomous recovery via Razorpay Test Mode Payment Link",
            confidence=0.94,
            policy_decision="APPROVED",
            status="completed",
            amount_recovered=3499.0,
            external_reference="https://rzp.io/rzp/live_recov_sample",
            created_at=datetime.utcnow() - timedelta(hours=1, minutes=58),
            completed_at=datetime.utcnow() - timedelta(hours=1, minutes=45),
        )
        session.add(action_case4)

        # Generate Synthetic Transactions
        print(f"Generating {sample_size} synthetic transactions...")
        synthetic_records = SyntheticDataGenerator.generate_transactions(count=sample_size)

        for record in synthetic_records:
            # Match customer
            cust = customer_map.get(record["customer_email"])
            cust_id = cust.id if cust else "cust_001"
            rec_id = record["id"]

            txn = Transaction(
                id=rec_id,
                merchant_id="mch_razorpay_demo",
                customer_id=cust_id,
                amount=record["amount"],
                currency=record["currency"],
                payment_method=record["payment_method"],
                payment_gateway="razorpay",
                bank=record.get("bank", "HDFC"),
                status=record["status"],
                failure_reason=record.get("failure_reason"),
                attempt_number=record.get("attempt_number", 1),
                created_at=record["created_at"],
            )
            session.add(txn)

            if record["status"] in ["failed", "abandoned", "pending", "recovered"]:
                risk = RevenueRisk(
                    id=f"risk_{rec_id}",
                    transaction_id=rec_id,
                    risk_type="payment_failure" if record["status"] == "failed" else "checkout_dropoff",
                    risk_score=record.get("risk_score", 0.2),
                    detected_reason=f"{record['payment_method'].upper()} failure: {record.get('failure_reason', 'timeout')}",
                    recovery_probability=record.get("recovery_probability", 0.85),
                    expected_recovery=round(record["amount"] * record.get("recovery_probability", 0.85), 2),
                    status="resolved" if record["status"] == "recovered" else "detected",
                    created_at=record["created_at"],
                )
                session.add(risk)

                if record["status"] == "recovered":
                    action = RecoveryAction(
                        id=f"act_{rec_id}",
                        transaction_id=rec_id,
                        action_type="payment_link",
                        reason=f"Recovered via payment link for {record.get('failure_reason', 'timeout')}",
                        confidence=0.91,
                        policy_decision="APPROVED",
                        status="completed",
                        amount_recovered=record["amount"],
                        created_at=record["created_at"] + timedelta(minutes=2),
                        completed_at=record["created_at"] + timedelta(minutes=15),
                    )
                    session.add(action)

        # Initial hash chain
        now = datetime.utcnow()
        init_id = f"aud_genesis_{uuid.uuid4().hex[:8]}"
        init_prev = "0" * 64
        init_hash = AuditLog.calculate_hash(
            id_str=init_id,
            transaction_id="txn_4999_upi",
            agent_name="SystemInit",
            action="system_genesis_initialize",
            reasoning_summary="RazorRecover AI database initialized and hash chain sealed",
            policy_result="PASSED",
            previous_hash=init_prev,
            created_at_str=now.isoformat(),
        )
        session.add(AuditLog(
            id=init_id,
            transaction_id="txn_4999_upi",
            agent_name="SystemInit",
            actor="SystemInit",
            action="system_genesis_initialize",
            reasoning_summary="RazorRecover AI database initialized and hash chain sealed",
            policy_result="PASSED",
            previous_hash=init_prev,
            event_hash=init_hash,
            created_at=now,
        ))

        await session.commit()
        print(f"Successfully seeded database with {sample_size + 4} transactions, policies, and sealed genesis block.")
