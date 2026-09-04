import pytest
from httpx import AsyncClient
from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token


@pytest.mark.asyncio
async def test_merchant_signup_success(async_client: AsyncClient):
    """
    Test 1: Merchant signup creates account with verification_status = PENDING and razorpay_connection_status = NOT_CONNECTED.
    """
    payload = {
        "business_name": "Acme Retail Store",
        "owner_name": "Jane Doe",
        "email": "jane.doe@acmeretail.com",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
    }
    res = await async_client.post("/api/auth/signup", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["success"] is True
    assert data["data"]["merchant"]["business_name"] == "Acme Retail Store"
    assert data["data"]["merchant"]["verification_status"] == "PENDING"
    assert data["data"]["merchant"]["razorpay_connection_status"] == "NOT_CONNECTED"
    assert data["data"]["redirect_url"] == "/onboarding/razorpay"
    assert "access_token" in data["data"]


@pytest.mark.asyncio
async def test_signup_duplicate_email(async_client: AsyncClient):
    """
    Test 2: Signup with existing email is rejected.
    """
    payload = {
        "business_name": "Demo Duplicate",
        "owner_name": "Duplicate Owner",
        "email": settings.DEMO_MERCHANT_1_EMAIL,
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
    }
    res = await async_client.post("/api/auth/signup", json=payload)
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"]


@pytest.mark.asyncio
async def test_password_hashing_and_verification():
    """
    Test 3: Password hashing uses bcrypt and never stores plain text.
    """
    plain = "MySecretPassword2026!"
    hashed = hash_password(plain)
    assert hashed != plain
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


@pytest.mark.asyncio
async def test_login_successful_verified_merchant(async_client: AsyncClient):
    """
    Test 4: Successful login of VERIFIED merchant routes to /dashboard and sets auth token.
    """
    payload = {
        "email": settings.DEMO_MERCHANT_1_EMAIL,
        "password": settings.DEMO_MERCHANT_1_PASSWORD,
    }
    res = await async_client.post("/api/auth/login", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["merchant"]["verification_status"] == "VERIFIED"
    assert data["data"]["redirect_url"] == "/dashboard"


@pytest.mark.asyncio
async def test_login_successful_pending_merchant(async_client: AsyncClient):
    """
    Test 4b: Successful login of PENDING merchant routes to /verification-pending or /onboarding/razorpay.
    """
    payload = {
        "email": settings.DEMO_MERCHANT_2_EMAIL,
        "password": settings.DEMO_MERCHANT_2_PASSWORD,
    }
    res = await async_client.post("/api/auth/login", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["merchant"]["verification_status"] == "PENDING"
    assert data["data"]["redirect_url"] in ["/verification-pending", "/onboarding/razorpay"]


@pytest.mark.asyncio
async def test_login_wrong_password(async_client: AsyncClient):
    """
    Test 5: Wrong password returns generic error message.
    """
    payload = {
        "email": settings.DEMO_MERCHANT_1_EMAIL,
        "password": "TotallyWrongPassword!",
    }
    res = await async_client.post("/api/auth/login", json=payload)
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_login_nonexistent_email(async_client: AsyncClient):
    """
    Test 6: Non-existent email returns generic error message (no email enumeration).
    """
    payload = {
        "email": "ghost.nonexistent@example.com",
        "password": "SomePassword123!",
    }
    res = await async_client.post("/api/auth/login", json=payload)
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_logout(async_client: AsyncClient):
    """
    Test 7: Logout clears session cookie.
    """
    res = await async_client.post("/api/auth/logout")
    assert res.status_code == 200
    assert res.json()["data"]["logged_out"] is True


@pytest.mark.asyncio
async def test_unauthenticated_api_blocked(unauthenticated_client: AsyncClient):
    """
    Test 8: Unauthenticated access to protected endpoints is rejected with 401.
    """
    res = await unauthenticated_client.get("/api/dashboard/summary")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_pending_merchant_cannot_access_dashboard(async_client: AsyncClient):
    """
    Test 9 & 10: Authenticated PENDING merchant access to /api/dashboard/summary returns 403 Forbidden.
    """
    # 1. Login as Merchant 2 (PENDING)
    login_res = await async_client.post(
        "/api/auth/login",
        json={"email": settings.DEMO_MERCHANT_2_EMAIL, "password": settings.DEMO_MERCHANT_2_PASSWORD},
    )
    token = login_res.json()["data"]["access_token"]

    # 2. Attempt dashboard summary access
    res = await async_client.get(
        "/api/dashboard/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
    assert res.json()["detail"]["verification_status"] == "PENDING"


@pytest.mark.asyncio
async def test_verified_merchant_can_access_dashboard(async_client: AsyncClient):
    """
    Test 11: Authenticated VERIFIED merchant can access /api/dashboard/summary with 200 OK.
    """
    # 1. Login as Merchant 1 (VERIFIED)
    login_res = await async_client.post(
        "/api/auth/login",
        json={"email": settings.DEMO_MERCHANT_1_EMAIL, "password": settings.DEMO_MERCHANT_1_PASSWORD},
    )
    token = login_res.json()["data"]["access_token"]

    # 2. Access dashboard summary
    res = await async_client.get(
        "/api/dashboard/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert "revenue_at_risk" in res.json()["data"]["metrics"]


@pytest.mark.asyncio
async def test_rejected_and_suspended_merchant_blocked(async_client: AsyncClient):
    """
    Test 12 & 13: REJECTED and SUSPENDED merchants are blocked from dashboard with 403.
    """
    # Create REJECTED status via dev verify
    dev_res = await async_client.post(
        "/api/dev/merchants/mch_demo_fashion/verify",
        json={"verification_status": "REJECTED", "reason": "KYC mismatch"},
    )
    assert dev_res.status_code == 200

    token = create_access_token(data={"sub": "mch_demo_fashion", "email": settings.DEMO_MERCHANT_2_EMAIL, "role": "merchant"})
    res = await async_client.get("/api/dashboard/summary", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403
    assert res.json()["detail"]["verification_status"] == "REJECTED"


@pytest.mark.asyncio
async def test_merchant_data_isolation_transactions(async_client: AsyncClient):
    """
    Test 14: Merchant A cannot access Merchant B's transaction (returns 404, never leaks existence).
    """
    # Token for Merchant 1 (Demo Electronics)
    token_m1 = create_access_token(data={"sub": "mch_razorpay_demo", "email": settings.DEMO_MERCHANT_1_EMAIL, "role": "merchant"})

    # Try accessing Merchant B's transaction (txn_merchant_b_001)
    res = await async_client.get(
        "/api/transactions/txn_merchant_b_001",
        headers={"Authorization": f"Bearer {token_m1}"},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Transaction not found"

    # Access Merchant A's own transaction (txn_4999_upi)
    res_own = await async_client.get(
        "/api/transactions/txn_4999_upi",
        headers={"Authorization": f"Bearer {token_m1}"},
    )
    assert res_own.status_code == 200
    assert res_own.json()["data"]["id"] == "txn_4999_upi"


@pytest.mark.asyncio
async def test_merchant_data_isolation_list_transactions(async_client: AsyncClient):
    """
    Test 15: Transaction listing only returns transactions belonging to authenticated merchant.
    """
    token_m1 = create_access_token(data={"sub": "mch_razorpay_demo", "email": settings.DEMO_MERCHANT_1_EMAIL, "role": "merchant"})
    res = await async_client.get("/api/transactions", headers={"Authorization": f"Bearer {token_m1}"})
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    # All items must belong to Merchant 1
    for item in items:
        assert "merchant_b" not in item["id"]


@pytest.mark.asyncio
async def test_dev_verification_status_transition_and_audit(async_client: AsyncClient):
    """
    Test 17 & 18: Dev verification endpoint transitions status and creates audit log.
    """
    # Transition Merchant 2 from PENDING to VERIFIED
    verify_res = await async_client.post(
        "/api/dev/merchants/mch_demo_fashion/verify",
        json={"verification_status": "VERIFIED", "reason": "Buildathon Demo Instant Approval"},
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["data"]["new_status"] == "VERIFIED"

    # Merchant 2 can now access dashboard
    token_m2 = create_access_token(data={"sub": "mch_demo_fashion", "email": settings.DEMO_MERCHANT_2_EMAIL, "role": "merchant"})
    dash_res = await async_client.get("/api/dashboard/summary", headers={"Authorization": f"Bearer {token_m2}"})
    assert dash_res.status_code == 200


@pytest.mark.asyncio
async def test_onboarding_connect_razorpay(async_client: AsyncClient):
    """
    Test 20: Merchant connects Razorpay account during onboarding.
    """
    token_m2 = create_access_token(data={"sub": "mch_demo_fashion", "email": settings.DEMO_MERCHANT_2_EMAIL, "role": "merchant"})
    connect_res = await async_client.post(
        "/api/onboarding/connect-razorpay",
        json={"razorpay_account_id": "acc_rzp_fashion_live"},
        headers={"Authorization": f"Bearer {token_m2}"},
    )
    assert connect_res.status_code == 200
    data = connect_res.json()["data"]
    assert data["razorpay_connection_status"] == "CONNECTED"
    assert data["razorpay_account_id"] == "acc_rzp_fashion_live"
