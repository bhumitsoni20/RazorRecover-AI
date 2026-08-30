import asyncio
import sys
import os
from datetime import datetime, timedelta
import uuid
from sqlalchemy import select

# Ensure workspace root and backend path are in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from app.core.database import AsyncSessionLocal, init_db
from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.transaction import Transaction
from app.models.revenue_risk import RevenueRisk
from app.models.recovery_action import RecoveryAction
from app.models.audit_log import AuditLog
from app.models.agent_run import AgentRun
from app.models.merchant_policy import MerchantPolicy
from data.synthetic.dataset_generator import SyntheticDataGenerator, CUSTOMER_NAMES


async def seed_database(sample_size: int = 250):
    print(f"Initializing database tables...")
    await init_db()

    async with AsyncSessionLocal() as session:
        # Check if merchant already exists
        existing_mch = await session.execute(
            select(Merchant).where(Merchant.id == "mch_razorpay_demo")
        )
        if existing_mch.scalar_one_or_none():
            # Ensure key test transactions exist
            existing_t2 = await session.execute(select(Transaction).where(Transaction.id == "txn_high_value"))
            if not existing_t2.scalar_one_or_none():
                print("Seeding missing test cases (txn_high_value, txn_retry_exceeded, txn_already_recovered)...")
                session.add(Transaction(
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
                ))
                session.add(Transaction(
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
                ))
                session.add(Transaction(
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
                ))
                session.add(RecoveryAction(
                    id="act_already_recov_001",
                    transaction_id="txn_already_recovered",
                    action_type="payment_link",
                    reason="Recovered via Razorpay Test Mode Link",
                    confidence=0.91,
                    policy_decision="APPROVED",
                    status="completed",
                    amount_recovered=3499.0,
                    external_reference="https://rzp.io/i/test_already_recovered",
                    created_at=datetime.utcnow() - timedelta(hours=1, minutes=58),
                    completed_at=datetime.utcnow() - timedelta(hours=1, minutes=45),
                ))
                await session.commit()
                print("Test scenarios seeded.")
            else:
                print("Database already seeded with demo merchant and test scenarios.")
            return

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
            id="act_high_val_001",
            transaction_id="txn_high_value",
            action_type="payment_link",
            reason="High-value transaction exceeds ₹25,000 limit; routed to human review",
            confidence=0.88,
            policy_decision="HUMAN_APPROVAL_REQUIRED",
            status="pending",
            created_at=datetime.utcnow() - timedelta(minutes=23),
        )
        session.add(action_case2)

        # CASE 3: Retry Exceeded Transaction (₹2,000, attempt=3 -> BLOCKED)
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
            id="risk_demo_retry_exc",
            transaction_id="txn_retry_exceeded",
            risk_type="payment_failure",
            risk_score=0.85,
            detected_reason="Max retries exceeded (3 > 2)",
            recovery_probability=0.18,
            expected_recovery=360.0,
            status="detected",
            created_at=datetime.utcnow() - timedelta(minutes=45),
        )
        session.add(risk_case3)

        # CASE 4: Already Recovered Transaction (₹3,499 -> RECOVERED)
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

        action_case4 = RecoveryAction(
            id="act_already_recov_001",
            transaction_id="txn_already_recovered",
            action_type="payment_link",
            reason="Recovered via Razorpay Test Mode Link",
            confidence=0.91,
            policy_decision="APPROVED",
            status="completed",
            amount_recovered=3499.0,
            external_reference="https://rzp.io/i/test_already_recovered",
            created_at=datetime.utcnow() - timedelta(hours=1, minutes=58),
            completed_at=datetime.utcnow() - timedelta(hours=1, minutes=45),
        )
        session.add(action_case4)

        # Generate synthetic batch
        print(f"Generating {sample_size} synthetic transactions...")
        synthetic_txns = SyntheticDataGenerator.generate_transactions(count=sample_size)

        for item in synthetic_txns:
            cust = customer_map.get(item["customer_email"]) or list(customer_map.values())[0]
            txn = Transaction(
                id=item["id"],
                merchant_id="mch_razorpay_demo",
                customer_id=cust.id,
                amount=item["amount"],
                currency=item["currency"],
                payment_method=item["payment_method"],
                payment_gateway=item["payment_gateway"],
                bank=item["bank"],
                status=item["status"],
                failure_reason=item["failure_reason"],
                attempt_number=item["attempt_number"],
                created_at=item["created_at"],
            )
            session.add(txn)

            if item["status"] != "success":
                risk = RevenueRisk(
                    transaction_id=item["id"],
                    risk_type="payment_failure" if item["failure_reason"] != "checkout_abandonment" else "checkout_abandonment",
                    risk_score=item["risk_score"],
                    detected_reason=f"Payment failure: {item['failure_reason'] or 'timeout'}",
                    recovery_probability=item["recovery_probability"],
                    expected_recovery=item["expected_recovery"],
                    status="in_progress" if item["status"] == "pending" else ("recovered" if item["status"] == "recovered" else "detected"),
                    created_at=item["created_at"],
                )
                session.add(risk)

                if item["status"] in ["recovered", "pending"]:
                    action = RecoveryAction(
                        transaction_id=item["id"],
                        action_type="payment_link" if item["payment_method"] == "upi" else "reminder",
                        reason=f"Autonomous recovery for {item['failure_reason'] or 'failure'}",
                        confidence=0.91,
                        policy_decision="APPROVED" if item["amount"] <= 25000 else "HUMAN_APPROVAL_REQUIRED",
                        status="completed" if item["status"] == "recovered" else "pending",
                        amount_recovered=item["amount"] if item["status"] == "recovered" else 0.0,
                        created_at=item["created_at"] + timedelta(minutes=2),
                        completed_at=item["created_at"] + timedelta(minutes=15) if item["status"] == "recovered" else None,
                    )
                    session.add(action)

        # Initial Cryptographic Hash-Chained Audit Log
        now = datetime.utcnow()
        init_id = "aud_seed_001"
        init_prev_hash = "0" * 64
        init_hash = AuditLog.calculate_hash(
            id_str=init_id,
            transaction_id="txn_4999_upi",
            agent_name="RevenueDetectionAgent",
            action="detect_revenue_risk",
            reasoning_summary="Identified ₹4,999 UPI failed transaction with high recovery probability (87%).",
            policy_result="PASSED",
            previous_hash=init_prev_hash,
            created_at_str=now.isoformat(),
        )

        session.add(AuditLog(
            id=init_id,
            transaction_id="txn_4999_upi",
            agent_name="RevenueDetectionAgent",
            actor="RevenueDetectionAgent",
            action="detect_revenue_risk",
            reasoning_summary="Identified ₹4,999 UPI failed transaction with high recovery probability (87%).",
            policy_result="PASSED",
            previous_hash=init_prev_hash,
            event_hash=init_hash,
            created_at=now,
        ))

        session.add(AgentRun(
            transaction_id="txn_4999_upi",
            agent_name="RevenueDetectionAgent",
            status="success",
            latency_ms=42,
            input_data={"amount": 4999.0, "reason": "upi_timeout"},
            output_data={"risk_score": 0.13, "probability": 0.87},
        ))

        await session.commit()
        print(f"Successfully seeded database with 4 key test scenarios and {sample_size} transactions.")


if __name__ == "__main__":
    asyncio.run(seed_database(sample_size=200))
