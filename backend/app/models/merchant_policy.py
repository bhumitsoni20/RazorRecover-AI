from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base


class MerchantPolicy(Base):
    __tablename__ = "merchant_policies"

    id = Column(String(64), primary_key=True, default=lambda: f"pol_{uuid.uuid4().hex[:12]}")
    merchant_id = Column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    policy_name = Column(String(255), nullable=False)
    policy_type = Column(String(64), nullable=False)  # retry_limit, amount_threshold, payment_link_rule, discount_limit, fraud_rule
    configuration = Column(JSON, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    merchant = relationship("Merchant", back_populates="policies")
