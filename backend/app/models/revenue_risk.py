import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RevenueRisk(Base):
    __tablename__ = "revenue_risks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"risk_{uuid.uuid4().hex[:12]}")
    transaction_id: Mapped[str] = mapped_column(String(64), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    risk_type: Mapped[str] = mapped_column(String(64), nullable=False)  # payment_failure, checkout_abandonment, subscription_churn, invoice_overdue
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 to 1.0 (higher = riskier / critical)
    detected_reason: Mapped[str] = mapped_column(String(255), nullable=False)
    recovery_probability: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 to 1.0
    expected_recovery: Mapped[float] = mapped_column(Float, nullable=False)  # amount * recovery_probability
    status: Mapped[str] = mapped_column(String(32), default="detected", nullable=False)  # detected, investigating, action_scheduled, in_progress, recovered, unrecoverable
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    transaction = relationship("Transaction", back_populates="revenue_risk")
