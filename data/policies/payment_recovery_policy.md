# RazorRecover AI - Merchant Revenue Recovery Policy & Guardrail Specifications

## 1. Scope & Purpose
This policy document governs automated and assisted payment recovery actions taken by the RazorRecover AI multi-agent system on behalf of the merchant. All autonomous actions, recommendations, and execution dispatchers must adhere strictly to these deterministic rules and guardrails.

---

## 2. Recovery Action Types & Eligibility

### 2.1 Automated Payment Links (`payment_link`)
- **Eligibility**:
  - Payment failure caused by UPI degradation, gateway timeouts, bank network drops, or checkout session expiry.
  - Customer historical success rate >= 60% OR new customer with no prior fraud flags.
  - Transaction amount <= INR 25,000 for autonomous generation.
  - Maximum 1 payment link per failed transaction attempt.
  - Expiry window: Standard 24 hours (1440 minutes).
- **Ineligibility**:
  - Suspected fraud or high risk score (> 0.75).
  - Explicit customer cancellation / user abort without intent to retry.

### 2.2 Automated Payment Retries (`retry`)
- **Eligibility**:
  - Technical failures: temporary network timeout (`gateway_timeout`), bank downtime (`bank_unavailable`), or transient authorization blips.
  - Maximum autonomous retry attempts: **2 retries per transaction**.
  - Minimum retry backoff interval: **15 minutes** for retry #1, **60 minutes** for retry #2.
- **Strict Prohibition**:
  - Do NOT retry if failure reason is `insufficient_funds` or `account_blocked` without waiting at least 12 hours.
  - Do NOT retry if card is reported lost/stolen (`card_stolen_or_lost`).

### 2.3 Smart Reminders & Alternative Payment Methods (`reminder`, `alternative_payment_method`)
- **Channels**: Email, SMS, WhatsApp (via merchant configured webhooks/integrations).
- **Timing**:
  - First notification: Within 10 minutes of failure for cart abandonment / checkout drop-off.
  - Second notification: T+4 hours if unopened.
  - Max automated reminders: **2 per transaction**.
- **Alternative Method Recommendations**:
  - If Card fails due to OTP timeout, recommend UPI Deep-Link.
  - If UPI fails due to PSP timeout (e.g. Google Pay / PhonePe bank degradation), recommend NetBanking or Card.

### 2.4 Discounts & Incentives (`incentive_recovery`)
- **Autonomous Limit**: Maximum 10% instant checkout discount or waived convenience fee up to INR 250.
- **High-Discount Threshold**: Any incentive > 10% requires **Human Approval**.

---

## 3. Human Approval Thresholds & Guardrails

| Rule Condition | Policy Verdict | Action Required |
| :--- | :--- | :--- |
| Transaction Amount > INR 25,000 | `HUMAN_APPROVAL_REQUIRED` | Route to Merchant Admin Queue for 1-click review |
| Customer Total Risk Score > 0.65 | `HUMAN_APPROVAL_REQUIRED` | Flag for fraud risk investigation |
| Total Retries Exceeded (>= 3 attempts) | `BLOCKED` | Halt autonomous retries to prevent gateway penalties |
| Inactive / Blacklisted Customer Phone or Email | `BLOCKED` | Discard recovery action, log reason |
| Proposed Discount > 10% | `HUMAN_APPROVAL_REQUIRED` | Merchant finance approval needed |
| Repeated Failures on Same Bin/Card (> 5 in 1 hr) | `BLOCKED` | Potential card attack; trigger merchant anomaly alert |

---

## 4. Stopping Rules (Circuit Breakers)
1. **Recovery Stop Upon Payment Success**: Once Razorpay webhook signals `payment.captured` or `payment_link.paid`, immediately cancel all pending reminders, retries, and secondary recovery actions.
2. **Customer Opt-Out**: If customer replies STOP or indicates charge dispute, cancel recovery flow and mark status `STOPPED_BY_CUSTOMER`.
3. **Gateway Anomaly Threshold**: If overall PSP failure rate exceeds 25% over a 15-minute rolling window, pause automated direct retries and switch exclusively to asynchronous Payment Links with extended expiry.

---

## 5. Auditability & Compliance
- Every agent thought process, retrieved policy chunk, risk probability score, and guardrail validation result MUST be logged immutably in the `AUDIT_LOG` and `AGENT_RUN` tables.
- No direct financial debit or credit may occur without a cryptographic signature verification on inbound Razorpay webhooks.
