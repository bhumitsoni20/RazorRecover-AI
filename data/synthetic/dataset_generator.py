import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any


BANKS = ["HDFC", "ICICI", "SBI", "AXIS", "KOTAK", "YES_BANK"]
PAYMENT_METHODS = ["upi", "card", "netbanking", "subscription", "wallet"]
FAILURE_REASONS = [
    "upi_timeout",
    "bank_degraded",
    "insufficient_funds",
    "auth_failed",
    "checkout_abandonment",
    "card_expired",
    "gateway_timeout",
    "user_aborted",
]

CUSTOMER_NAMES = [
    ("Aditya Verma", "aditya.verma@example.com"),
    ("Priya Sharma", "priya.s@techcorp.in"),
    ("Vikram Mehta", "v.mehta@enterprises.com"),
    ("Rohan Gupta", "rohan.g@startup.io"),
    ("Sneha Patel", "sneha.p@designstudio.com"),
    ("Arjun Nair", "arjun.nair@fintech.co"),
    ("Ananya Roy", "ananya.roy@retailhub.in"),
    ("Karan Singh", "karan.singh@ecommerce.org"),
    ("Neha Deshmukh", "neha.d@cloudservices.in"),
    ("Rajesh Kumar", "rajesh.k@logisticsindia.com"),
]


class SyntheticDataGenerator:
    """
    Generates realistic payment failure, recovery, and anomaly datasets for RazorRecover AI.
    """

    @classmethod
    def generate_transactions(cls, count: int = 10000) -> List[Dict[str, Any]]:
        transactions = []
        base_time = datetime.utcnow() - timedelta(days=14)

        for i in range(count):
            # Timestamp distribution across 14 days
            txn_time = base_time + timedelta(
                days=random.uniform(0, 14),
                hours=random.uniform(0, 24),
                minutes=random.uniform(0, 60),
            )
            hour = txn_time.hour

            # Injected anomaly: UPI spike between 12:00 and 15:00
            is_anomaly_window = 12 <= hour <= 15
            payment_method = random.choices(
                PAYMENT_METHODS,
                weights=[0.55, 0.25, 0.10, 0.07, 0.03],
                k=1
            )[0]

            # Determine failure probability
            if payment_method == "upi" and is_anomaly_window:
                fail_rate = 0.142  # 14.2% failure spike
            elif payment_method == "upi":
                fail_rate = 0.032  # 3.2% baseline
            elif payment_method == "card":
                fail_rate = 0.055
            elif payment_method == "netbanking":
                fail_rate = 0.048
            else:
                fail_rate = 0.040

            is_failed = random.random() < fail_rate

            if is_failed:
                status = random.choices(
                    ["failed", "abandoned", "pending", "recovered"],
                    weights=[0.35, 0.15, 0.10, 0.40],
                    k=1
                )[0]
                if payment_method == "upi" and is_anomaly_window:
                    failure_reason = "upi_timeout"
                else:
                    failure_reason = random.choice(FAILURE_REASONS)
            else:
                status = "success"
                failure_reason = None

            # Realistic transaction amount (log-normal distribution)
            if payment_method == "subscription":
                amount = random.choice([499.0, 999.0, 1999.0, 2999.0, 4999.0])
            elif payment_method == "netbanking":
                amount = round(random.uniform(5000.0, 45000.0), 2)
            else:
                amount = round(random.choice([
                    random.uniform(299.0, 1999.0),
                    random.uniform(1999.0, 7999.0),
                    random.uniform(7999.0, 28000.0),
                ]), 2)

            cust_name, cust_email = random.choice(CUSTOMER_NAMES)
            txn_id = f"txn_{uuid.uuid4().hex[:12]}"

            # Calculate ML recovery probability based on features
            if is_failed:
                if failure_reason in ["upi_timeout", "bank_degraded", "gateway_timeout"]:
                    base_prob = 0.88
                elif failure_reason in ["checkout_abandonment", "user_aborted"]:
                    base_prob = 0.72
                elif failure_reason == "card_expired":
                    base_prob = 0.80
                else:
                    base_prob = 0.35  # insufficient funds etc.

                # Adjust for amount
                if amount > 25000:
                    base_prob -= 0.10
                recovery_prob = round(max(0.15, min(0.96, base_prob + random.uniform(-0.05, 0.05))), 3)
                risk_score = round(1.0 - recovery_prob * 0.9, 3)
            else:
                recovery_prob = 1.0
                risk_score = 0.05

            transactions.append({
                "id": txn_id,
                "customer_name": cust_name,
                "customer_email": cust_email,
                "amount": amount,
                "currency": "INR",
                "payment_method": payment_method,
                "payment_gateway": "razorpay",
                "bank": random.choice(BANKS),
                "status": status,
                "failure_reason": failure_reason,
                "attempt_number": 1 if not is_failed else random.choice([1, 1, 1, 2]),
                "risk_score": risk_score,
                "recovery_probability": recovery_prob,
                "expected_recovery": round(amount * recovery_prob, 2),
                "created_at": txn_time,
            })

        return transactions
