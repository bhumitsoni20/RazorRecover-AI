# RazorRecover AI — Primary Demo Guide

## 1. Demo Scenario Overview
- **Customer**: Aditya Verma (`aditya.verma@example.com`, 11/12 successful payments historical record)
- **Transaction**: `txn_4999_upi` (Amount: **₹4,999**)
- **Incident**: Failed payment caused by severe NPCI / HDFC UPI gateway degradation (+4.8x failure spike during attempt window).
- **Goal**: Demonstrate how RazorRecover AI automatically detects the failure, reasons about the root cause, retrieves merchant recovery policies, validates guardrails, generates a Razorpay Test Mode Payment Link, and verifies the recovery.

---

## 2. Step-by-Step Demo Walkthrough

### Step 1: Open Merchant Dashboard
1. Navigate to `http://localhost:3000/dashboard`.
2. Observe the high-level KPI cards:
   - **Revenue At Risk**: ₹2,84,210
   - **Recovered Revenue**: ₹1,82,450
   - **Recovery Rate**: 64.2%
   - **Active AI Actions**: 38
3. Point out the **Anomaly Alert Banner** highlighting the real-time UPI degradation spike across HDFC/SBI gateways.
4. Point out the **AI Recovery Queue** showing `txn_4999_upi` as top priority.

### Step 2: Deep-Dive into Transaction Investigation
1. Click **"Investigate Failed ₹4,999"** or navigate to `http://localhost:3000/transactions/txn_4999_upi`.
2. Review the **AI Investigation Card**:
   - **Root Cause**: Payment Method Degradation (91% Confidence)
   - **Evidence**:
     - ✓ UPI failure rate increased 4.8x during attempt window
     - ✓ Customer historical success rate: 91.6%
     - ✓ Zero fraud flags & trusted device fingerprint verified
   - **Recovery Probability**: 87% (Expected recovery: ₹4,349)
   - **Deterministic Policy Check**: `APPROVED` (Amount ₹4,999 <= ₹25k limit, Attempt #1 <= 2 retries)
   - **RAG Policy Source**: Cited from Merchant Recovery Policy §2.1.

### Step 3: Trigger Autonomous Execution
1. Click the **"Execute AI Recovery"** button.
2. Watch the **Animated Agent Execution Timeline** transition smoothly:
   - *Detect Revenue Risk* -> *Root Cause Analysis* -> *RAG Policy Retrieval* -> *Guardrails Validation* -> *Razorpay Test Mode API Call* -> *Payment Link Generated*.
3. Observe the live generated Razorpay Test link displayed in the green success card (e.g. `https://rzp.io/i/test_...`).

### Step 4: Verify Audit Trail & Telemetry
1. Navigate to `http://localhost:3000/audit` to view the immutable audit entry logged with exact input and output JSON.
2. Navigate to `http://localhost:3000/agents` to see live agent latency and execution metrics.
3. Navigate to `http://localhost:3000/evaluation` to review empirical model accuracy (92.4%) and ROI metrics.
