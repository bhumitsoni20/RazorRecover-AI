from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base


class RevenueRisk(Base):
    __tablename__ = "revenue_risks"

    id = Column(String(64), primary_key=True, default=lambda: f"risk_{uuid.uuid4().hex[:12]}")
    transaction_id = Column(String(64), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    risk_type = Column(String(64), nullable=False)  # payment_failure, checkout_abandonment, subscription_churn, invoice_overdue
    risk_score = Column(Float, nullable=False)  # 0.0 to 1.0 (higher = riskier / critical)
    detected_reason = Column(String(255), nullable=False)
    recovery_probability = Column(Float, nullable=False)  # 0.0 to 1.0
    expected_recovery = Column(Float, nullable=False)  # amount * recovery_probability
    status = Column(String(32), default="detected", nullable=False)  # detected, investigating, action_scheduled, in_progress, recovered, unrecoverable
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    transaction = relationship("Transaction", back_populates="revenue_risk")
