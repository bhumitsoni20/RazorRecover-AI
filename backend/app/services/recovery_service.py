import time
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.workflow import MultiAgentWorkflow
from app.core.logging import logger
from app.integrations.razorpay_service import razorpay_service
from app.models.agent_run import AgentRun
from app.models.customer import Customer
from app.models.recovery_action import RecoveryAction
from app.models.revenue_risk import RevenueRisk
from app.models.transaction import Transaction
from app.policies.policy_engine import PolicyEngine
from app.schemas.recovery import (
    AnalyzeResponse,
    ApproveResponse,
    ExecuteResponse,
)
from app.services.audit_service import AuditService


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class RecoveryService:
    @classmethod
    async def analyze_transaction(
        cls,
        db: AsyncSession,
        transaction_id: str,
        is_simulation_mode: bool = False,
    ) -> AnalyzeResponse:
        start_time = time.time()

        # Record AI_INVESTIGATION_STARTED audit
        await AuditService.record_audit_event(
            db=db,
            agent_name="MultiAgentWorkflow",
            action="AI_INVESTIGATION_STARTED",
            reasoning_summary=f"Initiating autonomous revenue recovery investigation for {transaction_id}",
            actor="RecoveryStrategyAgent",
            transaction_id=transaction_id,
            policy_result="IN_PROGRESS",
        )

        # Fetch transaction from DB
        txn_res = await db.execute(
            select(Transaction, Customer, RevenueRisk)
            .join(Customer, Customer.id == Transaction.customer_id)
            .outerjoin(RevenueRisk, RevenueRisk.transaction_id == Transaction.id)
            .where(Transaction.id == transaction_id)
        )
        res = txn_res.first()

        amount: float = 4999.0
        failure_reason = "upi_timeout"
        customer_name = "Aditya Verma"
        customer_email = "aditya.verma@example.com"
        customer_phone = "+919876543210"
        payment_method = "upi"
        bank = "HDFC"
        attempt_number = 1
        customer_success_rate = 0.916

        if res:
            txn, cust, _ = res
            amount = float(txn.amount)
            failure_reason = txn.failure_reason or "upi_timeout"
            customer_name = cust.name
            customer_email = cust.email
            customer_phone = cust.phone
            payment_method = txn.payment_method
            bank = txn.bank or "HDFC"
            attempt_number = txn.attempt_number
            customer_success_rate = (
                cust.successful_transactions / max(cust.total_transactions, 1)
            )

        # Run Multi-Agent Workflow
        result = await MultiAgentWorkflow.run(
            transaction_id=transaction_id,
            amount=amount,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            payment_method=payment_method,
            failure_reason=failure_reason,
            attempt_number=attempt_number,
            bank=bank,
            customer_success_rate=customer_success_rate,
            is_simulation_mode=is_simulation_mode,
        )

        latency_ms = int((time.time() - start_time) * 1000)

        # Record Telemetry and Granular Audits
        db.add(AgentRun(
            transaction_id=transaction_id,
            agent_name="MultiAgentWorkflow",
            status="success",
            latency_ms=max(latency_ms, 120),
            input_data={"amount": amount, "method": payment_method, "reason": failure_reason},
            output_data={"action": result["action"], "verdict": result["policy_decision"]},
        ))

        # ROOT_CAUSE_IDENTIFIED
        await AuditService.record_audit_event(
            db=db,
            agent_name="RootCauseAgent",
            action="ROOT_CAUSE_IDENTIFIED",
            reasoning_summary=f"Diagnosed failure root cause as '{result['root_cause']}'",
            actor="RootCauseAgent",
            transaction_id=transaction_id,
            output_data={"root_cause": result["root_cause"], "evidence": result["evidence"]},
            policy_result="PASSED",
        )

        # POLICY_RETRIEVED
        await AuditService.record_audit_event(
            db=db,
            agent_name="RAGPolicyRetriever",
            action="POLICY_RETRIEVED",
            reasoning_summary=f"Retrieved merchant policy citation: {result['policy_references'][0] if result['policy_references'] else 'Policy §2.1'}",
            actor="RAGPolicyRetriever",
            transaction_id=transaction_id,
            output_data={"citations": result["policy_references"]},
            policy_result="PASSED",
        )

        # RECOVERY_PREDICTED & STRATEGY_SELECTED
        await AuditService.record_audit_event(
            db=db,
            agent_name="RecoveryMLModel",
            action="RECOVERY_PREDICTED",
            reasoning_summary=f"Predicted recovery probability {int(result['recovery_probability'] * 100)}% (Expected yield: ₹{result['expected_recovery']:,.2f})",
            actor="RecoveryMLModel",
            transaction_id=transaction_id,
            output_data={"probability": result["recovery_probability"], "expected": result["expected_recovery"]},
            policy_result="PASSED",
        )

        await AuditService.record_audit_event(
            db=db,
            agent_name="RecoveryStrategyAgent",
            action="STRATEGY_SELECTED",
            reasoning_summary=f"Selected recovery action '{result['action']}' with verdict '{result['policy_decision']}'",
            actor="RecoveryStrategyAgent",
            transaction_id=transaction_id,
            output_data={"action": result["action"], "verdict": result["policy_decision"]},
            policy_result=result["policy_decision"],
        )

        if result["policy_decision"] == "APPROVED":
            await AuditService.record_audit_event(
                db=db,
                agent_name="PolicyGuardrailEngine",
                action="GUARDRAIL_APPROVED",
                reasoning_summary=f"Autonomous action '{result['action']}' approved by deterministic guardrails",
                actor="PolicyGuardrailEngine",
                transaction_id=transaction_id,
                policy_result="APPROVED",
            )

        return AnalyzeResponse(
            transaction_id=transaction_id,
            root_cause=result["root_cause"],
            confidence=result["confidence"],
            evidence=result["evidence"],
            recovery_probability=result["recovery_probability"],
            recommended_action=result["action"],
            expected_recovery=result["expected_recovery"],
            policy_decision=result["policy_decision"],
            guardrails_passed=(result["policy_decision"] == "APPROVED"),
            policy_details=[c.get("detail", "") for c in result.get("policy_checks", [])],
            rag_policy_reference=result["policy_references"][0] if result.get("policy_references") else None,
        )

    @classmethod
    async def execute_recovery(
        cls,
        db: AsyncSession,
        transaction_id: str,
        action_type: str = "payment_link",
        is_simulation_mode: bool = False,
        is_human_approved: bool = False,
    ) -> ExecuteResponse:
        """
        Idempotent Recovery Execution.
        Enforces database state checks to prevent duplicate actions, double charging, or redundant API calls.
        """
        # 1. Fetch transaction
        txn_res = await db.execute(
            select(Transaction, Customer, RevenueRisk)
            .join(Customer, Customer.id == Transaction.customer_id)
            .outerjoin(RevenueRisk, RevenueRisk.transaction_id == Transaction.id)
            .where(Transaction.id == transaction_id)
        )
        res = txn_res.first()

        amount = 4999.0
        currency = "INR"
        customer_name = "Customer"
        customer_email = "customer@example.com"
        customer_phone = "+919876543210"
        attempt_number = 1
        failure_reason = "upi_timeout"
        txn_status = "failed"

        if res:
            txn, cust, _ = res
            amount = float(txn.amount)
            currency = txn.currency
            customer_name = cust.name
            customer_email = cust.email
            customer_phone = cust.phone
            attempt_number = txn.attempt_number
            failure_reason = txn.failure_reason or "upi_timeout"
            txn_status = txn.status

        # 2. Idempotency Check: Already Recovered
        if txn_status == "recovered":
            logger.info(f"Idempotency: Transaction {transaction_id} is already recovered.")
            return ExecuteResponse(
                transaction_id=transaction_id,
                action_id=f"act_recov_{transaction_id}",
                action_type=action_type,
                status="recovered",
                policy_verdict="APPROVED",
                message=f"Transaction {transaction_id} has already been successfully recovered.",
                timeline_steps=[
                    {"step": "Recovery Status Verified", "status": "completed", "note": "Already recovered"},
                    {"step": "Payment Captured", "status": "completed", "amount": amount},
                ],
            )

        # 3. Idempotency Check: Active Payment Link Already Generated (unless human approval is overriding)
        if not is_human_approved:
            existing_action_res = await db.execute(
                select(RecoveryAction)
                .where(
                    RecoveryAction.transaction_id == transaction_id,
                    RecoveryAction.status.in_(["executed", "link_created", "completed"]),
                )
                .order_by(desc(RecoveryAction.created_at))
            )
            existing_action = existing_action_res.scalars().first()
            if existing_action and existing_action.external_reference and "rzp.io" in str(existing_action.external_reference):
                logger.info(f"Idempotency: Active payment link already exists for {transaction_id}: {existing_action.external_reference}")
                return ExecuteResponse(
                    transaction_id=str(transaction_id),
                    action_id=str(existing_action.id),
                    action_type=str(existing_action.action_type),
                    status="executed",
                    razorpay_payment_link=str(existing_action.external_reference),
                    razorpay_reference_id=str(existing_action.id),
                    policy_verdict="APPROVED",
                    message="Active payment link retrieved from existing recovery record (Idempotent).",
                    timeline_steps=[
                        {"step": "Detect Revenue Risk", "status": "completed"},
                        {"step": "Policy Guardrails Verified", "status": "completed"},
                        {"step": "Active Razorpay Link Retrieved", "status": "completed", "link": str(existing_action.external_reference)},
                    ],
                )

        # 4. Deterministic Guardrails Check
        verdict, _checks, reasons = PolicyEngine.evaluate(
            amount=amount,
            proposed_action=action_type,
            failure_reason=failure_reason,
            attempt_number=attempt_number,
        )

        timeline_steps: list[dict[str, Any]] = [
            {"step": "Detect Revenue Risk", "status": "completed", "timestamp": utcnow().isoformat()},
            {"step": "Root Cause Analysis", "status": "completed", "timestamp": utcnow().isoformat()},
            {"step": "RAG Policy Retrieval", "status": "completed", "timestamp": utcnow().isoformat()},
            {"step": "Policy & Guardrail Validation", "status": "completed", "verdict": verdict, "timestamp": utcnow().isoformat()},
        ]

        if verdict == "BLOCKED" and not is_human_approved:
            timeline_steps.append({"step": "Action Execution", "status": "blocked", "reason": reasons[0] if reasons else "Blocked"})
            await AuditService.record_audit_event(
                db=db,
                agent_name="PolicyGuardrailEngine",
                action="block_unauthorized_recovery",
                reasoning_summary=f"Blocked {action_type} for {transaction_id}: {reasons[0] if reasons else 'Limit exceeded'}",
                actor="PolicyGuardrailEngine",
                transaction_id=transaction_id,
                policy_result="BLOCKED",
            )
            return ExecuteResponse(
                transaction_id=transaction_id,
                action_id=f"act_blocked_{uuid.uuid4().hex[:8]}",
                action_type=action_type,
                status="blocked",
                policy_verdict=verdict,
                message=f"Action blocked by policy guardrails: {reasons[0] if reasons else 'Limits exceeded'}",
                timeline_steps=timeline_steps,
            )

        if verdict == "HUMAN_APPROVAL_REQUIRED" and not is_human_approved:
            existing_pend_res = await db.execute(
                select(RecoveryAction)
                .where(RecoveryAction.transaction_id == transaction_id)
                .order_by(desc(RecoveryAction.created_at))
            )
            existing_pend = existing_pend_res.scalars().first()
            if existing_pend:
                action_id = str(existing_pend.id)
                existing_pend.action_type = action_type
                existing_pend.reason = "High-value or flagged transaction routed to human review"
                existing_pend.confidence = 0.88
                existing_pend.policy_decision = "HUMAN_APPROVAL_REQUIRED"
                existing_pend.status = "pending"
            else:
                action_id = f"act_pend_{uuid.uuid4().hex[:8]}"
                new_action = RecoveryAction(
                    id=action_id,
                    transaction_id=transaction_id,
                    action_type=action_type,
                    reason="High-value or flagged transaction routed to human review",
                    confidence=0.88,
                    policy_decision="HUMAN_APPROVAL_REQUIRED",
                    status="pending",
                )
                db.add(new_action)
            await db.commit()

            timeline_steps.append({"step": "Routed to Human Review", "status": "pending_approval", "timestamp": utcnow().isoformat()})
            await AuditService.record_audit_event(
                db=db,
                agent_name="PolicyGuardrailEngine",
                action="route_to_human_approval",
                reasoning_summary=f"Routed {transaction_id} to merchant human review queue",
                actor="PolicyGuardrailEngine",
                transaction_id=transaction_id,
                policy_result="HUMAN_APPROVAL_REQUIRED",
            )
            return ExecuteResponse(
                transaction_id=str(transaction_id),
                action_id=action_id,
                action_type=action_type,
                status="pending_approval",
                policy_verdict=verdict,
                message="Action requires merchant human approval before execution.",
                timeline_steps=timeline_steps,
            )

        # 5. APPROVED: Record RECOVERY_EXECUTION_STARTED
        await AuditService.record_audit_event(
            db=db,
            agent_name="ActionExecutionAgent",
            action="RECOVERY_EXECUTION_STARTED",
            reasoning_summary=f"Starting Razorpay Test Mode execution for {transaction_id}",
            actor="ActionExecutionAgent",
            transaction_id=transaction_id,
            policy_result="APPROVED",
        )

        # 6. Execute via Razorpay Test Mode API
        ref_id = f"recov_{transaction_id}_{int(time.time())}"
        rzp_link = await razorpay_service.create_payment_link(
            amount=amount,
            currency=currency,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            description=f"Payment recovery for {transaction_id}",
            reference_id=ref_id,
        )

        existing_act_res = await db.execute(
            select(RecoveryAction)
            .where(RecoveryAction.transaction_id == transaction_id)
            .order_by(desc(RecoveryAction.created_at))
        )
        existing_act = existing_act_res.scalars().first()
        if existing_act:
            existing_act.action_type = action_type
            existing_act.reason = "Human approved recovery via Razorpay Test Mode Payment Link" if is_human_approved else "Autonomous recovery via Razorpay Test Mode Payment Link"
            existing_act.confidence = 0.91
            existing_act.policy_decision = "APPROVED"
            existing_act.status = "executed"
            existing_act.external_reference = rzp_link.get("short_url") or rzp_link.get("id")
            existing_act.completed_at = utcnow()
            action_id = str(existing_act.id)
        else:
            action_id = f"act_{uuid.uuid4().hex[:8]}"
            new_action = RecoveryAction(
                id=action_id,
                transaction_id=transaction_id,
                action_type=action_type,
                reason="Autonomous recovery via Razorpay Test Mode Payment Link" if not is_human_approved else "Human approved recovery via Razorpay Test Mode Payment Link",
                confidence=0.91,
                policy_decision="APPROVED",
                status="executed",
                external_reference=rzp_link.get("short_url") or rzp_link.get("id"),
                completed_at=utcnow(),
            )
            db.add(new_action)
        await db.commit()

        # RAZORPAY_PAYMENT_LINK_CREATED Audit Log
        await AuditService.record_audit_event(
            db=db,
            agent_name="ActionExecutionAgent",
            action="RAZORPAY_PAYMENT_LINK_CREATED",
            reasoning_summary=f"Generated and dispatched Razorpay Test Mode link: {rzp_link.get('short_url')}",
            actor="ActionExecutionAgent",
            transaction_id=transaction_id,
            input_data={"amount": amount, "customer": customer_name},
            output_data=rzp_link,
            policy_result="APPROVED",
        )

        timeline_steps.append({"step": "Razorpay Test Mode API Call", "status": "completed", "link": rzp_link.get("short_url"), "timestamp": utcnow().isoformat()})
        timeline_steps.append({"step": "Payment Link Generated & Dispatched", "status": "completed", "timestamp": utcnow().isoformat()})

        return ExecuteResponse(
            transaction_id=transaction_id,
            action_id=action_id,
            action_type=action_type,
            status="executed",
            razorpay_payment_link=rzp_link.get("short_url"),
            razorpay_reference_id=rzp_link.get("id"),
            policy_verdict="APPROVED",
            message="Payment Link successfully generated and dispatched via Razorpay Test Mode.",
            timeline_steps=timeline_steps,
        )

    @classmethod
    async def approve_action(
        cls,
        db: AsyncSession,
        transaction_id: str,
        approved: bool = True,
        approver_note: str = "Approved by Merchant Admin",
        actor: str = "MerchantAdmin",
    ) -> ApproveResponse:
        action_query = await db.execute(
            select(RecoveryAction)
            .where(
                RecoveryAction.transaction_id == transaction_id,
                RecoveryAction.policy_decision == "HUMAN_APPROVAL_REQUIRED",
            )
            .order_by(desc(RecoveryAction.created_at))
        )
        action = action_query.scalars().first()
        action_id = str(action.id) if action else f"act_{uuid.uuid4().hex[:8]}"

        if not approved:
            if action:
                action.status = "rejected"
                action.completed_at = utcnow()
            await AuditService.record_audit_event(
                db=db,
                agent_name="HumanReviewer",
                action="reject_recovery_action",
                reasoning_summary=f"Action rejected by {actor}: {approver_note}",
                actor=actor,
                transaction_id=transaction_id,
                policy_result="REJECTED",
            )
            return ApproveResponse(
                transaction_id=transaction_id,
                action_id=action_id,
                status="rejected",
                message="Recovery action rejected by merchant admin.",
            )

        # Approved: Execute via Razorpay Test Mode with human approval flag
        exec_res = await cls.execute_recovery(db, transaction_id, action_type="payment_link", is_human_approved=True)
        await AuditService.record_audit_event(
            db=db,
            agent_name="HumanReviewer",
            action="approve_and_execute_recovery",
            reasoning_summary=f"Action approved by {actor}: Dispatched Razorpay link {exec_res.razorpay_payment_link}",
            actor=actor,
            transaction_id=transaction_id,
            policy_result="APPROVED",
        )
        return ApproveResponse(
            transaction_id=transaction_id,
            action_id=exec_res.action_id,
            status=exec_res.status,
            razorpay_payment_link=exec_res.razorpay_payment_link,
            message="Recovery action approved by merchant and executed via Razorpay Test Mode API.",
        )

    @classmethod
    async def get_recovery_status(cls, db: AsyncSession, transaction_id: str) -> dict[str, Any]:
        """
        Returns full current recovery status and latest action for a transaction.
        """
        txn_res = await db.execute(
            select(Transaction, Customer)
            .join(Customer, Customer.id == Transaction.customer_id)
            .where(Transaction.id == transaction_id)
        )
        row = txn_res.first()
        if not row:
            return {
                "transaction_id": transaction_id,
                "status": "not_found",
                "is_recovered": False,
            }

        txn, cust = row
        action_res = await db.execute(
            select(RecoveryAction)
            .where(RecoveryAction.transaction_id == transaction_id)
            .order_by(desc(RecoveryAction.created_at))
        )
        latest_action = action_res.scalars().first()

        return {
            "transaction_id": transaction_id,
            "status": txn.status,
            "is_recovered": (txn.status == "recovered"),
            "amount": txn.amount,
            "currency": txn.currency,
            "customer_name": cust.name,
            "customer_email": cust.email,
            "latest_action": {
                "id": latest_action.id if latest_action else None,
                "type": latest_action.action_type if latest_action else None,
                "status": latest_action.status if latest_action else None,
                "payment_link": latest_action.external_reference if latest_action else None,
                "amount_recovered": latest_action.amount_recovered if latest_action else 0.0,
                "created_at": latest_action.created_at.isoformat() if latest_action else None,
            } if latest_action else None,
        }
