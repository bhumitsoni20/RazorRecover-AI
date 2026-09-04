from datetime import datetime
from typing import cast
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base


class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(String(64), primary_key=True, default=lambda: f"mch_{uuid.uuid4().hex[:12]}")
    business_name = Column(String(255), nullable=False)
    owner_name = Column(String(255), default="Merchant Owner", nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(32), default="merchant", nullable=False)  # merchant, admin
    currency = Column(String(10), default="INR", nullable=False)
    razorpay_account_id = Column(String(128), nullable=True)
    razorpay_connection_status = Column(String(32), default="NOT_CONNECTED", nullable=False)  # NOT_CONNECTED, CONNECTED, DISCONNECTED
    verification_status = Column(String(32), default="PENDING", nullable=False)  # PENDING, VERIFIED, REJECTED, SUSPENDED
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    customers = relationship("Customer", back_populates="merchant", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="merchant", cascade="all, delete-orphan")
    policies = relationship("MerchantPolicy", back_populates="merchant", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="merchant", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        # Support name as alias for business_name for backward compatibility
        if "name" in kwargs and "business_name" not in kwargs:
            kwargs["business_name"] = kwargs.pop("name")
        if "business_name" in kwargs and "owner_name" not in kwargs:
            kwargs["owner_name"] = kwargs.get("owner_name", "Merchant Owner")
        if "email" not in kwargs:
            kwargs["email"] = f"{kwargs.get('id', 'merchant')}@example.com"
        if "password_hash" not in kwargs:
            # Default fallback hash if not supplied in test constructor
            from app.core.security import hash_password
            kwargs["password_hash"] = hash_password("DemoPassword123!")
        super().__init__(**kwargs)

    @property
    def name(self) -> str:
        return cast(str, self.business_name)

    @name.setter
    def name(self, val: str):
        setattr(self, "business_name", val)

