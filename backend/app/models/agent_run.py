import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"run_{uuid.uuid4().hex[:12]}")
    transaction_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    agent_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="running", nullable=False)  # running, success, failed, blocked
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    input_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    output_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_agent_runs_status_created", "status", "started_at"),
    )
