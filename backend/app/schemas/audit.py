from typing import Any, Dict, Optional
from pydantic import BaseModel


class AuditLogItem(BaseModel):
    id: str
    transaction_id: Optional[str] = None
    agent_name: str
    action: str
    reasoning_summary: str
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    policy_result: Optional[str] = None
    created_at: str
