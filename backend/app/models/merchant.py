import uuid
from datetime import datetime, timezone
from typing import cast

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"mch_{uuid.uuid4().hex[:12]}")
    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_name: Mapped[str] = mapped_column(String(255), default="Merchant Owner", nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="merchant", nullable=False)  # merchant, admin
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    razorpay_account_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    razorpay_connection_status: Mapped[str] = mapped_column(String(32), default="NOT_CONNECTED", nullable=False)  # NOT_CONNECTED, CONNECTED, DISCONNECTED
    verification_status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)  # PENDING, VERIFIED, REJECTED, SUSPENDED
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

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
        self.business_name = val
