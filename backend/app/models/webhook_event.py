from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    event_id: Mapped[str] = mapped_column(String(128), primary_key=True, index=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    signature_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("ix_webhook_events_type_created", "event_type", "created_at"),
    )
