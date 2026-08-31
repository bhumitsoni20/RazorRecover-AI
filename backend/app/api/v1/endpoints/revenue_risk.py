from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models.revenue_risk import RevenueRisk
from app.models.transaction import Transaction
from app.models.customer import Customer
from app.schemas.revenue_risk import (
    RevenueRiskSummaryResponse,
    PaginatedTransactionRiskResponse,
    RevenueRiskItem,
)
from app.schemas.root_cause import RootCauseAnalysis
from app.schemas.rag import PolicyContextResponse
from app.schemas.common import APIResponse
from app.services.revenue_risk import RevenueRiskService
from app.services.anomaly_detector import AnomalyDetectorService
from app.agents.root_cause_agent import root_cause_agent
from app.agents.rag_retriever import rag_retriever_agent

router = APIRouter()


@router.get("", response_model=APIResponse[RevenueRiskSummaryResponse])
@router.get("/summary", response_model=APIResponse[RevenueRiskSummaryResponse])
async def get_revenue_risk_summary(db: AsyncSession = Depends(get_db)):
    """
    Primary Phase 4 Revenue at Risk Summary Endpoint.
    Returns aggregated revenue at risk, average loss probability, leakage sources, and active anomaly alerts.
    """
    summary = await RevenueRiskService.get_revenue_risk_summary(db)
    return APIResponse(success=True, data=summary)


@router.get("/transactions", response_model=APIResponse[PaginatedTransactionRiskResponse])
async def get_transaction_risks(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level: LOW, MEDIUM, HIGH, CRITICAL"),
    db: AsyncSession = Depends(get_db),
):
    """
    Transaction-level risk scoring endpoint.
    Exposes individual transaction loss probabilities, expected loss amounts, risk levels, and explainable reasons.
    """
    result = await RevenueRiskService.get_transaction_risks(
        db=db,
        page=page,
        limit=limit,
        risk_level_filter=risk_level,
    )
    return APIResponse(success=True, data=result)


@router.get("/items", response_model=APIResponse[List[RevenueRiskItem]])
async def list_legacy_revenue_risks(db: AsyncSession = Depends(get_db)):
    """
    Legacy items endpoint for backward compatibility with existing components.
    """
    query = (
        select(RevenueRisk, Transaction, Customer)
        .join(Transaction, Transaction.id == RevenueRisk.transaction_id)
        .join(Customer, Customer.id == Transaction.customer_id)
        .order_by(desc(RevenueRisk.created_at))
        .limit(50)
    )
    results = (await db.execute(query)).all()

    items: List[RevenueRiskItem] = []
    for risk, txn, cust in results:
        items.append(
            RevenueRiskItem(
                id=risk.id,
                transaction_id=risk.transaction_id,
                amount=txn.amount,
                currency=txn.currency,
                customer_name=cust.name,
                payment_method=txn.payment_method,
                risk_type=risk.risk_type,
                risk_score=risk.risk_score,
                detected_reason=risk.detected_reason,
                recovery_probability=risk.recovery_probability,
                expected_recovery=risk.expected_recovery,
                status=risk.status,
                created_at=risk.created_at.strftime("%Y-%m-%d %H:%M:%S") if risk.created_at else "",
            )
        )


