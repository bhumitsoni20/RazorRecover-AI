import asyncio
import os
import sys
from datetime import datetime, timedelta

# Ensure backend path is on sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal, engine, Base
from app.core.config import settings
from app.core.security import hash_password
from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.transaction import Transaction
from app.models.revenue_risk import RevenueRisk
from app.models.recovery_action import RecoveryAction
from app.models.audit_log import AuditLog
from app.core.logging import logger
import app.models  # noqa


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

        await session.commit()
        logger.info("Database seeding completed successfully.")



if __name__ == "__main__":
    asyncio.run(seed_database())
