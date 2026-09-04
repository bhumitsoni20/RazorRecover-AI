from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class RootCauseCategory(str, Enum):
    PAYMENT_METHOD_DEGRADATION = "payment_method_degradation"
    GATEWAY_FAILURE = "gateway_failure"
    BANK_FAILURE = "bank_failure"
    TIMEOUT = "timeout"
    INSUFFICIENT_FUNDS = "insufficient_funds"
    INVALID_PAYMENT_DETAILS = "invalid_payment_details"
    CUSTOMER_ABANDONMENT = "customer_abandonment"
    REPEATED_PAYMENT_FAILURE = "repeated_payment_failure"
    UNKNOWN = "unknown"


class RootCauseAnalysis(BaseModel):
    transaction_id: str
    root_cause: str
    confidence: float = Field(default=0.85, description="Model confidence between 0.0 and 1.0")
    evidence: list[str] = Field(default_factory=list, description="Evidence-first factual points based strictly on signals")
    explanation: str = Field(..., description="Explainable root cause diagnosis")
    signals_analyzed: dict[str, Any] | None = None
    analyzed_at: str | None = None

    @field_validator("confidence", mode="before")
    @classmethod
    def validate_confidence(cls, v: Any) -> float:
        try:
            val = float(v)
        except (ValueError, TypeError):
            return 0.5
        if val < 0.0:
            return 0.0
        if val > 1.0:
            return 1.0
        return round(val, 2)


class RootCauseRequest(BaseModel):
    transaction_id: str | None = None
