export type VerificationStatus = "PENDING" | "VERIFIED" | "REJECTED" | "SUSPENDED";
export type RazorpayConnectionStatus = "NOT_CONNECTED" | "CONNECTED" | "DISCONNECTED";
export type UserRole = "merchant" | "admin";

export interface MerchantUser {
  id: string;
  business_name: string;
  owner_name: string;
  email: string;
  role: UserRole;
  currency: string;
  razorpay_account_id?: string | null;
  razorpay_connection_status: RazorpayConnectionStatus;
  verification_status: VerificationStatus;
  verification_notes?: string | null;
  is_active: boolean;
  created_at?: string;
  last_login?: string | null;
}

export interface AuthResponse {
  merchant: MerchantUser;
  access_token: string;
  token_type: string;
  redirect_url: string;
}

export interface VerificationStatusResponse {
  merchant_id: string;
  business_name: string;
  verification_status: VerificationStatus;
  razorpay_connection_status: RazorpayConnectionStatus;
  razorpay_account_id?: string | null;
  can_access_dashboard: boolean;
  message: string;
  next_step: string;
}
