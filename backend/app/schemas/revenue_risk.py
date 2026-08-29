from typing import Optional
from pydantic import BaseModel


class RevenueRiskItem(BaseModel):
    id: str
    transaction_id: str
    amount: float
    currency: str
    customer_name: str
    payment_method: str
    risk_type: str
    risk_score: float
    detected_reason: str
    recovery_probability: float
    expected_recovery: float
    status: str
    created_at: str
