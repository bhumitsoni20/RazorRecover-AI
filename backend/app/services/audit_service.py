from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.audit_log import AuditLog
from app.schemas.audit import AuditLogItem


class AuditService:
    @classmethod
    async def record_audit_event(
        cls,
        db: AsyncSession,
        agent_name: str,
        action: str,
        reasoning_summary: str,
        actor: str = "system",
        transaction_id: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        policy_result: Optional[str] = None,
    ) -> AuditLog:
        """
        Appends an immutable audit log entry into the cryptographic hash chain.
        """
        # Fetch the most recent audit entry to get previous_hash
        latest_entry_res = await db.execute(
            select(AuditLog).order_by(desc(AuditLog.created_at)).limit(1)
        )
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
        )

        entry = AuditLog(
            id=temp_id,
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

    @classmethod
    async def list_audit_logs(
        cls,
        db: AsyncSession,
        agent_name: Optional[str] = None,
        transaction_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[AuditLogItem]:
        query = select(AuditLog)
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
                created_at=log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            )
            for log in results
        ]

        return items

    @classmethod
    async def verify_audit_chain(cls, db: AsyncSession) -> Dict[str, Any]:
        """
        Cryptographically verifies the continuity and immutability of the entire audit log hash chain.
        """
        query = select(AuditLog).order_by(AuditLog.created_at.asc())
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