@router.get("/transactions/{transaction_id}/root-cause", response_model=APIResponse[RootCauseAnalysis])
async def get_transaction_root_cause(
    transaction_id: str = Path(..., description="Transaction ID to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """
    Phase 5 — Root Cause Agent Endpoint.
    Collects real transaction signals & Phase 4 anomaly telemetry and executes Gemini 2.5 Flash diagnosis.
    """
    query = (
        select(Transaction, Customer)
        .outerjoin(Customer, Customer.id == Transaction.customer_id)
        .where(Transaction.id == transaction_id)
    )
    res = (await db.execute(query)).first()
    if not res:
        raise HTTPException(status_code=404, detail=f"Transaction '{transaction_id}' not found.")

    txn, cust = res

    # Phase 4 Anomaly Telemetry
    anomaly_data = await AnomalyDetectorService.detect_payment_anomalies(db)
    method_key = txn.payment_method.lower() if txn.payment_method else "upi"
    anomalies_list = anomaly_data.get("anomalies", [])
    active_anomaly = next((a for a in anomalies_list if a.get("payment_method") == method_key), None)
    anomaly_payload = {
        "anomaly_detected": active_anomaly is not None,
        "anomaly_message": active_anomaly.get("message") if active_anomaly else None,
    }

    cust_success_rate = (
        (cust.successful_transactions / max(cust.total_transactions, 1))
        if cust and cust.total_transactions > 0
        else (0.916 if cust else None)
    )
    lifetime_txns = cust.total_transactions if cust else None

    result = await root_cause_agent.analyze(
        transaction_id=txn.id,
        amount=txn.amount,
        currency=txn.currency,
        payment_method=txn.payment_method,
        failure_reason=txn.failure_reason,
        failure_code=getattr(txn, "failure_code", None),
        attempt_count=txn.attempt_number,
        bank=txn.bank,
        customer_name=cust.name if cust else None,
        customer_success_rate=cust_success_rate,
        lifetime_transactions=lifetime_txns,
        anomaly_info=anomaly_payload,
    )
    return APIResponse(success=True, data=result)


@router.get("/transactions/{transaction_id}/policy-context", response_model=APIResponse[PolicyContextResponse])
async def get_transaction_policy_context(
    transaction_id: str = Path(..., description="Transaction ID for RAG retrieval"),
    db: AsyncSession = Depends(get_db),
):
    """
    Phase 6 — RAG Policy Context Endpoint.
    Retrieves matching sections from merchant_policy.md and generates policy-grounded interpretation.
    """
    query = (
        select(Transaction, Customer)
        .outerjoin(Customer, Customer.id == Transaction.customer_id)
        .where(Transaction.id == transaction_id)
    )
    res = (await db.execute(query)).first()
    if not res:
        raise HTTPException(status_code=404, detail=f"Transaction '{transaction_id}' not found.")

    txn, cust = res

    # Phase 4 Anomaly Telemetry
    anomaly_data = await AnomalyDetectorService.detect_payment_anomalies(db)
    method_key = txn.payment_method.lower() if txn.payment_method else "upi"
    anomalies_list = anomaly_data.get("anomalies", [])
    active_anomaly = next((a for a in anomalies_list if a.get("payment_method") == method_key), None)
    anomaly_payload = {
        "anomaly_detected": active_anomaly is not None,
        "anomaly_message": active_anomaly.get("message") if active_anomaly else None,
    }

    cust_success_rate = (
        (cust.successful_transactions / max(cust.total_transactions, 1))
        if cust and cust.total_transactions > 0
        else (0.916 if cust else None)
    )
    lifetime_txns = cust.total_transactions if cust else None

    # Root Cause Diagnosis first
    root_cause_res = await root_cause_agent.analyze(
        transaction_id=txn.id,
        amount=txn.amount,
        currency=txn.currency,
        payment_method=txn.payment_method,
        failure_reason=txn.failure_reason,
        failure_code=getattr(txn, "failure_code", None),
        attempt_count=txn.attempt_number,
        bank=txn.bank,
        customer_name=cust.name if cust else None,
        customer_success_rate=cust_success_rate,
        lifetime_transactions=lifetime_txns,
        anomaly_info=anomaly_payload,
    )

    # RAG Retrieval & Interpretation
    rag_result = await rag_retriever_agent.retrieve_policy_context(
        transaction_id=txn.id,
        root_cause=root_cause_res.root_cause,
        failure_reason=txn.failure_reason,
        payment_method=txn.payment_method,
        amount=txn.amount,
        attempt_count=txn.attempt_number,
        anomaly_info=anomaly_payload,
    )
    return APIResponse(success=True, data=rag_result)
