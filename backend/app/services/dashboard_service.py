from datetime import datetime, timedelta

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.recovery_action import RecoveryAction
from app.models.revenue_risk import RevenueRisk
from app.models.transaction import Transaction
from app.schemas.dashboard import (
    AIQueueItem,
    DashboardSummaryResponse,
    MetricSummary,
    RecoveryTrendPoint,
    RevenueLeakageItem,
)
from app.services.revenue_risk import RevenueRiskService


class DashboardService:
    @classmethod
    async def get_summary(cls, db: AsyncSession, merchant_id: str | None = None) -> DashboardSummaryResponse:
        # 1. Real Deterministic Revenue at Risk & Anomaly Summary for Merchant
        risk_summary = await RevenueRiskService.get_revenue_risk_summary(db, merchant_id=merchant_id)
        revenue_at_risk = risk_summary["total_revenue_at_risk"]
        anomaly_detected = risk_summary["anomaly_detected"]
        anomaly_message = risk_summary["anomaly_message"]

        # 2. Total Recovered Revenue (from Transaction status == 'recovered')
        recovered_stmt = select(func.coalesce(func.sum(Transaction.amount), 0.0)).where(Transaction.status == "recovered")
        if merchant_id:
            recovered_stmt = recovered_stmt.where(Transaction.merchant_id == merchant_id)
        recovered_query = await db.execute(recovered_stmt)
        recovered_revenue = float(recovered_query.scalar() or 0.0)

        # 3. Active AI actions
        active_actions_stmt = (
            select(func.count(RecoveryAction.id))
            .join(Transaction, Transaction.id == RecoveryAction.transaction_id)
            .where(RecoveryAction.status.in_(["pending", "executing", "executed"]))
        )
        if merchant_id:
            active_actions_stmt = active_actions_stmt.where(Transaction.merchant_id == merchant_id)
        active_actions_query = await db.execute(active_actions_stmt)
        active_actions = int(active_actions_query.scalar() or 0)

        # 4. Pending human approvals
        pending_approvals_stmt = (
            select(func.count(RecoveryAction.id))
            .join(Transaction, Transaction.id == RecoveryAction.transaction_id)
            .where(
                RecoveryAction.policy_decision == "HUMAN_APPROVAL_REQUIRED",
                RecoveryAction.status == "pending",
            )
        )
        if merchant_id:
            pending_approvals_stmt = pending_approvals_stmt.where(Transaction.merchant_id == merchant_id)
        pending_approvals_query = await db.execute(pending_approvals_stmt)
        pending_approvals = int(pending_approvals_query.scalar() or 0)

        # 5. Total transactions analyzed
        total_txns_stmt = select(func.count(Transaction.id))
        if merchant_id:
            total_txns_stmt = total_txns_stmt.where(Transaction.merchant_id == merchant_id)
        total_txns_query = await db.execute(total_txns_stmt)
        total_txns = int(total_txns_query.scalar() or 0)

        # 6. Overall Recovery Rate
        recovery_rate = (
            round((recovered_revenue / (revenue_at_risk + recovered_revenue)) * 100, 1)
            if (revenue_at_risk + recovered_revenue) > 0
            else 0.0
        )

        metrics = MetricSummary(
            revenue_at_risk=revenue_at_risk,
            recovered_revenue=recovered_revenue,
            recovery_rate=recovery_rate,
            active_actions_count=active_actions,
            total_transactions_analyzed=total_txns,
            pending_human_approvals=pending_approvals,
            anomaly_detected=anomaly_detected,
            anomaly_message=anomaly_message,
        )

        # 7. Dynamic Revenue Leakage Breakdown from database
        leakage_breakdown: list[RevenueLeakageItem] = []
        for src in risk_summary["top_risk_sources"]:
            leakage_breakdown.append(
                RevenueLeakageItem(
                    category=src["category"],
                    amount=src["amount"],
                    percentage=src["percentage"],
                    color=src["color"],
                )
            )

        if not leakage_breakdown:
            leakage_breakdown = [
                RevenueLeakageItem(category="Payment Failures", amount=0.0, percentage=0.0, color="#ef4444"),
                RevenueLeakageItem(category="Checkout Abandonment", amount=0.0, percentage=0.0, color="#f59e0b"),
                RevenueLeakageItem(category="Bank Degradation", amount=0.0, percentage=0.0, color="#8b5cf6"),
                RevenueLeakageItem(category="Invoices & Subscriptions", amount=0.0, percentage=0.0, color="#6366f1"),
            ]

        # 8. Real 7-day Historical Trend from Database Timestamps
        max_time_stmt = select(func.max(Transaction.created_at))
        if merchant_id:
            max_time_stmt = max_time_stmt.where(Transaction.merchant_id == merchant_id)
        max_time_query = await db.execute(max_time_stmt)
        anchor_time = max_time_query.scalar() or datetime.utcnow()

        trend: list[RecoveryTrendPoint] = []
        # Calculate daily aggregates for the past 7 days up to anchor_time
        for day_offset in range(6, -1, -1):
            day_start = (anchor_time - timedelta(days=day_offset)).replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            day_label = day_start.strftime("%a")

            # Day's at-risk transactions
            failed_conditions = [
                Transaction.created_at >= day_start,
                Transaction.created_at < day_end,
                Transaction.status.in_(["failed", "abandoned", "pending"]),
            ]
            if merchant_id:
                failed_conditions.append(Transaction.merchant_id == merchant_id)

            day_failed_query = await db.execute(
                select(Transaction.amount, Transaction.failure_reason, Transaction.payment_method, Transaction.attempt_number)
                .where(and_(*failed_conditions))
            )
            failed_rows = day_failed_query.all()
            day_risk_amount = 0.0
            for r in failed_rows:
                l_prob, _, _, _ = RevenueRiskService.compute_loss_probability(
                    amount=r.amount,
                    payment_method=r.payment_method,
                    failure_reason=r.failure_reason,
                    attempt_number=r.attempt_number,
                )
                day_risk_amount += r.amount * l_prob

            # Day's recovered transactions
            recov_conditions = [
                Transaction.created_at >= day_start,
                Transaction.created_at < day_end,
                Transaction.status == "recovered",
            ]
            if merchant_id:
                recov_conditions.append(Transaction.merchant_id == merchant_id)

            day_recov_query = await db.execute(
                select(func.coalesce(func.sum(Transaction.amount), 0.0))
                .where(and_(*recov_conditions))
            )
            day_recovered = float(day_recov_query.scalar() or 0.0)

            day_total = day_risk_amount + day_recovered
            day_rate = round((day_recovered / day_total) * 100, 1) if day_total > 0 else 0.0

            trend.append(
                RecoveryTrendPoint(
                    date=day_label,
                    revenue_at_risk=round(day_risk_amount, 2),
                    revenue_recovered=round(day_recovered, 2),
                    recovery_rate=day_rate,
                )
            )

        # 9. Recent AI Queue items from real DB
        recent_queue_stmt = (
            select(Transaction, Customer, RevenueRisk, RecoveryAction)
            .join(Customer, Customer.id == Transaction.customer_id)
            .outerjoin(RevenueRisk, RevenueRisk.transaction_id == Transaction.id)
            .outerjoin(RecoveryAction, RecoveryAction.transaction_id == Transaction.id)
            .where(Transaction.status.in_(["failed", "abandoned", "pending", "recovered"]))
        )
        if merchant_id:
            recent_queue_stmt = recent_queue_stmt.where(Transaction.merchant_id == merchant_id)

        recent_queue_stmt = recent_queue_stmt.order_by(desc(Transaction.created_at)).limit(8)
        recent_queue_query = await db.execute(recent_queue_stmt)
        rows = recent_queue_query.all()

        queue_items: list[AIQueueItem] = []
        for txn, cust, risk, action in rows:
            loss_prob, recov_prob, risk_level, expl = RevenueRiskService.compute_loss_probability(
                amount=txn.amount,
                payment_method=txn.payment_method,
                failure_reason=txn.failure_reason,
                attempt_number=txn.attempt_number,
                customer_success_rate=(
                    cust.successful_transactions / max(cust.total_transactions, 1) if cust else 0.85
                ),
                is_anomaly_active=anomaly_detected,
            )

            queue_items.append(
                AIQueueItem(
                    transaction_id=txn.id,
                    customer_name=cust.name,
                    customer_email=cust.email,
                    amount=txn.amount,
                    currency=txn.currency,
                    payment_method=txn.payment_method,
                    failure_reason=txn.failure_reason or "technical_degradation",
                    detected_issue=risk.detected_reason if risk else expl,
                    ai_recommendation=action.action_type if action else "payment_link",
                    confidence=action.confidence if action else round(recov_prob, 2),
                    recovery_probability=risk.recovery_probability if risk else recov_prob,
                    expected_recovery=risk.expected_recovery if risk else round(txn.amount * recov_prob, 2),
                    policy_decision=action.policy_decision if action else ("APPROVED" if txn.amount <= 25000 else "HUMAN_APPROVAL_REQUIRED"),
                    status=txn.status,
                    created_at=txn.created_at.strftime("%b %d, %H:%M") if txn.created_at else "",
                )
            )

        return DashboardSummaryResponse(
            metrics=metrics,
            leakage_breakdown=leakage_breakdown,
            trend=trend,
            recent_queue=queue_items,
        )
