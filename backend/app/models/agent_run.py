from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, JSON, Index
import uuid
from app.core.database import Base


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(String(64), primary_key=True, default=lambda: f"run_{uuid.uuid4().hex[:12]}")
    transaction_id = Column(String(64), nullable=True, index=True)
    agent_name = Column(String(128), nullable=False, index=True)
    status = Column(String(32), default="running", nullable=False)  # running, success, failed, blocked
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    latency_ms = Column(Integer, default=0, nullable=False)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_agent_runs_status_created", "status", "started_at"),
    )
