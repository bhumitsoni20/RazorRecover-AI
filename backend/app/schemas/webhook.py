from typing import Any

from pydantic import BaseModel


class RazorpayWebhookPayload(BaseModel):
    entity: str
    account_id: str
    event: str
    contains: list[str]
    payload: dict[str, Any]
    created_at: int


class WebhookProcessingResult(BaseModel):
    event_id: str
    event_type: str
    status: str
    transaction_id: str | None = None
    action_taken: str
    signature_verified: bool
    audit_logged: bool
