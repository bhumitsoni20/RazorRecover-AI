import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"txn_{uuid.uuid4().hex[:12]}")
    merchant_id: Mapped[str] = mapped_column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(64), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    payment_method: Mapped[str] = mapped_column(String(64), nullable=False)  # upi, card, netbanking, subscription, wallet
    payment_gateway: Mapped[str] = mapped_column(String(64), default="razorpay", nullable=False)
    bank: Mapped[str | None] = mapped_column(String(64), nullable=True)  # HDFC, ICICI, SBI, AXIS, etc.
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # success, failed, pending, recovered, abandoned
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)  # upi_timeout, bank_degraded, insufficient_funds, etc.
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    razorpay_order_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    merchant = relationship("Merchant", back_populates="transactions")
    customer = relationship("Customer", back_populates="transactions")
    revenue_risk = relationship("RevenueRisk", back_populates="transaction", uselist=False, cascade="all, delete-orphan")
    recovery_actions = relationship("RecoveryAction", back_populates="transaction", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_transactions_status_created", "status", "created_at"),
    )
