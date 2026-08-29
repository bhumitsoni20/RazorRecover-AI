from typing import List, Tuple
from app.core.config import settings
from app.schemas.transaction import PolicyCheckItem


class PolicyEngine:
    """
    Deterministic Guardrail & Policy Engine for RazorRecover AI.
    Never allows non-deterministic LLMs to bypass business limits, fraud safeguards, or retry caps.
    """

    @classmethod
    def evaluate(
        cls,
        amount: float,
        proposed_action: str,
        failure_reason: str,
        attempt_number: int,
        customer_risk_score: float = 0.15,
        proposed_discount_pct: float = 0.0,
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

        # 1. Amount Guardrail Check
        if amount > settings.MAX_AUTONOMOUS_AMOUNT:
            checks.append(PolicyCheckItem(
                name="Autonomous Amount Limit (<= ₹25,000)",
                status="warning",
                detail=f"Amount ₹{amount:,.2f} exceeds autonomous limit of ₹{settings.MAX_AUTONOMOUS_AMOUNT:,.2f}"
            ))
            requires_human = True
            reasons.append("High-value transaction exceeds automated threshold; routing for human review.")
        else:
            checks.append(PolicyCheckItem(
                name="Autonomous Amount Limit (<= ₹25,000)",
                status="passed",
                detail=f"Amount ₹{amount:,.2f} is within autonomous approval limit"
            ))

        # 2. Customer Fraud & Risk Score Check
        if customer_risk_score > settings.RISK_SCORE_THRESHOLD:
            checks.append(PolicyCheckItem(
                name="Customer Fraud Risk (< 0.65)",
                status="failed" if customer_risk_score > 0.85 else "warning",
                detail=f"Customer risk score {customer_risk_score:.2f} exceeds safe threshold"
            ))
            if customer_risk_score > 0.85:
                is_blocked = True
                reasons.append("Elevated fraud risk score. Automated recovery halted.")
            else:
                requires_human = True
                reasons.append("Moderate risk score flags transaction for manual review.")
        else:
            checks.append(PolicyCheckItem(
                name="Customer Fraud Risk (< 0.65)",
                status="passed",
                detail=f"Customer risk score {customer_risk_score:.2f} is safe"
            ))

        # 3. Action-Specific Guardrails
        if proposed_action == "retry":
            if attempt_number >= settings.MAX_AUTONOMOUS_RETRIES:
                checks.append(PolicyCheckItem(
                    name="Max Retry Limit (<= 2 retries)",
                    status="failed",
                    detail=f"Attempt #{attempt_number} exceeds max allowed automated retries ({settings.MAX_AUTONOMOUS_RETRIES})"
                ))
                is_blocked = True
                reasons.append(f"Maximum retry limit ({settings.MAX_AUTONOMOUS_RETRIES}) reached. Direct retries blocked to protect merchant gateway standing.")
            else:
                checks.append(PolicyCheckItem(
                    name="Max Retry Limit (<= 2 retries)",
                    status="passed",
                    detail=f"Attempt #{attempt_number} is within limit"
                ))

            # Non-retryable failure reasons
            if failure_reason in ["insufficient_funds", "card_stolen_or_lost", "account_frozen"]:
                checks.append(PolicyCheckItem(
                    name="Retryable Failure Reason",
                    status="failed",
                    detail=f"Reason '{failure_reason}' cannot be automatically retried immediately"
                ))
                is_blocked = True
                reasons.append(f"Immediate retry prohibited for failure type '{failure_reason}'.")
            else:
                checks.append(PolicyCheckItem(
                    name="Retryable Failure Reason",
                    status="passed",
                    detail=f"Technical timeout / bank degradation '{failure_reason}' allows retry"
                ))

        elif proposed_action == "payment_link":
            checks.append(PolicyCheckItem(
                name="Payment Link Policy",
                status="passed",
                detail="Payment link generation permitted for recoverable degradation and customer retry"
            ))

        # 4. Discount Cap Check
        if proposed_discount_pct > settings.MAX_AUTONOMOUS_DISCOUNT_PERCENT:
            checks.append(PolicyCheckItem(
                name="Discount Limit (<= 10%)",
                status="warning",
                detail=f"Proposed discount {proposed_discount_pct}% exceeds automated cap of {settings.MAX_AUTONOMOUS_DISCOUNT_PERCENT}%"
            ))
            requires_human = True
            reasons.append(f"Incentive discount {proposed_discount_pct}% requires merchant finance approval.")
        elif proposed_discount_pct > 0:
            checks.append(PolicyCheckItem(
                name="Discount Limit (<= 10%)",
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
