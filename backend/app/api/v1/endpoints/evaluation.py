from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.evaluation import EvaluationMetricsResponse
from app.schemas.common import APIResponse
from app.services.evaluation_service import EvaluationService

router = APIRouter()


@router.get("/metrics", response_model=APIResponse[EvaluationMetricsResponse])
async def get_evaluation_metrics(db: AsyncSession = Depends(get_db)):
    metrics = await EvaluationService.get_metrics(db)
    return APIResponse(success=True, data=metrics)
