from typing import List, Tuple, Dict, Any, Optional
from app.core.config import settings
from app.schemas.transaction import PolicyCheckItem


class PolicyEngine:
    """
    Deterministic Guardrail & Policy Engine for RazorRecover AI (Phase 8).
    Authoritative backend decision engine: Never allows non-deterministic LLMs to bypass business limits,
    fraud safeguards, retry caps, or stopping rules.
    """

    ALLOWED_ACTIONS = {"payment_link", "retry", "reminder", "alternative_payment_method"}

    @classmethod
    def evaluate(
        cls,
        amount: float,
        proposed_action: str = "payment_link",
        failure_reason: str = "upi_timeout",
        attempt_number: int = 1,
        customer_risk_score: float = 0.15,
        proposed_discount_pct: float = 0.0,
        transaction_status: str = "failed",
        has_active_link: bool = False,
    ) -> Tuple[str, List[PolicyCheckItem], List[str]]:
        """
        Evaluates proposed AI action against deterministic rules.
        Returns:
            - verdict: 'APPROVED' | 'HUMAN_APPROVAL_REQUIRED' | 'BLOCKED'
            - check_items: List of granular pass/fail checks
            - reasons: Summary list of explanations
        """
        checks: List[PolicyCheckItem] = []
        reasons: List[str] = []
        is_blocked = False
        requires_human = False

        # 1. Stopping Rules: Check transaction state
        if transaction_status in ["recovered", "success"]:
            checks.append(PolicyCheckItem(
                name="Stopping Rule: Transaction Status",
                status="failed",
                detail="Transaction is already recovered. All automated recovery actions halted."
            ))
            is_blocked = True
            reasons.append("Stopping Rule: Payment already captured.")
        elif transaction_status == "blocked":
            checks.append(PolicyCheckItem(
                name="Stopping Rule: Transaction Status",
                status="failed",
                detail="Transaction was previously blocked by policy."
            ))
            is_blocked = True
            reasons.append("Transaction is permanently blocked.")
        else:
            checks.append(PolicyCheckItem(
                name="Stopping Rule: Transaction Status",
                status="passed",
                detail="Transaction is in recoverable failed/abandoned state."
            ))

        # 2. Duplicate Recovery Prevention
        if has_active_link and proposed_action == "payment_link":
            checks.append(PolicyCheckItem(
                name="Duplicate Recovery Prevention",
                status="failed",
                detail="An active, unexpired payment link already exists for this transaction."
            ))
            is_blocked = True
            reasons.append("Duplicate recovery blocked: active payment link already dispatched.")
        else:
            checks.append(PolicyCheckItem(
                name="Duplicate Recovery Prevention",
                status="passed",
                detail="No conflicting active recovery action."
            ))

        # 3. Allowed Actions Validation
        if proposed_action not in cls.ALLOWED_ACTIONS:
            checks.append(PolicyCheckItem(
                name="Allowed Recovery Actions",
                status="failed",
                detail=f"Action '{proposed_action}' is not in allowed merchant recovery actions list."
            ))
            is_blocked = True
            reasons.append(f"Invalid recovery action '{proposed_action}'.")
        else:
            checks.append(PolicyCheckItem(
                name="Allowed Recovery Actions",
                status="passed",
                detail=f"Action '{proposed_action}' is permitted under Merchant Policy §2."
            ))

        # 4. Attempt Count Limit Check (Max 2 retries)
        if attempt_number > settings.MAX_AUTONOMOUS_RETRIES:
            checks.append(PolicyCheckItem(
                name=f"Max Retry Limit (<= {settings.MAX_AUTONOMOUS_RETRIES} retries)",
                status="failed",
                detail=f"Attempt #{attempt_number} exceeds max allowed automated retries ({settings.MAX_AUTONOMOUS_RETRIES})"
            ))
            is_blocked = True
            reasons.append(f"Maximum retry limit ({settings.MAX_AUTONOMOUS_RETRIES}) reached. Automated recovery blocked.")
        else:
            checks.append(PolicyCheckItem(
                name=f"Max Retry Limit (<= {settings.MAX_AUTONOMOUS_RETRIES} retries)",
                status="passed",
                detail=f"Attempt #{attempt_number} is within safe limit"
            ))

        # 5. Non-retryable failure reasons
        if failure_reason in ["insufficient_funds", "card_stolen_or_lost", "account_frozen", "account_blocked"]:
            checks.append(PolicyCheckItem(
                name="Non-Retryable Failure Code",
                status="failed",
                detail=f"Reason '{failure_reason}' cannot be automatically recovered"
            ))
            is_blocked = True
            reasons.append(f"Immediate recovery prohibited for permanent failure type '{failure_reason}'.")
        else:
            checks.append(PolicyCheckItem(
                name="Non-Retryable Failure Code",
                status="passed",
                detail=f"Failure reason '{failure_reason}' is eligible for recovery"
            ))

        # 6. Amount Guardrail Check (<= ₹25,000)
        if amount > settings.MAX_AUTONOMOUS_AMOUNT:
            checks.append(PolicyCheckItem(
                name=f"Autonomous Amount Limit (<= ₹{settings.MAX_AUTONOMOUS_AMOUNT:,.0f})",
                status="warning",
                detail=f"Amount ₹{amount:,.2f} exceeds autonomous limit of ₹{settings.MAX_AUTONOMOUS_AMOUNT:,.2f}"
            ))
            requires_human = True
            reasons.append("High-value transaction exceeds automated threshold; routing for human review.")
        else:
            checks.append(PolicyCheckItem(
                name=f"Autonomous Amount Limit (<= ₹{settings.MAX_AUTONOMOUS_AMOUNT:,.0f})",
                status="passed",
                detail=f"Amount ₹{amount:,.2f} is within autonomous approval limit"
            ))

        # 7. Customer Fraud & Risk Score Check (< 0.65 safe, 0.65-0.85 human review, >0.85 blocked)
        if customer_risk_score > 0.85:
            checks.append(PolicyCheckItem(
                name="Customer Fraud Risk (< 0.65)",
                status="failed",
                detail=f"Critical customer risk score {customer_risk_score:.2f} exceeds 0.85 threshold"
            ))
            is_blocked = True
            reasons.append("Critical fraud risk score. Automated recovery halted.")
        elif customer_risk_score > settings.RISK_SCORE_THRESHOLD:
            checks.append(PolicyCheckItem(
                name="Customer Fraud Risk (< 0.65)",
                status="warning",
                detail=f"Customer risk score {customer_risk_score:.2f} exceeds safe threshold of 0.65"
            ))
            requires_human = True
            reasons.append("Moderate risk score flags transaction for manual review.")
        else:
            checks.append(PolicyCheckItem(
                name="Customer Fraud Risk (< 0.65)",
                status="passed",
                detail=f"Customer risk score {customer_risk_score:.2f} is safe"
            ))

        # 8. Discount Cap Check (<= 10%)
        if proposed_discount_pct > settings.MAX_AUTONOMOUS_DISCOUNT_PERCENT:
            checks.append(PolicyCheckItem(
                name=f"Discount Limit (<= {settings.MAX_AUTONOMOUS_DISCOUNT_PERCENT}%)",
                status="warning",
                detail=f"Proposed discount {proposed_discount_pct}% exceeds automated cap of {settings.MAX_AUTONOMOUS_DISCOUNT_PERCENT}%"
            ))
            requires_human = True
            reasons.append(f"Incentive discount {proposed_discount_pct}% requires merchant finance approval.")
        elif proposed_discount_pct > 0:
            checks.append(PolicyCheckItem(
                name=f"Discount Limit (<= {settings.MAX_AUTONOMOUS_DISCOUNT_PERCENT}%)",
                status="passed",
                detail=f"Discount {proposed_discount_pct}% is within autonomous policy limits"
            ))

        # Determine Final Verdict
        if is_blocked:
            verdict = "BLOCKED"
        elif requires_human:
            verdict = "HUMAN_APPROVAL_REQUIRED"
        else:
            verdict = "APPROVED"
            reasons.append("All policy guardrails and safety limits passed successfully.")

        return verdict, checks, reasons

    @classmethod
    def evaluate_structured(cls, **kwargs) -> Dict[str, Any]:
        """Convenience method returning a JSON-serializable dictionary."""
        verdict, checks, reasons = cls.evaluate(**kwargs)
        return {
            "verdict": verdict,
            "checks": [c.model_dump() for c in checks],
            "reasons": reasons,
            "reason": reasons[0] if reasons else "Complies with merchant recovery policy.",
            "is_approved": verdict == "APPROVED",
            "requires_human_approval": verdict == "HUMAN_APPROVAL_REQUIRED",
            "is_blocked": verdict == "BLOCKED",
        }
