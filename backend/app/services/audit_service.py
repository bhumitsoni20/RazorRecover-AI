from datetime import datetime
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.schemas.audit import AuditLogItem


class AuditService:
    @classmethod
    async def record_event(
        cls,
        db: AsyncSession,
        agent_name: str,
        action: str,
        reasoning_summary: str,
        actor: str = "system",
        transaction_id: str | None = None,
        input_data: dict[str, Any] | None = None,
        output_data: dict[str, Any] | None = None,
        policy_result: str | None = None,
        merchant_id: str | None = None,
    ) -> AuditLog:
        """
        Appends an immutable audit log entry into the cryptographic hash chain.
        """
        if not merchant_id and transaction_id:
            from app.models.transaction import Transaction
            txn_res = await db.execute(select(Transaction.merchant_id).where(Transaction.id == transaction_id))
            merchant_id = txn_res.scalar_one_or_none()

        # Fetch the most recent audit entry to get previous_hash for this merchant
        query = select(AuditLog)
        if merchant_id:
            query = query.where(AuditLog.merchant_id == merchant_id)
        query = query.order_by(desc(AuditLog.created_at)).limit(1)

        latest_entry_res = await db.execute(query)
        latest_entry = latest_entry_res.scalar_one_or_none()
        previous_hash = latest_entry.event_hash if latest_entry else ("0" * 64)

        now = datetime.utcnow()
        created_at_str = now.isoformat()
        temp_id = f"aud_{int(now.timestamp() * 1000)}"

        event_hash = AuditLog.calculate_hash(
            id_str=temp_id,
            transaction_id=transaction_id,
            agent_name=agent_name,
            action=action,
            reasoning_summary=reasoning_summary,
            policy_result=policy_result,
            previous_hash=previous_hash,
            created_at_str=created_at_str,
            merchant_id=merchant_id,
        )

        entry = AuditLog(
            id=temp_id,
            merchant_id=merchant_id,
            transaction_id=transaction_id,
            agent_name=agent_name,
            actor=actor,
            action=action,
            reasoning_summary=reasoning_summary,
            input_data=input_data,
            output_data=output_data,
            policy_result=policy_result,
            previous_hash=previous_hash,
            event_hash=event_hash,
            created_at=now,
        )
        db.add(entry)
        await db.commit()
        return entry

    # Alias for backward compatibility
    record_audit_event = record_event

    @classmethod
    async def list_audit_logs(
        cls,
        db: AsyncSession,
        merchant_id: str | None = None,
        agent_name: str | None = None,
        transaction_id: str | None = None,
        limit: int = 50,
    ) -> list[AuditLogItem]:
        query = select(AuditLog)
        if merchant_id:
            query = query.where(AuditLog.merchant_id == merchant_id)
        if agent_name and agent_name != "all":
            query = query.where(AuditLog.agent_name == agent_name)
        if transaction_id:
            query = query.where(AuditLog.transaction_id == transaction_id)

        query = query.order_by(desc(AuditLog.created_at)).limit(limit)
        results = (await db.execute(query)).scalars().all()

        items = [
            AuditLogItem(
                id=log.id,
                transaction_id=log.transaction_id,
                agent_name=log.agent_name,
                action=log.action,
                reasoning_summary=log.reasoning_summary,
                input_data=log.input_data,
                output_data=log.output_data,
                policy_result=log.policy_result,
                created_at=log.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(log.created_at, "strftime") else str(log.created_at),
            )
            for log in results
        ]

        return items

    @classmethod
    async def verify_audit_chain(cls, db: AsyncSession, merchant_id: str | None = None) -> dict[str, Any]:
        """
        Cryptographically verifies the continuity and immutability of the audit log hash chain.
        """
        query = select(AuditLog)
        if merchant_id:
            query = query.where(AuditLog.merchant_id == merchant_id)
        query = query.order_by(AuditLog.created_at.asc())
        results = (await db.execute(query)).scalars().all()

        if not results:
            return {"is_valid": True, "total_records": 0, "status": "empty_chain"}

        expected_prev_hash = "0" * 64
        for idx, entry in enumerate(results):
            # Check previous hash link
            if entry.previous_hash != expected_prev_hash:
                return {
                    "is_valid": False,
                    "broken_index": idx,
                    "record_id": entry.id,
                    "error": f"Previous hash mismatch at record {entry.id}",
                }

            # Recalculate event hash
            recalc = AuditLog.calculate_hash(
                id_str=entry.id,
                transaction_id=entry.transaction_id,
                agent_name=entry.agent_name,
                action=entry.action,
                reasoning_summary=entry.reasoning_summary,
                policy_result=entry.policy_result,
                previous_hash=entry.previous_hash,
                created_at_str=entry.created_at.isoformat(),
                merchant_id=entry.merchant_id,
            )
            if recalc != entry.event_hash:
                return {
                    "is_valid": False,
                    "broken_index": idx,
                    "record_id": entry.id,
                    "error": f"Hash integrity failure at record {entry.id}",
                }

            expected_prev_hash = entry.event_hash

        return {
            "is_valid": True,
            "total_records": len(results),
            "status": "cryptographically_verified",
            "latest_hash": results[-1].event_hash,
        }
