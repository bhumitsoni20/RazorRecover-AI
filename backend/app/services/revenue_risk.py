from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.models.transaction import Transaction
from app.models.customer import Customer
from app.models.revenue_risk import RevenueRisk
from app.services.anomaly_detector import AnomalyDetectorService
from app.core.logging import logger


class RevenueRiskService:
    """
    Core Deterministic Revenue Risk & Loss Probability Engine for RazorRecover AI.
    Calculates expected revenue loss: Revenue at Risk = sum(amount * loss_probability)
    where loss_probability = 1.0 - recovery_probability.
    """

    # Risk level threshold configuration
    RISK_LEVEL_THRESHOLDS = {
        "LOW": (0.00, 0.249),
        "MEDIUM": (0.250, 0.499),
        "HIGH": (0.500, 0.749),
        "CRITICAL": (0.750, 1.000),
    }

    @classmethod
    def get_risk_level(cls, loss_probability: float) -> str:
        """Determines categorical risk level from deterministic loss probability."""
        if loss_probability >= 0.75:
            return "CRITICAL"
        elif loss_probability >= 0.50:
            return "HIGH"
        elif loss_probability >= 0.25:
            return "MEDIUM"
        else:
            return "LOW"

    @classmethod
    def compute_loss_probability(
        cls,
        amount: float,
        payment_method: str,
        failure_reason: Optional[str],
        attempt_number: int = 1,
        customer_success_rate: float = 0.85,
        is_anomaly_active: bool = False,
    ) -> Tuple[float, float, str, str]:
        """
        Transparent baseline probability scoring model.
        Returns:
            (loss_probability, recovery_probability, risk_level, explanation)
        """
        reason = (failure_reason or "unknown").lower()
        method = (payment_method or "upi").lower()

        # 1. Base recovery probability by failure archetype
        if any(r in reason for r in ["upi_timeout", "bank_degraded", "gateway_timeout", "network_error"]):
            base_recovery = 0.88
            core_desc = "Transient technical or gateway timeout"
        elif any(r in reason for r in ["checkout_abandonment", "user_aborted", "session_expired"]):
            base_recovery = 0.72
            core_desc = "Checkout drop-off / session abandonment"
        elif any(r in reason for r in ["card_expired", "card_declined_transient"]):
            base_recovery = 0.80
            core_desc = "Expired payment credential with update path"
        elif any(r in reason for r in ["insufficient_funds", "auth_failed", "pin_incorrect"]):
            base_recovery = 0.32
            core_desc = "Customer-side authorization / balance deficiency"
        else:
            base_recovery = 0.65
            core_desc = "Uncategorized transaction failure"

        # 2. Adjustments based on attempt count (repeated failures = higher loss risk)
        if attempt_number >= 3:
            base_recovery -= 0.40
            core_desc += f" (Exceeded safe retry limit: attempt #{attempt_number})"
        elif attempt_number == 2:
            base_recovery -= 0.15
            core_desc += " (Second consecutive failure attempt)"

        # 3. Adjustments based on transaction value
        if amount > 25000:
            base_recovery -= 0.10
            core_desc += f" (High-value amount ₹{amount:,.0f} requiring verification)"

        # 4. Customer payment history adjustment
        if customer_success_rate >= 0.80:
            base_recovery += 0.05
        elif customer_success_rate < 0.50:
            base_recovery -= 0.10

        # 5. Network anomaly context adjustment
        if is_anomaly_active and method == "upi":
            base_recovery += 0.04  # Recovery links are especially effective during network degradation

        # Final clamped probabilities
        recov_prob = round(max(0.05, min(0.95, base_recovery)), 3)
        loss_prob = round(1.0 - recov_prob, 3)
        risk_level = cls.get_risk_level(loss_prob)

        explanation = f"{core_desc}. Loss probability: {round(loss_prob * 100, 1)}% ({risk_level} risk tier)."

        return loss_prob, recov_prob, risk_level, explanation

    @classmethod
    async def get_revenue_risk_summary(cls, db: AsyncSession) -> Dict[str, Any]:
        """
        Aggregates real database transactions to compute total revenue at risk,
        breakdowns, and anomaly alerts.
        """
        # Fetch active anomalies
        anomaly_report = await AnomalyDetectorService.detect_payment_anomalies(db)
        is_upi_anomaly = anomaly_report.get("has_anomaly", False)

        # Query all at-risk transactions (failed, abandoned, pending)
        query = (
            select(Transaction, Customer)
            .join(Customer, Customer.id == Transaction.customer_id)
            .where(Transaction.status.in_(["failed", "abandoned", "pending"]))
            .order_by(desc(Transaction.created_at))
        )
        result = (await db.execute(query)).all()

        total_risk_revenue = 0.0
        total_gross_at_risk = 0.0
        weighted_loss_prob_sum = 0.0
        count = len(result)

        category_buckets: Dict[str, Dict[str, Any]] = {
            "Payment Failures": {"amount": 0.0, "count": 0, "color": "#ef4444"},
            "Checkout Abandonment": {"amount": 0.0, "count": 0, "color": "#f59e0b"},
            "Bank Degradation": {"amount": 0.0, "count": 0, "color": "#8b5cf6"},
            "Invoices & Subscriptions": {"amount": 0.0, "count": 0, "color": "#6366f1"},
        }

        risk_distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}

        for txn, cust in result:
            cust_succ_rate = (
                cust.successful_transactions / max(cust.total_transactions, 1)
                if cust else 0.85
            )
            loss_prob, recov_prob, risk_level, _ = cls.compute_loss_probability(
                amount=txn.amount,
                payment_method=txn.payment_method,
                failure_reason=txn.failure_reason,
                attempt_number=txn.attempt_number,
                customer_success_rate=cust_succ_rate,
                is_anomaly_active=is_upi_anomaly,
            )

            expected_loss = round(txn.amount * loss_prob, 2)
            total_risk_revenue += expected_loss
            total_gross_at_risk += txn.amount
            weighted_loss_prob_sum += loss_prob
            risk_distribution[risk_level] += 1

            # Map to meaningful categories
            reason = (txn.failure_reason or "").lower()
            method = (txn.payment_method or "").lower()

            if "abandon" in reason or txn.status == "abandoned":
                cat = "Checkout Abandonment"
            elif "degraded" in reason or "timeout" in reason or "network" in reason:
                cat = "Bank Degradation"
            elif method in ["subscription", "invoice"] or "sub" in reason:
                cat = "Invoices & Subscriptions"
            else:
                cat = "Payment Failures"

            category_buckets[cat]["amount"] += expected_loss
            category_buckets[cat]["count"] += 1

        avg_loss_prob = round(weighted_loss_prob_sum / count, 3) if count > 0 else 0.0

        # Format top risk sources
        top_risk_sources = []
        for cat_name, cat_data in category_buckets.items():
            if cat_data["count"] > 0 or cat_data["amount"] > 0:
                pct = round((cat_data["amount"] / total_risk_revenue) * 100, 1) if total_risk_revenue > 0 else 0.0
                top_risk_sources.append({
                    "category": cat_name,
                    "amount": round(cat_data["amount"], 2),
                    "percentage": pct,
                    "transaction_count": cat_data["count"],
                    "color": cat_data["color"],
                })

        return {
            "total_revenue_at_risk": round(total_risk_revenue, 2),
            "total_gross_failed_volume": round(total_gross_at_risk, 2),
            "currency": "INR",
            "transaction_count": count,
            "average_loss_probability": avg_loss_prob,
            "risk_distribution": risk_distribution,
            "top_risk_sources": top_risk_sources,
            "anomaly_detected": anomaly_report.get("has_anomaly", False),
            "anomaly_message": anomaly_report.get("primary_message"),
            "anomalies": anomaly_report.get("anomalies", []),
            "calculated_at": datetime.utcnow().isoformat(),
        }

    @classmethod
    async def get_transaction_risks(
        cls,
        db: AsyncSession,
        page: int = 1,
        limit: int = 20,
        risk_level_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Returns paginated list of at-risk transactions with computed loss metrics.
        """
        anomaly_report = await AnomalyDetectorService.detect_payment_anomalies(db)
        is_upi_anomaly = anomaly_report.get("has_anomaly", False)

        query = (
            select(Transaction, Customer)
            .join(Customer, Customer.id == Transaction.customer_id)
            .where(Transaction.status.in_(["failed", "abandoned", "pending"]))
            .order_by(desc(Transaction.created_at))
        )
        result = (await db.execute(query)).all()

        items = []
        for txn, cust in result:
            cust_succ_rate = (
                cust.successful_transactions / max(cust.total_transactions, 1)
                if cust else 0.85
            )
            loss_prob, recov_prob, risk_level, explanation = cls.compute_loss_probability(
                amount=txn.amount,
                payment_method=txn.payment_method,
                failure_reason=txn.failure_reason,
                attempt_number=txn.attempt_number,
                customer_success_rate=cust_succ_rate,
                is_anomaly_active=is_upi_anomaly,
            )

            if risk_level_filter and risk_level_filter.upper() != "ALL" and risk_level != risk_level_filter.upper():
                continue

            revenue_at_risk = round(txn.amount * loss_prob, 2)

            items.append({
                "transaction_id": txn.id,
                "amount": txn.amount,
                "currency": txn.currency,
                "status": txn.status,
                "payment_method": txn.payment_method,
                "bank": txn.bank,
                "customer_name": cust.name if cust else "Unknown",
                "customer_email": cust.email if cust else "N/A",
                "failure_reason": txn.failure_reason,
                "attempt_number": txn.attempt_number,
                "loss_probability": loss_prob,
                "successful_recovery_probability": recov_prob,
                "revenue_at_risk": revenue_at_risk,
                "risk_level": risk_level,
                "explanation": explanation,
                "created_at": txn.created_at.strftime("%Y-%m-%d %H:%M:%S") if txn.created_at else "",
            })

        total = len(items)
        start = (page - 1) * limit
        paginated_items = items[start : start + limit]

        return {
            "items": paginated_items,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": max(1, (total + limit - 1) // limit),
        }
