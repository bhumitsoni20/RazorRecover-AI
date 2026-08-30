import hashlib
import json
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Index
import uuid
from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(64), primary_key=True, default=lambda: f"aud_{uuid.uuid4().hex[:12]}")
    transaction_id = Column(String(64), nullable=True, index=True)
    agent_name = Column(String(128), nullable=False, index=True)
    actor = Column(String(128), default="system", nullable=False)
    action = Column(String(128), nullable=False)
    reasoning_summary = Column(String(1000), nullable=False)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    policy_result = Column(String(64), nullable=True)
    previous_hash = Column(String(64), default="0" * 64, nullable=False)
    event_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("ix_audit_logs_agent_created", "agent_name", "created_at"),
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
    ) -> str:
        payload = f"{id_str}|{transaction_id or ''}|{agent_name}|{action}|{reasoning_summary}|{policy_result or ''}|{previous_hash}|{created_at_str}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
