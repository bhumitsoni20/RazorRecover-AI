# Payment Recovery Policy

## 1. Scope & Purpose
This policy document establishes standard operating rules for autonomous revenue recovery in merchant checkout operations. All automated recovery actions, risk assessments, and customer communication workflows must strictly comply with these rules.

---

## 2. UPI Failures
1. **Transient PSP Latency & Degradation**:
   - When UPI payment failures occur during an active PSP degradation window (e.g. failure rate spike > 3x normal baseline), automated direct retries are suspended.
   - For orders with transaction value <= INR 25,000, autonomous generation of a secure payment link is permitted.
   - Payment links must have an expiry window of 24 hours.
2. **Customer Intent Verification**:
   - Only customers with a historical success rate >= 60% or first-time customers with zero fraud risk flags are eligible for autonomous payment link recovery.
   - If customer has 0 successful payments and an elevated risk score (> 0.65), autonomous recovery is suppressed.

---

## 3. Gateway Degradation
1. **Active Gateway & Bank Outages**:
   - If payment failures occur due to gateway timeouts (`gateway_timeout`, `504_gateway_timeout`, `bank_unavailable`), the system must record the incident as technical degradation.
   - Autonomous retry or alternative checkout links may be issued if the degradation incident is confirmed by telemetry.
2. **Circuit Breaker Thresholds**:
   - If gateway failure rate exceeds 25% over a 15-minute rolling window, direct API retries must be paused immediately to prevent merchant gateway penalties.

---

## 4. Retry Policy
1. **Maximum Retry Attempts**:
   - A maximum of **2 automated retries** is permitted per transaction.
   - Transactions on attempt #3 or greater are strictly **BLOCKED** from further automated retries to protect customer experience and avoid gateway penalty fees.
2. **Backoff Intervals**:
   - Minimum backoff interval for Retry #1 is **15 minutes**.
   - Minimum backoff interval for Retry #2 is **60 minutes**.
3. **Strict Stopping Rules**:
   - Once a webhook confirms payment capture (`payment.captured` or `payment_link.paid`), all scheduled retries and reminders must be halted immediately.
   - Do NOT retry transactions failed due to `insufficient_funds` or `account_blocked` without waiting at least 12 hours.

---

## 5. Alternative Payment Methods
1. **Fallback Options**:
   - If a Card transaction fails due to OTP timeout or 3DS verification drop-off, recommend a UPI Deep-Link or QR option.
   - If a UPI payment fails due to bank-side degradation, recommend NetBanking or Card checkout options.
2. **Incentives & Waived Fees**:
   - Autonomous discount or waived convenience fee up to 10% (max INR 250) is allowed to incentivize payment completion.
   - Any discount > 10% requires human merchant approval.

---

## 6. High Value Transactions
1. **Human Review Threshold**:
   - Any transaction with gross amount **> INR 25,000** is classified as High Value.
   - Autonomous execution is prohibited for high-value transactions.
   - High-value transactions MUST be routed to the **Merchant Human Approval Queue** (`HUMAN_APPROVAL_REQUIRED`) before any payment link or communication is dispatched.
2. **Admin Authorization**:
   - The merchant administrator must review the AI root cause analysis and manually approve or reject the recovery action.

---

## 7. Customer History
1. **Trusted Customer Tier**:
   - Customers with historical success rate >= 80% and lifetime value >= INR 20,000 are eligible for accelerated autonomous recovery.
2. **High Risk Tier**:
   - Customers with a risk score > 0.65 or recent velocity anomalies (> 3 failed attempts in 10 minutes) must be flagged for manual fraud review.

---

## 8. Escalation
1. **Routing to Human Review**:
   - Transactions exceeding INR 25,000.
   - Transactions with ambiguous root cause or low AI model confidence (< 0.70).
   - Suspected fraud or disputed customer claims.
2. **Audit Requirement**:
   - All AI diagnoses, RAG policy matches, and admin approval actions must be logged immutably in the audit trail.
