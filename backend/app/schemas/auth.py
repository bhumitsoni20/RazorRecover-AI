from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class SignupRequest(BaseModel):
    business_name: str = Field(..., min_length=2, max_length=255, description="Registered legal business name")
    owner_name: str = Field(..., min_length=2, max_length=255, description="Full name of business owner")
    email: EmailStr = Field(..., description="Unique merchant email address")
    password: str = Field(..., min_length=8, max_length=128, description="Strong password (min 8 chars)")
    confirm_password: str = Field(..., description="Password confirmation")

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Merchant account email")
    password: str = Field(..., min_length=1, description="Account password")


class MerchantResponse(BaseModel):
    id: str
    business_name: str
    owner_name: str
    email: str
    role: str
    currency: str
    razorpay_account_id: str | None = None
    razorpay_connection_status: str
    verification_status: str
    is_active: bool
    created_at: datetime
    last_login: datetime | None = None

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    merchant: MerchantResponse
    access_token: str
    token_type: str = "bearer"
    redirect_url: str


class ConnectRazorpayRequest(BaseModel):
    razorpay_account_id: str | None = Field(None, description="Optional Razorpay Merchant Account ID (acc_...)")


class DevVerifyRequest(BaseModel):
    verification_status: str | None = Field(None, description="Target status: VERIFIED, REJECTED, SUSPENDED, PENDING")
    status: str | None = Field(None, description="Alias for verification_status")
    reason: str | None = Field(None, description="Reason for verification status transition")
    notes: str | None = Field(None, description="Alias for reason")

    def get_status(self) -> str:
        s = self.verification_status or self.status or "VERIFIED"
        s_upper = s.upper()
        allowed = {"VERIFIED", "REJECTED", "SUSPENDED", "PENDING"}
        if s_upper not in allowed:
            raise ValueError(f"Status must be one of {allowed}")
        return s_upper

    def get_reason(self) -> str:
        return self.reason or self.notes or "Developer verification transition"



class VerificationStatusResponse(BaseModel):
    merchant_id: str
    business_name: str
    verification_status: str
    razorpay_connection_status: str
    razorpay_account_id: str | None = None
    can_access_dashboard: bool
    message: str
