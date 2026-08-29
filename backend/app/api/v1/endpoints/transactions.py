from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.transaction import TransactionListItem, TransactionDetailResponse
from app.schemas.common import APIResponse, PaginatedResponse
from app.services.transaction_service import TransactionService

router = APIRouter()


@router.get("", response_model=APIResponse[PaginatedResponse[TransactionListItem]])
async def list_transactions(
    status: Optional[str] = Query(None, description="Filter by status: failed, pending, recovered, success"),
    payment_method: Optional[str] = Query(None, description="Filter by method: upi, card, netbanking, subscription"),
    search: Optional[str] = Query(None, description="Search by customer name, email, or transaction ID"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    items, total = await TransactionService.list_transactions(
        db=db,
        status=status,
        payment_method=payment_method,
        search=search,
        page=page,
        limit=limit,
    )
    total_pages = (total + limit - 1) // limit if limit > 0 else 1
    return APIResponse(
        success=True,
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
        ),
    )


@router.get("/{id}", response_model=APIResponse[TransactionDetailResponse])
async def get_transaction(
    id: str,
    db: AsyncSession = Depends(get_db),
):
    txn = await TransactionService.get_transaction(db=db, transaction_id=id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return APIResponse(success=True, data=txn)
