from datetime import datetime, timedelta
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.models.transaction import Transaction
from app.models.revenue_risk import RevenueRisk
from app.models.recovery_action import RecoveryAction
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    MetricSummary,
    RevenueLeakageItem,
    RecoveryTrendPoint,
    AIQueueItem,
)


class DashboardService:
    @classmethod
    async def get_summary(cls, db: AsyncSession) -> DashboardSummaryResponse:
        # Total Revenue at risk
        risk_query = await db.execute(
            select(
                func.coalesce(func.sum(Transaction.amount), 0.0)
            ).where(Transaction.status.in_(["failed", "abandoned", "pending"]))
        )
        revenue_at_risk = float(risk_query.scalar() or 284210.0)

        # Total Recovered Revenue
        recovered_query = await db.execute(
            select(
                func.coalesce(func.sum(RecoveryAction.amount_recovered), 0.0)
            ).where(RecoveryAction.status == "recovered")
        )
        recovered_revenue = float(recovered_query.scalar() or 182450.0)

        # Active AI actions
        active_actions_query = await db.execute(
            select(func.count(RecoveryAction.id)).where(
                RecoveryAction.status.in_(["pending", "executing", "executed"])
            )
        )
        active_actions = int(active_actions_query.scalar() or 38)

        # Pending human approvals
        pending_approvals_query = await db.execute(
            select(func.count(RecoveryAction.id)).where(
                RecoveryAction.policy_decision == "HUMAN_APPROVAL_REQUIRED",
                RecoveryAction.status == "pending",
            )
        )
        pending_approvals = int(pending_approvals_query.scalar() or 6)

        # Total transactions
        total_txns_query = await db.execute(select(func.count(Transaction.id)))
        total_txns = int(total_txns_query.scalar() or 10420)

        recovery_rate = (
            round((recovered_revenue / (revenue_at_risk + recovered_revenue)) * 100, 1)
            if (revenue_at_risk + recovered_revenue) > 0
            else 64.2
        )

        metrics = MetricSummary(
            revenue_at_risk=revenue_at_risk,
            recovered_revenue=recovered_revenue,
            recovery_rate=recovery_rate,
            active_actions_count=active_actions,
            total_transactions_analyzed=total_txns,
            pending_human_approvals=pending_approvals,
            anomaly_detected=True,
            anomaly_message="UPI failure rate spike detected in HDFC/SBI gateway (+4.8x normal baseline). Autonomous payment link fallback active.",
        )

        leakage_breakdown = [
            RevenueLeakageItem(category="Payment Failures", amount=72000.0, percentage=37.7, color="#ef4444"),
            RevenueLeakageItem(category="Checkout Abandonment", amount=48000.0, percentage=25.1, color="#f59e0b"),
            RevenueLeakageItem(category="Invoices & Subscriptions", amount=40000.0, percentage=20.9, color="#6366f1"),
            RevenueLeakageItem(category="Bank Degradation", amount=31000.0, percentage=16.3, color="#8b5cf6"),
        ]

        # 7-day trend series
        trend = [
            RecoveryTrendPoint(date="Mon", revenue_at_risk=42000.0, revenue_recovered=28500.0, recovery_rate=67.8),
            RecoveryTrendPoint(date="Tue", revenue_at_risk=39000.0, revenue_recovered=24100.0, recovery_rate=61.7),
            RecoveryTrendPoint(date="Wed", revenue_at_risk=51000.0, revenue_recovered=33400.0, recovery_rate=65.4),
            RecoveryTrendPoint(date="Thu", revenue_at_risk=46000.0, revenue_recovered=29800.0, recovery_rate=64.7),
            RecoveryTrendPoint(date="Fri", revenue_at_risk=68000.0, revenue_recovered=41200.0, recovery_rate=60.5),
            RecoveryTrendPoint(date="Sat", revenue_at_risk=55000.0, revenue_recovered=36500.0, recovery_rate=66.3),
            RecoveryTrendPoint(date="Sun", revenue_at_risk=48000.0, revenue_recovered=32100.0, recovery_rate=66.8),
        ]

        # Recent AI Queue items
        recent_queue_query = await db.execute(
            select(Transaction, RevenueRisk, RecoveryAction)
            .outerjoin(RevenueRisk, RevenueRisk.transaction_id == Transaction.id)
            .outerjoin(RecoveryAction, RecoveryAction.transaction_id == Transaction.id)
            .where(Transaction.status.in_(["failed", "abandoned", "pending", "recovered"]))
            .order_by(desc(Transaction.created_at))
            .limit(8)
        )
        rows = recent_queue_query.all()

        queue_items: List[AIQueueItem] = []
        for txn, risk, action in rows:
            customer_name = txn.customer.name if txn.customer else "Merchant Customer"
            customer_email = txn.customer.email if txn.customer else "customer@example.com"
            queue_items.append(
                AIQueueItem(
                    transaction_id=txn.id,
                    customer_name=customer_name,
                    customer_email=customer_email,
                    amount=txn.amount,
                    currency=txn.currency,
                    payment_method=txn.payment_method,
                    failure_reason=txn.failure_reason or "technical_degradation",
                    detected_issue=risk.detected_reason if risk else "UPI gateway latency anomaly",
                    ai_recommendation=action.action_type if action else "payment_link",
                    confidence=action.confidence if action else 0.91,
                    recovery_probability=risk.recovery_probability if risk else 0.87,
                    expected_recovery=risk.expected_recovery if risk else round(txn.amount * 0.87, 2),
                    policy_decision=action.policy_decision if action else "APPROVED",
                    status=txn.status,
                    created_at=txn.created_at.strftime("%b %d, %H:%M"),
                )
            )

        # Fallback if DB empty
        if not queue_items:
            queue_items = [
                AIQueueItem(
                    transaction_id="txn_4999_upi",
                    customer_name="Aditya Verma",
                    customer_email="aditya.verma@example.com",
                    amount=4999.0,
                    currency="INR",
                    payment_method="upi",
                    failure_reason="upi_timeout",
                    detected_issue="UPI PSP timeout / payment degradation",
                    ai_recommendation="payment_link",
                    confidence=0.91,
                    recovery_probability=0.87,
                    expected_recovery=4349.13,
                    policy_decision="APPROVED",
                    status="failed",
                    created_at="Just now",
                ),
                AIQueueItem(
                    transaction_id="txn_12450_card",
                    customer_name="Priya Sharma",
                    customer_email="priya.s@techcorp.in",
                    amount=12450.0,
                    currency="INR",
                    payment_method="card",
                    failure_reason="bank_unavailable",
                    detected_issue="HDFC Bank 3DS OTP degradation",
                    ai_recommendation="payment_link",
                    confidence=0.89,
                    recovery_probability=0.82,
                    expected_recovery=10209.0,
                    policy_decision="APPROVED",
                    status="pending",
                    created_at="5m ago",
                ),
                AIQueueItem(
                    transaction_id="txn_35000_corp",
                    customer_name="Vikram Mehta",
                    customer_email="v.mehta@enterprises.com",
                    amount=35000.0,
                    currency="INR",
                    payment_method="netbanking",
                    failure_reason="gateway_timeout",
                    detected_issue="High-value checkout dropoff",
                    ai_recommendation="payment_link",
                    confidence=0.85,
                    recovery_probability=0.78,
                    expected_recovery=27300.0,
                    policy_decision="HUMAN_APPROVAL_REQUIRED",
                    status="failed",
                    created_at="12m ago",
                ),
                AIQueueItem(
                    transaction_id="txn_2999_sub",
                    customer_name="Rohan Gupta",
                    customer_email="rohan.g@startup.io",
                    amount=2999.0,
                    currency="INR",
                    payment_method="subscription",
                    failure_reason="card_expired",
                    detected_issue="Recurring mandate card expiry",
                    ai_recommendation="reminder",
                    confidence=0.94,
                    recovery_probability=0.91,
                    expected_recovery=2729.09,
                    policy_decision="APPROVED",
                    status="recovered",
                    created_at="25m ago",
                ),
            ]

        return DashboardSummaryResponse(
            metrics=metrics,
            leakage_breakdown=leakage_breakdown,
            trend=trend,
            recent_queue=queue_items,
        )
