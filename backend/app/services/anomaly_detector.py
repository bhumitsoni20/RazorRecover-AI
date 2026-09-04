from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction


class AnomalyDetectorService:
    """
    Deterministic Payment & Gateway Anomaly Detection Service.
    Computes real database failure rate baselines and detects abnormal failure spikes.
    """

    DEFAULT_METHODS = ["upi", "card", "netbanking", "subscription", "wallet"]

    @classmethod
    async def detect_payment_anomalies(
        cls,
        db: AsyncSession,
        recent_window_hours: int = 4,
    ) -> dict[str, Any]:
        """
        Scans transaction history in the database to detect payment method degradation or failure spikes.
        """
        # Fetch latest transaction timestamp to anchor sliding window
        max_time_query = await db.execute(select(func.max(Transaction.created_at)))
        latest_time = max_time_query.scalar() or datetime.utcnow()

        window_start = latest_time - timedelta(hours=recent_window_hours)

        # 1. Total counts in recent window vs historical baseline
        recent_stats_query = await db.execute(
            select(
                Transaction.payment_method,
                func.count(Transaction.id).label("total_count"),
                func.sum(
                    case((Transaction.status.in_(["failed", "abandoned"]), 1), else_=0)
                ).label("failed_count"),
            )
            .where(Transaction.created_at >= window_start)
            .group_by(Transaction.payment_method)
        )
        recent_stats = {
            row.payment_method: {
                "total": int(row.total_count or 0),
                "failed": int(row.failed_count or 0),
            }
            for row in recent_stats_query.all()
        }

        # 2. Historical baseline stats (older than recent window)
        baseline_stats_query = await db.execute(
            select(
                Transaction.payment_method,
                func.count(Transaction.id).label("total_count"),
                func.sum(
                    case((Transaction.status.in_(["failed", "abandoned"]), 1), else_=0)
                ).label("failed_count"),
            )
            .where(Transaction.created_at < window_start)
            .group_by(Transaction.payment_method)
        )
        baseline_stats = {
            row.payment_method: {
                "total": int(row.total_count or 0),
                "failed": int(row.failed_count or 0),
            }
            for row in baseline_stats_query.all()
        }

        detected_anomalies: list[dict[str, Any]] = []

        all_methods = set(list(recent_stats.keys()) + list(baseline_stats.keys()) + cls.DEFAULT_METHODS)

        for method in all_methods:
            b_total = baseline_stats.get(method, {}).get("total", 0)
            b_failed = baseline_stats.get(method, {}).get("failed", 0)
            r_total = recent_stats.get(method, {}).get("total", 0)
            r_failed = recent_stats.get(method, {}).get("failed", 0)

            # Baseline rate (min 3% default if small sample)
            b_rate = round(b_failed / b_total, 4) if b_total >= 5 else 0.035
            b_rate = max(b_rate, 0.03)

            if r_total >= 3:
                r_rate = round(r_failed / r_total, 4)
                spike_multiplier = round(r_rate / b_rate, 2) if b_rate > 0 else 1.0

                # Threshold: if failure rate >= 12% and spike >= 1.8x baseline
                if r_rate >= 0.12 and spike_multiplier >= 1.8:
                    severity = (
                        "CRITICAL" if spike_multiplier >= 4.0
                        else "HIGH" if spike_multiplier >= 2.5
                        else "MEDIUM"
                    )

                    anomaly_obj = {
                        "anomaly_type": "payment_degradation",
                        "payment_method": method,
                        "baseline_rate": b_rate,
                        "current_rate": r_rate,
                        "spike_multiplier": spike_multiplier,
                        "recent_failed_count": r_failed,
                        "recent_total_count": r_total,
                        "severity": severity,
                        "message": (
                            f"{method.upper()} failure rate spike detected (+{spike_multiplier}x normal baseline: "
                            f"{round(r_rate * 100, 1)}% vs {round(b_rate * 100, 1)}% baseline). "
                            "Autonomous payment link fallback active."
                        ),
                    }
                    detected_anomalies.append(anomaly_obj)

        has_anomaly = len(detected_anomalies) > 0
        primary_anomaly = detected_anomalies[0] if has_anomaly else None

        primary_message = (
            primary_anomaly["message"]
            if primary_anomaly
            else "All payment channels operating within normal historical baselines."
        )

        return {
            "has_anomaly": has_anomaly,
            "anomaly_count": len(detected_anomalies),
            "primary_message": primary_message,
            "primary_anomaly": primary_anomaly,
            "anomalies": detected_anomalies,
            "calculated_at": datetime.utcnow().isoformat(),
        }
