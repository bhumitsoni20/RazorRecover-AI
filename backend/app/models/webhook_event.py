from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, JSON, Index
from app.core.database import Base


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    event_id = Column(String(128), primary_key=True, index=True)
    event_type = Column(String(128), nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    signature_valid = Column(Boolean, default=True, nullable=False)
    processed = Column(Boolean, default=False, nullable=False, index=True)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("ix_webhook_events_type_created", "event_type", "created_at"),
    )
