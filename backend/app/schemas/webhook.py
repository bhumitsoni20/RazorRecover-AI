from typing import Any, Dict, Optional
from pydantic import BaseModel


class RazorpayWebhookPayload(BaseModel):
    entity: str
    account_id: str
    event: str
    contains: list[str]
    payload: Dict[str, Any]
    created_at: int


class WebhookProcessingResult(BaseModel):
    event_id: str
    event_type: str
    status: str
    transaction_id: Optional[str] = None
    action_taken: str
    signature_verified: bool
    audit_logged: bool
