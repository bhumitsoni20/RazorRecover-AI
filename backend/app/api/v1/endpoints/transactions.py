
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_verified_merchant
from app.core.database import get_db
from app.models.merchant import Merchant
from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.transaction import TransactionDetailResponse, TransactionListItem
from app.services.transaction_service import TransactionService

router = APIRouter()


@router.get("", response_model=APIResponse[PaginatedResponse[TransactionListItem]])
async def list_transactions(
    status: str | None = Query(None, description="Filter by status: failed, pending, recovered, success"),
    payment_method: str | None = Query(None, description="Filter by method: upi, card, netbanking, subscription"),
    search: str | None = Query(None, description="Search by customer name, email, or transaction ID"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_merchant: Merchant = Depends(get_current_verified_merchant),
    db: AsyncSession = Depends(get_db),
):
    """
    List transactions belonging strictly to the authenticated verified merchant.
    """
    items, total = await TransactionService.list_transactions(
        db=db,
        merchant_id=current_merchant.id,
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
    current_merchant: Merchant = Depends(get_current_verified_merchant),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve transaction details strictly verifying ownership by the authenticated merchant.
    Returns 404 if not found or belongs to another merchant.
    """
    txn = await TransactionService.get_transaction(
        db=db,
        transaction_id=id,
        merchant_id=current_merchant.id,
    )
    if not txn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    return APIResponse(success=True, data=txn)
