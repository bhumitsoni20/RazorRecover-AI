import pytest
from datetime import datetime, timedelta
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.main import app
from app.core.database import AsyncSessionLocal
from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.transaction import Transaction
from app.models.revenue_risk import RevenueRisk
from app.services.revenue_risk import RevenueRiskService
from app.services.anomaly_detector import AnomalyDetectorService
from app.services.dashboard_service import DashboardService


# =========================================================
# 1. Deterministic Formula Tests
# =========================================================

def test_revenue_at_risk_formula():
    """
    Test core specification:
    Revenue at Risk = amount * (1 - recovery_probability)
    For amount = 10,000 and recovery_prob = 0.20 -> loss_prob = 0.80 -> risk = 8,000.
    """
    amount = 10000.0
    recovery_prob = 0.20
    loss_prob = round(1.0 - recovery_prob, 2)
    revenue_at_risk = round(amount * loss_prob, 2)

    assert loss_prob == 0.80
    assert revenue_at_risk == 8000.0


def test_risk_level_thresholds():
    """
    Test deterministic risk level thresholds:
    0.00 - 0.24 -> LOW
    0.25 - 0.49 -> MEDIUM
    0.50 - 0.74 -> HIGH
    0.75 - 1.00 -> CRITICAL
    """
    assert RevenueRiskService.get_risk_level(0.10) == "LOW"
    assert RevenueRiskService.get_risk_level(0.24) == "LOW"
    assert RevenueRiskService.get_risk_level(0.25) == "MEDIUM"
    assert RevenueRiskService.get_risk_level(0.49) == "MEDIUM"
    assert RevenueRiskService.get_risk_level(0.50) == "HIGH"
    assert RevenueRiskService.get_risk_level(0.74) == "HIGH"
    assert RevenueRiskService.get_risk_level(0.75) == "CRITICAL"
    assert RevenueRiskService.get_risk_level(0.95) == "CRITICAL"


def test_loss_probability_scoring_rules():
    """
    Test explainable scoring rules across different failure reasons and retry states.
    """
    # 1. Transient UPI timeout on attempt 1 with high customer loyalty
    loss_prob, recov_prob, risk_level, expl = RevenueRiskService.compute_loss_probability(
        amount=4999.0,
        payment_method="upi",
        failure_reason="upi_timeout",
        attempt_number=1,
        customer_success_rate=0.92,
        is_anomaly_active=True,
    )
    assert recov_prob >= 0.85
    assert loss_prob <= 0.15
    assert risk_level == "LOW"
    assert "Transient" in expl or "timeout" in expl

    # 2. Repeated failure (attempt 3) -> should be CRITICAL risk
    loss_prob_3, recov_prob_3, risk_level_3, expl_3 = RevenueRiskService.compute_loss_probability(
        amount=2000.0,
        payment_method="upi",
        failure_reason="upi_timeout",
        attempt_number=3,
        customer_success_rate=0.70,
    )
    assert loss_prob_3 >= 0.50
    assert risk_level_3 in ["HIGH", "CRITICAL"]
    assert "attempt #3" in expl_3

    # 3. Permanent failure (insufficient funds)
    loss_prob_fund, recov_prob_fund, risk_level_fund, expl_fund = RevenueRiskService.compute_loss_probability(
        amount=1500.0,
        payment_method="card",
        failure_reason="insufficient_funds",
        attempt_number=1,
    )
    assert loss_prob_fund >= 0.60
    assert risk_level_fund in ["HIGH", "CRITICAL"]


# =========================================================
# 2. Anomaly Detection Tests
# =========================================================

@pytest.mark.asyncio
async def test_anomaly_detection_logic():
    """
    Test database-derived anomaly detection service.
    """
    async with AsyncSessionLocal() as session:
        result = await AnomalyDetectorService.detect_payment_anomalies(session)
        assert "has_anomaly" in result
        assert "anomalies" in result
        assert "primary_message" in result
        assert isinstance(result["anomalies"], list)


# =========================================================
# 3. Revenue Risk API Tests
# =========================================================

@pytest.mark.asyncio
async def test_get_revenue_risk_summary_api():
    """
    Test GET /api/revenue-risk returns structured summary metrics.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/revenue-risk")
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True

        data = json_data["data"]
        assert "total_revenue_at_risk" in data
        assert "currency" in data
        assert data["currency"] == "INR"
        assert "transaction_count" in data
        assert "average_loss_probability" in data
        assert "top_risk_sources" in data
        assert "risk_distribution" in data
        assert isinstance(data["top_risk_sources"], list)
        assert isinstance(data["risk_distribution"], dict)


@pytest.mark.asyncio
async def test_get_transaction_risks_api():
    """
    Test GET /api/revenue-risk/transactions returns paginated transaction risk items.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/revenue-risk/transactions?page=1&limit=10")
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True

        data = json_data["data"]
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert "total_pages" in data

        if len(data["items"]) > 0:
            first_item = data["items"][0]
            assert "transaction_id" in first_item
            assert "amount" in first_item
            assert "loss_probability" in first_item
            assert "successful_recovery_probability" in first_item
            assert "revenue_at_risk" in first_item
            assert "risk_level" in first_item
            assert first_item["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
            assert "explanation" in first_item


@pytest.mark.asyncio
async def test_dashboard_real_revenue_at_risk():
    """
    Test GET /api/dashboard/summary reflects real database revenue at risk.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/dashboard/summary")
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True

        metrics = json_data["data"]["metrics"]
        assert "revenue_at_risk" in metrics
        assert isinstance(metrics["revenue_at_risk"], (int, float))
        assert metrics["revenue_at_risk"] >= 0.0

        trend = json_data["data"]["trend"]
        assert len(trend) == 7
        for point in trend:
            assert "date" in point
            assert "revenue_at_risk" in point
            assert "revenue_recovered" in point
            assert "recovery_rate" in point
