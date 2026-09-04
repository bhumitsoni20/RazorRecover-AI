import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MerchantPolicy(Base):
    __tablename__ = "merchant_policies"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"pol_{uuid.uuid4().hex[:12]}")
    merchant_id: Mapped[str] = mapped_column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    policy_name: Mapped[str] = mapped_column(String(255), nullable=False)
    policy_type: Mapped[str] = mapped_column(String(64), nullable=False)  # retry_limit, amount_threshold, payment_link_rule, discount_limit, fraud_rule
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    merchant = relationship("Merchant", back_populates="policies")
