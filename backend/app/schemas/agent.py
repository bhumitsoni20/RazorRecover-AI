from typing import Any

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
    transaction_id: str | None = None
    agent_name: str
    status: str
    started_at: str
    completed_at: str | None = None
    latency_ms: int
    input_data: dict[str, Any] | None = None
    output_data: dict[str, Any] | None = None


class AgentsOverviewResponse(BaseModel):
    agents: list[AgentStatusCard]
    recent_runs: list[AgentRunItem]
