from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.evaluation import (
    EvaluationMetricsResponse,
    EndToEndEvaluationResponse,
    GuardrailTestSuiteResponse,
)
from app.schemas.common import APIResponse
from app.services.evaluation_service import EvaluationService

router = APIRouter()


@router.get("/metrics", response_model=APIResponse[EvaluationMetricsResponse])
async def get_evaluation_metrics(db: AsyncSession = Depends(get_db)):
    """
    Returns real-time dynamic evaluation metrics & agent performance computed from live database records.
    """
    metrics = await EvaluationService.get_metrics(db)
    return APIResponse(success=True, data=metrics)


@router.post("/run-e2e", response_model=APIResponse[EndToEndEvaluationResponse])
async def run_end_to_end_evaluation(
    payload: dict = Body(default={"transaction_id": "txn_4999_upi"}),
    db: AsyncSession = Depends(get_db),
):
    """
    Executes a complete 11-step end-to-end evaluation through the live multi-agent recovery pipeline.
    """
    tx_id = payload.get("transaction_id", "txn_4999_upi")
    result = await EvaluationService.run_end_to_end_evaluation(db, transaction_id=tx_id)
    return APIResponse(success=True, data=result)


@router.post("/run-guardrails", response_model=APIResponse[GuardrailTestSuiteResponse])
async def run_guardrail_test_suite():
    """
    Executes the 7 automated policy & guardrail boundary test cases.
    """
    suite_result = EvaluationService.run_guardrail_test_suite()
    return APIResponse(success=True, data=suite_result)
