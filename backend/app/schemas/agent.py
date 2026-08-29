from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class AgentStatusCard(BaseModel):
    name: str
    role: str
    status: str  # active, idle, degraded
    total_runs: int
    success_rate: float
    avg_latency_ms: int
    last_run_at: str


class AgentRunItem(BaseModel):
    id: str
    transaction_id: Optional[str] = None
    agent_name: str
    status: str
    started_at: str
    completed_at: Optional[str] = None
    latency_ms: int
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None


class AgentsOverviewResponse(BaseModel):
    agents: List[AgentStatusCard]
    recent_runs: List[AgentRunItem]
