import asyncio
import os
import sys
from datetime import datetime, timedelta

# Ensure backend path is on sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from sqlalchemy import select

import app.models  # noqa
from app.core.config import settings
from app.core.database import AsyncSessionLocal, Base, engine
from app.core.logging import logger
from app.core.security import hash_password
from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.merchant import Merchant
from app.models.recovery_action import RecoveryAction
from app.models.revenue_risk import RevenueRisk
from app.models.transaction import Transaction


async def seed_database():
    """
    Seeds the database with:
    - Initial Admin user
    - Demo Merchant 1 (Demo Electronics - VERIFIED)
    - Demo Merchant 2 (Demo Fashion Store - PENDING)
    - Isolated customers, transactions, and audit records for each merchant
    """
    logger.info("Starting database seeding...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Seed Admin
        admin_email = settings.INITIAL_ADMIN_EMAIL.lower()
        admin_res = await session.execute(select(Merchant).where(Merchant.email == admin_email))
        admin = admin_res.scalar_one_or_none()
        if not admin:
            admin = Merchant(
                id="mch_admin_global",
                business_name="RazorRecover Global Admin",
                owner_name="Platform Admin",
                email=admin_email,
                password_hash=hash_password(settings.INITIAL_ADMIN_PASSWORD),
                role="admin",
                currency="INR",
                razorpay_account_id="acc_admin_master",
                razorpay_connection_status="CONNECTED",
                verification_status="VERIFIED",
                is_active=True,
            )
            session.add(admin)
            logger.info(f"Created Admin account: {admin_email}")

        # 2. Seed Demo Merchant 1 (Demo Electronics - VERIFIED)
        m1_email = settings.DEMO_MERCHANT_1_EMAIL.lower()
        m1_res = await session.execute(select(Merchant).where(Merchant.email == m1_email))
        m1 = m1_res.scalar_one_or_none()
        if not m1:
            m1 = Merchant(
                id="mch_razorpay_demo",
                business_name="Demo Electronics",
                owner_name="Aditya Verma (Merchant)",
                email=m1_email,
                password_hash=hash_password(settings.DEMO_MERCHANT_1_PASSWORD),
                role="merchant",
                currency="INR",
                razorpay_account_id="acc_rzp_demo_electronics",
                razorpay_connection_status="CONNECTED",
                verification_status="VERIFIED",
                is_active=True,
            )
            session.add(m1)
            logger.info(f"Created Demo Merchant 1 (VERIFIED): {m1_email}")
        else:
            # Ensure password hash and status are up to date
            m1.verification_status = "VERIFIED"
            m1.password_hash = hash_password(settings.DEMO_MERCHANT_1_PASSWORD)

        # 3. Seed Demo Merchant 2 (Demo Fashion Store - PENDING)
        m2_email = settings.DEMO_MERCHANT_2_EMAIL.lower()
        m2_res = await session.execute(select(Merchant).where(Merchant.email == m2_email))
        m2 = m2_res.scalar_one_or_none()
        if not m2:
            m2 = Merchant(
                id="mch_demo_fashion",
                business_name="Demo Fashion Store",
                owner_name="Priya Sharma (Merchant)",
                email=m2_email,
                password_hash=hash_password(settings.DEMO_MERCHANT_2_PASSWORD),
                role="merchant",
                currency="INR",
                razorpay_account_id=None,
                razorpay_connection_status="NOT_CONNECTED",
                verification_status="PENDING",
                is_active=True,
            )
            session.add(m2)
            logger.info(f"Created Demo Merchant 2 (PENDING): {m2_email}")
        else:
            m2.verification_status = "PENDING"
            m2.password_hash = hash_password(settings.DEMO_MERCHANT_2_PASSWORD)

        await session.flush()

        # 4. Customers for Merchant 1 (Demo Electronics)
        customers_m1 = [
            ("cust_001", "Aditya Verma", "aditya.verma@example.com", "+919876543210", 18, 15, 3, 68000.0),
            ("cust_002", "Rohan Mehra", "rohan.mehra@example.com", "+919876543211", 24, 21, 3, 145000.0),
            ("cust_003", "Sneha Patel", "sneha.patel@example.com", "+919876543212", 28, 26, 2, 110000.0),
            ("cust_004", "Vikram Singh", "vikram.singh@example.com", "+919876543213", 12, 10, 2, 42000.0),
            ("cust_005", "Ananya Iyer", "ananya.iyer@example.com", "+919876543214", 16, 14, 2, 85000.0),
            ("cust_006", "Rahul Sharma", "rahul.sharma@example.com", "+919876543215", 8, 6, 2, 18500.0),
            ("cust_007", "Meera Kapoor", "meera.kapoor@example.com", "+919876543216", 20, 18, 2, 76000.0),
            ("cust_008", "Kiran Patel", "kiran.patel@example.com", "+919876543217", 15, 12, 3, 54000.0),
            ("cust_009", "Pooja Deshmukh", "pooja.deshmukh@example.com", "+919876543218", 32, 29, 3, 180000.0),
            ("cust_010", "Amitabh Sen", "amitabh.sen@example.com", "+919876543219", 11, 9, 2, 47500.0),
            ("cust_011", "Divya Nair", "divya.nair@example.com", "+919876543220", 22, 20, 2, 98000.0),
            ("cust_012", "Siddharth Joshi", "siddharth.joshi@example.com", "+919876543221", 5, 3, 2, 16200.0),
        ]

        for cid, cname, cemail, cphone, tot, succ, fail, ltv in customers_m1:
            c_res = await session.execute(select(Customer).where(Customer.id == cid))
            if not c_res.scalar_one_or_none():
                session.add(
                    Customer(
                        id=cid,
                        merchant_id=m1.id,
                        name=cname,
                        email=cemail,
                        phone=cphone,
                        total_transactions=tot,
                        successful_transactions=succ,
                        failed_transactions=fail,
                        lifetime_value=ltv,
                    )
                )

        # 5. Customers for Merchant 2 (Demo Fashion Store)
        customers_m2 = [
            ("cust_fashion_001", "Kavita Rao", "kavita.rao@example.com", "+919876543299", 7, 5, 2, 28500.0),
            ("cust_fashion_002", "Pooja Hegde", "pooja.hegde@example.com", "+919876543298", 10, 8, 2, 34000.0),
            ("cust_fashion_003", "Neha Gupta", "neha.gupta@example.com", "+919876543297", 14, 12, 2, 52000.0),
            ("cust_fashion_004", "Rajesh Khanna", "rajesh.khanna@example.com", "+919876543296", 9, 7, 2, 41000.0),
            ("cust_fashion_005", "Ritu Chawla", "ritu.chawla@example.com", "+919876543295", 12, 10, 2, 38000.0),
            ("cust_fashion_006", "Varun Malhotra", "varun.malhotra@example.com", "+919876543294", 19, 16, 3, 67000.0),
            ("cust_fashion_007", "Tanvi Sethi", "tanvi.sethi@example.com", "+919876543293", 8, 7, 1, 21000.0),
            ("cust_fashion_008", "Arjun Singhal", "arjun.singhal@example.com", "+919876543292", 15, 13, 2, 49500.0),
        ]

        for cid, cname, cemail, cphone, tot, succ, fail, ltv in customers_m2:
            c_res = await session.execute(select(Customer).where(Customer.id == cid))
            if not c_res.scalar_one_or_none():
                session.add(
                    Customer(
                        id=cid,
                        merchant_id=m2.id,
                        name=cname,
                        email=cemail,
                        phone=cphone,
                        total_transactions=tot,
                        successful_transactions=succ,
                        failed_transactions=fail,
                        lifetime_value=ltv,
                    )
                )

        await session.flush()

        # 6. Transactions for Merchant 1 (Demo Electronics)
        now = datetime.utcnow()
        txns_m1 = [
            # ID, CustomerID, Amount, Method, Gateway, Bank, Status, Reason, Attempts, MinutesAgo
            ("txn_4999_upi", "cust_001", 4999.0, "upi", "razorpay", "HDFC", "failed", "upi_timeout", 1, 15),
            ("txn_merchant_a_001", "cust_001", 12500.0, "upi", "razorpay", "SBI", "failed", "bank_degraded", 1, 30),
            ("txn_8999_card", "cust_002", 8999.0, "card", "razorpay", "ICICI", "failed", "3ds_verification_failed", 1, 45),
            ("txn_1499_upi", "cust_003", 1499.0, "upi", "razorpay", "Axis", "failed", "upi_timeout", 1, 60),
            ("txn_24500_netbanking", "cust_004", 24500.0, "netbanking", "razorpay", "HDFC", "failed", "gateway_timeout", 1, 90),
            ("txn_high_value", "cust_002", 50000.0, "card", "razorpay", "ICICI", "failed", "gateway_timeout", 1, 120),
            ("txn_35000_card", "cust_005", 35000.0, "card", "razorpay", "SBI", "failed", "gateway_timeout", 1, 150),
            ("txn_750_wallet", "cust_006", 750.0, "wallet", "razorpay", "Paytm Bank", "failed", "insufficient_funds", 1, 180),
            ("txn_18200_upi", "cust_007", 18200.0, "upi", "razorpay", "Kotak", "failed", "upi_timeout", 1, 210),
            ("txn_retry_exceeded", "cust_003", 2000.0, "upi", "razorpay", "SBI", "failed", "upi_timeout", 3, 240),
            ("txn_6450_upi", "cust_004", 6450.0, "upi", "razorpay", "HDFC", "failed", "bank_degraded", 1, 300),
            ("txn_15000_card", "cust_001", 15000.0, "card", "razorpay", "Axis", "failed", "network_error", 1, 360),
            ("txn_demo_upi_01", "cust_008", 3299.0, "upi", "razorpay", "HDFC", "failed", "upi_timeout", 1, 10),
            ("txn_demo_card_02", "cust_009", 42500.0, "card", "razorpay", "ICICI", "failed", "gateway_timeout", 1, 20),
            ("txn_demo_upi_03", "cust_010", 1899.0, "upi", "razorpay", "SBI", "failed", "bank_degraded", 1, 35),
            ("txn_demo_netb_04", "cust_011", 62000.0, "netbanking", "razorpay", "Axis", "failed", "gateway_timeout", 1, 50),
            ("txn_demo_wallet_05", "cust_012", 999.0, "wallet", "razorpay", "Paytm", "failed", "insufficient_funds", 1, 65),
            ("txn_demo_card_06", "cust_008", 16499.0, "card", "razorpay", "Kotak", "failed", "3ds_verification_failed", 1, 80),
            ("txn_demo_upi_07", "cust_009", 7800.0, "upi", "razorpay", "HDFC", "failed", "upi_timeout", 1, 95),
            ("txn_demo_card_08", "cust_010", 28900.0, "card", "razorpay", "SBI", "failed", "network_error", 1, 110),
            ("txn_demo_upi_09", "cust_011", 2499.0, "upi", "razorpay", "ICICI", "failed", "bank_degraded", 1, 130),
            ("txn_demo_netb_10", "cust_009", 75000.0, "netbanking", "razorpay", "HDFC", "failed", "gateway_timeout", 1, 160),
            ("txn_demo_card_11", "cust_008", 9500.0, "card", "razorpay", "Axis", "failed", "card_expired", 1, 190),
            ("txn_demo_upi_12", "cust_012", 3999.0, "upi", "razorpay", "SBI", "failed", "upi_timeout", 2, 220),
            ("txn_demo_sub_13", "cust_010", 1299.0, "subscription", "razorpay", "ICICI", "failed", "insufficient_funds", 1, 250),
            ("txn_demo_upi_14", "cust_008", 5499.0, "upi", "razorpay", "Kotak", "failed", "bank_degraded", 1, 280),
            ("txn_demo_card_15", "cust_011", 19999.0, "card", "razorpay", "HDFC", "failed", "3ds_verification_failed", 1, 320),
            ("txn_demo_netb_16", "cust_009", 112000.0, "netbanking", "razorpay", "ICICI", "failed", "gateway_timeout", 1, 380),
            ("txn_already_recovered", "cust_003", 3499.0, "upi", "razorpay", "Axis", "recovered", "upi_timeout", 1, 400),
            ("txn_recovered_card", "cust_002", 9200.0, "card", "razorpay", "HDFC", "recovered", "3ds_verification_failed", 1, 460),
            ("txn_recovered_upi_2", "cust_007", 1999.0, "upi", "razorpay", "SBI", "recovered", "upi_timeout", 1, 520),
            ("txn_demo_recov_17", "cust_010", 8499.0, "card", "razorpay", "SBI", "recovered", "3ds_verification_failed", 1, 410),
            ("txn_demo_recov_18", "cust_011", 4999.0, "upi", "razorpay", "HDFC", "recovered", "upi_timeout", 1, 440),
            ("txn_demo_recov_19", "cust_008", 13500.0, "upi", "razorpay", "Axis", "recovered", "bank_degraded", 1, 480),
            ("txn_demo_recov_20", "cust_012", 2199.0, "wallet", "razorpay", "Paytm", "recovered", "insufficient_funds", 1, 510),
        ]

        for tid, tcust, tamt, tmeth, tgate, tbank, tstat, treason, tatt, tmins in txns_m1:
            t_res = await session.execute(select(Transaction).where(Transaction.id == tid))
            existing_t = t_res.scalar_one_or_none()
            if not existing_t:
                session.add(
                    Transaction(
                        id=tid,
                        merchant_id=m1.id,
                        customer_id=tcust,
                        amount=tamt,
                        currency="INR",
                        payment_method=tmeth,
                        payment_gateway=tgate,
                        bank=tbank,
                        status=tstat,
                        failure_reason=treason,
                        attempt_number=tatt,
                        created_at=now - timedelta(minutes=tmins),
                    )
                )

        # 7. Transactions for Merchant 2 (Demo Fashion Store)
        txns_m2 = [
            ("txn_merchant_b_001", "cust_fashion_001", 2999.0, "card", "razorpay", "HDFC", "failed", "3ds_verification_failed", 1, 45),
            ("txn_fashion_4500", "cust_fashion_002", 4500.0, "upi", "razorpay", "ICICI", "failed", "upi_timeout", 1, 75),
            ("txn_fashion_1200", "cust_fashion_003", 1200.0, "upi", "razorpay", "SBI", "failed", "bank_degraded", 1, 105),
            ("txn_fashion_8999", "cust_fashion_004", 8999.0, "card", "razorpay", "Axis", "failed", "gateway_timeout", 1, 140),
            ("txn_fashion_28000", "cust_fashion_001", 28000.0, "card", "razorpay", "HDFC", "failed", "gateway_timeout", 1, 200),
            ("txn_fashion_1750", "cust_fashion_002", 1750.0, "upi", "razorpay", "Kotak", "failed", "upi_timeout", 1, 260),
            ("txn_fashion_3499", "cust_fashion_005", 3499.0, "upi", "razorpay", "HDFC", "failed", "upi_timeout", 1, 25),
            ("txn_fashion_14500", "cust_fashion_006", 14500.0, "card", "razorpay", "ICICI", "failed", "3ds_verification_failed", 1, 55),
            ("txn_fashion_799", "cust_fashion_007", 799.0, "wallet", "razorpay", "PhonePe", "failed", "insufficient_funds", 1, 85),
            ("txn_fashion_19999", "cust_fashion_008", 19999.0, "card", "razorpay", "Axis", "failed", "gateway_timeout", 1, 115),
            ("txn_fashion_2499", "cust_fashion_005", 2499.0, "upi", "razorpay", "SBI", "failed", "bank_degraded", 1, 155),
            ("txn_fashion_38500", "cust_fashion_006", 38500.0, "netbanking", "razorpay", "HDFC", "failed", "gateway_timeout", 1, 185),
            ("txn_fashion_5200", "cust_fashion_007", 5200.0, "card", "razorpay", "Kotak", "failed", "network_error", 1, 230),
            ("txn_fashion_1599", "cust_fashion_008", 1599.0, "upi", "razorpay", "Axis", "failed", "upi_timeout", 1, 275),
            ("txn_fashion_recovered_1", "cust_fashion_003", 3200.0, "upi", "razorpay", "ICICI", "recovered", "upi_timeout", 1, 350),
            ("txn_fashion_recovered_2", "cust_fashion_004", 6100.0, "card", "razorpay", "SBI", "recovered", "3ds_verification_failed", 1, 420),
            ("txn_fashion_recov_3", "cust_fashion_005", 4800.0, "upi", "razorpay", "ICICI", "recovered", "upi_timeout", 1, 310),
            ("txn_fashion_recov_4", "cust_fashion_006", 9500.0, "card", "razorpay", "SBI", "recovered", "3ds_verification_failed", 1, 380),
        ]

        for tid, tcust, tamt, tmeth, tgate, tbank, tstat, treason, tatt, tmins in txns_m2:
            t_res = await session.execute(select(Transaction).where(Transaction.id == tid))
            existing_t = t_res.scalar_one_or_none()
            if not existing_t:
                session.add(
                    Transaction(
                        id=tid,
                        merchant_id=m2.id,
                        customer_id=tcust,
                        amount=tamt,
                        currency="INR",
                        payment_method=tmeth,
                        payment_gateway=tgate,
                        bank=tbank,
                        status=tstat,
                        failure_reason=treason,
                        attempt_number=tatt,
                        created_at=now - timedelta(minutes=tmins),
                    )
                )

        await session.flush()

        # 8. Recovery Actions for Merchant 1 & Merchant 2
        recovery_actions_data = [
            # ID, TxnID, Type, Reason, Conf, PolicyDecision, Status, AmountRecovered, Ref, MinutesAgo
            # Merchant 1 - Autonomous Approved
            ("act_4999", "txn_4999_upi", "payment_link", "Transient UPI PSP timeout. Dispatched autonomous Razorpay smart payment link via WhatsApp and SMS.", 0.94, "APPROVED", "executed", 0.0, "plink_test_4999upi", 12),
            ("act_a001", "txn_merchant_a_001", "alternative_payment_method", "Bank-side UPI degradation detected on SBI gateway. Recommended NetBanking & Card options.", 0.91, "APPROVED", "executed", 0.0, "plink_test_a001", 25),
            ("act_8999", "txn_8999_card", "payment_link", "3DS verification failure on ICICI Card. Issued secure fallback checkout link.", 0.89, "APPROVED", "executed", 0.0, "plink_test_8999card", 40),
            ("act_1499", "txn_1499_upi", "payment_link", "Autonomous SMS recovery link dispatched.", 0.94, "APPROVED", "executed", 0.0, "plink_test_1499", 55),
            ("act_24500", "txn_24500_netbanking", "payment_link", "NetBanking checkout recovery link dispatched.", 0.90, "APPROVED", "executed", 0.0, "plink_test_24500", 85),
            ("act_18200", "txn_18200_upi", "payment_link", "Autonomous Razorpay UPI link dispatched.", 0.93, "APPROVED", "executed", 0.0, "plink_test_18200", 205),
            ("act_6450", "txn_6450_upi", "alternative_payment_method", "Recommended alternative payment method on degraded bank channel.", 0.91, "APPROVED", "executed", 0.0, "plink_test_6450", 290),
            ("act_15000", "txn_15000_card", "payment_link", "Network error recovery link dispatched.", 0.88, "APPROVED", "executed", 0.0, "plink_test_15000", 350),
            ("act_dupi01", "txn_demo_upi_01", "payment_link", "Autonomous WhatsApp payment link generated.", 0.95, "APPROVED", "executed", 0.0, "plink_test_dupi01", 8),
            ("act_dcard06", "txn_demo_card_06", "alternative_payment_method", "Card 3DS failure routed to UPI intent fallback.", 0.90, "APPROVED", "executed", 0.0, "plink_test_dcard06", 75),
            ("act_dupi07", "txn_demo_upi_07", "payment_link", "PhonePe checkout link dispatched.", 0.92, "APPROVED", "executed", 0.0, "plink_test_dupi07", 90),
            ("act_dupi09", "txn_demo_upi_09", "alternative_payment_method", "Autonomous payment link with netbanking option.", 0.91, "APPROVED", "executed", 0.0, "plink_test_dupi09", 125),
            ("act_dupi14", "txn_demo_upi_14", "payment_link", "Kotak UPI link dispatched.", 0.93, "APPROVED", "executed", 0.0, "plink_test_dupi14", 270),
            ("act_dcard15", "txn_demo_card_15", "payment_link", "3DS retry link dispatched.", 0.89, "APPROVED", "executed", 0.0, "plink_test_dcard15", 310),

            # Merchant 1 - Human Review Required (High-Value > ₹25k)
            ("act_highval", "txn_high_value", "human_review", "High-value order (₹50,000) exceeds autonomous threshold (₹25,000). Routed to human approval queue.", 0.96, "HUMAN_APPROVAL_REQUIRED", "pending", 0.0, None, 115),
            ("act_35000", "txn_35000_card", "human_review", "High-value card failure (₹35,000) routed for merchant finance approval.", 0.93, "HUMAN_APPROVAL_REQUIRED", "pending", 0.0, None, 145),
            ("act_42500", "txn_demo_card_02", "human_review", "Order exceeding ₹25,000 requires merchant manager review.", 0.95, "HUMAN_APPROVAL_REQUIRED", "pending", 0.0, None, 18),
            ("act_62000", "txn_demo_netb_04", "human_review", "High-value B2B purchase (₹62,000) requires verification before link generation.", 0.97, "HUMAN_APPROVAL_REQUIRED", "pending", 0.0, None, 45),
            ("act_75000", "txn_demo_netb_10", "human_review", "High-value transaction awaiting merchant authorization.", 0.98, "HUMAN_APPROVAL_REQUIRED", "pending", 0.0, None, 155),
            ("act_112000", "txn_demo_netb_16", "human_review", "High-value enterprise order (₹1,12,000) routed to VIP review queue.", 0.99, "HUMAN_APPROVAL_REQUIRED", "pending", 0.0, None, 375),

            # Merchant 1 - Blocked / Retries Exceeded
            ("act_retry_exc", "txn_retry_exceeded", "do_nothing", "Maximum retry threshold (2 attempts) exceeded. Autonomous recovery halted per policy.", 0.98, "BLOCKED", "cancelled", 0.0, None, 235),

            # Merchant 1 - Recovered
            ("act_recov_1", "txn_already_recovered", "payment_link", "Customer completed checkout via autonomous link.", 0.95, "APPROVED", "recovered", 3499.0, "plink_test_recov1", 390),
            ("act_recov_2", "txn_recovered_card", "payment_link", "Payment completed successfully after retry link.", 0.92, "APPROVED", "recovered", 9200.0, "plink_test_recov2", 450),
            ("act_recov_3", "txn_recovered_upi_2", "retry", "Automated retry executed on transient bank recovery.", 0.88, "APPROVED", "recovered", 1999.0, "plink_test_recov3", 510),
            ("act_recov_17", "txn_demo_recov_17", "payment_link", "Recovered via Razorpay pop-up checkout.", 0.93, "APPROVED", "recovered", 8499.0, "plink_test_recov17", 400),
            ("act_recov_18", "txn_demo_recov_18", "payment_link", "Autonomous link paid via UPI.", 0.96, "APPROVED", "recovered", 4999.0, "plink_test_recov18", 430),
            ("act_recov_19", "txn_demo_recov_19", "alternative_payment_method", "Customer completed payment on alternative channel.", 0.91, "APPROVED", "recovered", 13500.0, "plink_test_recov19", 470),
            ("act_recov_20", "txn_demo_recov_20", "payment_link", "Wallet payment re-attempted and recovered.", 0.87, "APPROVED", "recovered", 2199.0, "plink_test_recov20", 500),

            # Merchant 2 (Demo Fashion Store)
            ("act_m2_001", "txn_merchant_b_001", "payment_link", "Card drop-off recovery link dispatched.", 0.91, "APPROVED", "executed", 0.0, "plink_test_m2_001", 40),
            ("act_m2_4500", "txn_fashion_4500", "payment_link", "UPI timeout recovery link sent.", 0.94, "APPROVED", "executed", 0.0, "plink_test_m2_4500", 70),
            ("act_m2_8999", "txn_fashion_8999", "payment_link", "Card timeout fallback link dispatched.", 0.90, "APPROVED", "executed", 0.0, "plink_test_m2_8999", 135),
            ("act_m2_19999", "txn_fashion_19999", "payment_link", "Autonomous link generated.", 0.92, "APPROVED", "executed", 0.0, "plink_test_m2_19999", 110),
            ("act_m2_28000", "txn_fashion_28000", "human_review", "High-value fashion order (> ₹25k) pending approval.", 0.95, "HUMAN_APPROVAL_REQUIRED", "pending", 0.0, None, 195),
            ("act_m2_38500", "txn_fashion_38500", "human_review", "High-value bridal order (> ₹25k) pending approval.", 0.96, "HUMAN_APPROVAL_REQUIRED", "pending", 0.0, None, 180),
            ("act_m2_rec1", "txn_fashion_recovered_1", "payment_link", "Payment recovered via UPI.", 0.95, "APPROVED", "recovered", 3200.0, "plink_test_m2_rec1", 340),
            ("act_m2_rec2", "txn_fashion_recovered_2", "payment_link", "Payment recovered via Card.", 0.93, "APPROVED", "recovered", 6100.0, "plink_test_m2_rec2", 410),
            ("act_m2_rec3", "txn_fashion_recov_3", "payment_link", "Payment recovered via Razorpay pop-up.", 0.94, "APPROVED", "recovered", 4800.0, "plink_test_m2_rec3", 300),
            ("act_m2_rec4", "txn_fashion_recov_4", "payment_link", "Payment recovered via Card.", 0.92, "APPROVED", "recovered", 9500.0, "plink_test_m2_rec4", 370),
        ]

        for aid, atxn, atype, areason, aconf, apol, astat, arecov, aref, amins in recovery_actions_data:
            act_res = await session.execute(select(RecoveryAction).where(RecoveryAction.id == aid))
            if not act_res.scalar_one_or_none():
                session.add(
                    RecoveryAction(
                        id=aid,
                        transaction_id=atxn,
                        action_type=atype,
                        reason=areason,
                        confidence=aconf,
                        policy_decision=apol,
                        status=astat,
                        amount_recovered=arecov,
                        external_reference=aref,
                        created_at=now - timedelta(minutes=amins),
                        completed_at=now - timedelta(minutes=amins - 5) if astat in ("recovered", "completed") else None,
                    )
                )

        # 9. Revenue Risk Records
        risks_data = [
            # ID, TxnID, RiskType, RiskScore, Reason, RecoveryProb, ExpectedRecovery, Status
            ("risk_4999", "txn_4999_upi", "payment_failure", 0.22, "Transient UPI PSP timeout during checkout", 0.92, 4599.08, "action_scheduled"),
            ("risk_a001", "txn_merchant_a_001", "payment_failure", 0.35, "Bank-side UPI degradation detected on SBI gateway", 0.88, 11000.0, "action_scheduled"),
            ("risk_8999", "txn_8999_card", "payment_failure", 0.40, "3DS verification drop-off on card payment", 0.85, 7649.15, "action_scheduled"),
            ("risk_highval", "txn_high_value", "payment_failure", 0.75, "High-value transaction timeout (> ₹25,000)", 0.65, 32500.0, "investigating"),
            ("risk_35000", "txn_35000_card", "payment_failure", 0.70, "High-value card failure requiring human review", 0.68, 23800.0, "investigating"),
            ("risk_recov1", "txn_already_recovered", "payment_failure", 0.15, "Resolved via autonomous recovery link", 0.95, 3499.0, "recovered"),
            ("risk_recov2", "txn_recovered_card", "payment_failure", 0.18, "Resolved via Razorpay test modal", 0.92, 9200.0, "recovered"),
        ]

        for rid, rtxn, rtype, rscore, rreason, rprob, rexpect, rstat in risks_data:
            risk_res = await session.execute(select(RevenueRisk).where(RevenueRisk.id == rid))
            if not risk_res.scalar_one_or_none():
                session.add(
                    RevenueRisk(
                        id=rid,
                        transaction_id=rtxn,
                        risk_type=rtype,
                        risk_score=rscore,
                        detected_reason=rreason,
                        recovery_probability=rprob,
                        expected_recovery=rexpect,
                        status=rstat,
                        created_at=now,
                    )
                )

        # 10. Audit Logs (ordered chronologically from oldest to newest)
        audit_events = [
            ("aud_005", str(m1.id), "txn_already_recovered", "WebhookEngine", "PAYMENT_RECOVERED", "Cryptographic HMAC verified for payment_link.paid event. Marked recovered.", "APPROVED", 390),
            ("aud_007", str(m2.id), "txn_fashion_28000", "PolicyEngine", "EVALUATE_POLICY", "Fashion order ₹28,000 routed to human review queue (§6).", "HUMAN_APPROVAL_REQUIRED", 194),
            ("aud_004", str(m1.id), "txn_high_value", "PolicyEngine", "EVALUATE_POLICY", "Amount ₹50,000 exceeds ₹25,000 threshold (§6 High Value Transactions). Routed to human queue.", "HUMAN_APPROVAL_REQUIRED", 114),
            ("aud_006", str(m2.id), "txn_merchant_b_001", "RootCauseAgent", "DIAGNOSE_FAILURE", "Diagnosed 3DS drop-off on card payment. Confidence: 91%.", "APPROVED", 44),
            ("aud_001", str(m1.id), "txn_4999_upi", "RootCauseAgent", "DIAGNOSE_FAILURE", "Identified transient UPI PSP timeout on HDFC bank. Model confidence: 94%.", "APPROVED", 14),
            ("aud_002", str(m1.id), "txn_4999_upi", "PolicyEngine", "EVALUATE_POLICY", "Evaluated §2 UPI Failures from merchant_policy.md. Verdict: APPROVED.", "APPROVED", 13),
            ("aud_003", str(m1.id), "txn_4999_upi", "RecoveryExecutor", "DISPATCH_ACTION", "Generated Razorpay smart checkout link and dispatched via omnichannel messaging.", "APPROVED", 12),
        ]

        merchant_prev_hashes: dict[str, str] = {}
        for aid, amid, atxn, aagent, aact, asummary, apol, amins in audit_events:
            m_key = str(amid) if amid is not None else "global"
            prev_hash = merchant_prev_hashes.get(m_key, "0" * 64)
            aud_res = await session.execute(select(AuditLog).where(AuditLog.id == aid))
            if not aud_res.scalar_one_or_none():
                created_dt = now - timedelta(minutes=amins)
                ev_hash = AuditLog.calculate_hash(
                    id_str=aid,
                    transaction_id=atxn,
                    agent_name=aagent,
                    action=aact,
                    reasoning_summary=asummary,
                    policy_result=apol,
                    previous_hash=prev_hash,
                    created_at_str=created_dt.isoformat(),
                    merchant_id=str(amid) if amid is not None else None,
                )
                session.add(
                    AuditLog(
                        id=aid,
                        merchant_id=str(amid) if amid is not None else None,
                        transaction_id=atxn,
                        agent_name=aagent,
                        actor="system",
                        action=aact,
                        reasoning_summary=asummary,
                        policy_result=apol,
                        previous_hash=prev_hash,
                        event_hash=ev_hash,
                        created_at=created_dt,
                    )
                )
                merchant_prev_hashes[m_key] = ev_hash

        await session.commit()
        logger.info("Database seeding completed successfully.")



if __name__ == "__main__":
    asyncio.run(seed_database())
