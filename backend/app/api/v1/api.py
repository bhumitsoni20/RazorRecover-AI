from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    onboarding,
    dev,
    dashboard,
    transactions,
    revenue_risk,
    recovery,
    audit,
    agents,
    evaluation,
    webhooks,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["Merchant Onboarding"])
api_router.include_router(dev.router, prefix="/dev", tags=["Development Tools"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
api_router.include_router(revenue_risk.router, prefix="/revenue-risk", tags=["Revenue Risk"])
api_router.include_router(recovery.router, prefix="/recovery", tags=["Recovery Actions"])
api_router.include_router(audit.router, prefix="/audit-logs", tags=["Audit Logs"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_router.include_router(evaluation.router, prefix="/evaluation", tags=["Evaluation"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
