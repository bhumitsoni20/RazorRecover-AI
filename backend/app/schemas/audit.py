from typing import Any

from pydantic import BaseModel


class AuditLogItem(BaseModel):
    id: str
    transaction_id: str | None = None
    agent_name: str
    action: str
    reasoning_summary: str
    input_data: dict[str, Any] | None = None
    output_data: dict[str, Any] | None = None
    policy_result: str | None = None
    created_at: str
