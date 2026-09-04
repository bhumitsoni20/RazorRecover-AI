import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_check_endpoint(async_client):
    response = await async_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "razorrecover-backend"


@pytest.mark.asyncio
async def test_dashboard_summary_endpoint(async_client):
    response = await async_client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "metrics" in data["data"]
    assert "trend" in data["data"]


@pytest.mark.asyncio
async def test_evaluation_metrics_endpoint(async_client):
    response = await async_client.get("/api/evaluation/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["overall_recovery_rate"] >= 0
    assert "category_breakdown" in data["data"]

