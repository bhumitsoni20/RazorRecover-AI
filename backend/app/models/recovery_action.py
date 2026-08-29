from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base


class RecoveryAction(Base):
    __tablename__ = "recovery_actions"

    id = Column(String(64), primary_key=True, default=lambda: f"act_{uuid.uuid4().hex[:12]}")
    transaction_id = Column(String(64), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type = Column(String(64), nullable=False)  # payment_link, retry, reminder, alternative_payment_method, human_review, do_nothing
    reason = Column(String(500), nullable=False)
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    policy_decision = Column(String(64), nullable=False)  # APPROVED, HUMAN_APPROVAL_REQUIRED, BLOCKED
    status = Column(String(32), default="pending", nullable=False)  # pending, executing, executed, verified, recovered, failed, cancelled
    amount_recovered = Column(Float, default=0.0, nullable=False)
    external_reference = Column(String(255), nullable=True)  # razorpay payment link ID or transfer ID
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)

    transaction = relationship("Transaction", back_populates="recovery_actions")

    __table_args__ = (
        Index("ix_recovery_actions_status_created", "status", "created_at"),
    )
