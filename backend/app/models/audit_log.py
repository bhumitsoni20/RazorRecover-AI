from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Index
import uuid
from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(64), primary_key=True, default=lambda: f"aud_{uuid.uuid4().hex[:12]}")
    transaction_id = Column(String(64), nullable=True, index=True)
    agent_name = Column(String(128), nullable=False, index=True)  # DetectionAgent, RootCauseAgent, StrategyAgent, PolicyEngine, ActionAgent, WebhookVerifier
    action = Column(String(128), nullable=False)
    reasoning_summary = Column(String(1000), nullable=False)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    policy_result = Column(String(64), nullable=True)  # APPROVED, BLOCKED, HUMAN_APPROVAL_REQUIRED, PASSED
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("ix_audit_logs_agent_created", "agent_name", "created_at"),
    )
