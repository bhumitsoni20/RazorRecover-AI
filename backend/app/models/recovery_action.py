import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.transaction import Transaction


class RecoveryAction(Base):
    __tablename__ = "recovery_actions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"act_{uuid.uuid4().hex[:12]}")
    transaction_id: Mapped[str] = mapped_column(String(64), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)  # payment_link, retry, reminder, alternative_payment_method, human_review, do_nothing
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 to 1.0
    policy_decision: Mapped[str] = mapped_column(String(64), nullable=False)  # APPROVED, HUMAN_APPROVAL_REQUIRED, BLOCKED
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)  # pending, executing, executed, verified, recovered, failed, cancelled
    amount_recovered: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    external_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)  # razorpay payment link ID or transfer ID
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    transaction: Mapped["Transaction"] = relationship("Transaction", back_populates="recovery_actions")

    __table_args__ = (
        Index("ix_recovery_actions_status_created", "status", "created_at"),
    )
