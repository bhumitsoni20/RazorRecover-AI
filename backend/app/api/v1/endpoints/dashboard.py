from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.dashboard import DashboardSummaryResponse
from app.schemas.common import APIResponse
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/summary", response_model=APIResponse[DashboardSummaryResponse])
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    data = await DashboardService.get_summary(db)
    return APIResponse(success=True, data=data)
