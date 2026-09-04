import hashlib
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"aud_{uuid.uuid4().hex[:12]}")
    merchant_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=True, index=True)
    transaction_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    agent_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    actor: Mapped[str] = mapped_column(String(128), default="system", nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    reasoning_summary: Mapped[str] = mapped_column(String(1000), nullable=False)
    input_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    output_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    policy_result: Mapped[str | None] = mapped_column(String(64), nullable=True)
    previous_hash: Mapped[str] = mapped_column(String(64), default="0" * 64, nullable=False)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    merchant = relationship("Merchant", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_logs_agent_created", "agent_name", "created_at"),
        Index("ix_audit_logs_merchant_created", "merchant_id", "created_at"),
    )

    @classmethod
    def calculate_hash(
        cls,
        id_str: str,
        transaction_id: str | None,
        agent_name: str,
        action: str,
        reasoning_summary: str,
        policy_result: str | None,
        previous_hash: str,
        created_at_str: str,
        merchant_id: str | None = None,
    ) -> str:
        payload = f"{id_str}|{merchant_id or ''}|{transaction_id or ''}|{agent_name}|{action}|{reasoning_summary}|{policy_result or ''}|{previous_hash}|{created_at_str}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
