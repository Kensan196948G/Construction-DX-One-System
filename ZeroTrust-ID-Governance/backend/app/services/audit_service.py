import hashlib
import json
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import AuditLog


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _compute_hash(
    prev_hash: str, action: str, actor_id: str, timestamp: str, payload: dict | None
) -> str:
    raw = f"{prev_hash}{action}{actor_id}{timestamp}{json.dumps(payload or {}, sort_keys=True)}"
    return hashlib.sha256(raw.encode()).hexdigest()


async def log_action(
    db: AsyncSession,
    action: str,
    actor_id: str | None = None,
    actor_ip: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    payload: dict | None = None,
    result: str | None = None,
) -> AuditLog:
    last = await db.execute(select(AuditLog).order_by(AuditLog.id.desc()).limit(1))
    last_log = last.scalar_one_or_none()
    prev_hash = last_log.hash if last_log else ""

    now = _now()
    hash_value = _compute_hash(
        prev_hash, action, actor_id or "", now.isoformat(), payload
    )

    log = AuditLog(
        action=action,
        actor_id=str(actor_id) if actor_id else None,
        actor_ip=actor_ip,
        target_type=target_type,
        target_id=str(target_id) if target_id else None,
        payload=payload,
        result=result,
        prev_hash=prev_hash or None,
        hash=hash_value,
        created_at=now,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def verify_chain(db: AsyncSession) -> dict:
    result = await db.execute(select(AuditLog).order_by(AuditLog.id))
    entries = list(result.scalars().all())

    if not entries:
        return {
            "valid": True,
            "broken_at": None,
            "total_entries": 0,
            "checked_entries": 0,
        }

    prev_hash = ""
    for idx, entry in enumerate(entries):
        expected = _compute_hash(
            prev_hash,
            entry.action,
            entry.actor_id or "",
            entry.created_at.isoformat(),
            entry.payload,
        )
        if entry.hash != expected:
            return {
                "valid": False,
                "broken_at": f"entry_{entry.id}",
                "total_entries": len(entries),
                "checked_entries": idx + 1,
            }
        if entry.prev_hash != (prev_hash or None):
            return {
                "valid": False,
                "broken_at": f"prev_hash_mismatch_{entry.id}",
                "total_entries": len(entries),
                "checked_entries": idx + 1,
            }
        prev_hash = entry.hash

    return {
        "valid": True,
        "broken_at": None,
        "total_entries": len(entries),
        "checked_entries": len(entries),
    }


async def verify_entry(db: AsyncSession, entry_id: int) -> dict:
    result = await db.execute(select(AuditLog).where(AuditLog.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        return {"valid": False, "error": "Entry not found"}

    prev_result = await db.execute(
        select(AuditLog).where(AuditLog.id < entry_id).order_by(AuditLog.id.desc()).limit(1)
    )
    prev = prev_result.scalar_one_or_none()
    prev_hash = prev.hash if prev else ""

    expected = _compute_hash(
        prev_hash, entry.action, entry.actor_id or "", entry.created_at.isoformat(), entry.payload
    )
    valid = entry.hash == expected and entry.prev_hash == (prev_hash or None)

    return {
        "valid": valid,
        "entry_id": entry_id,
        "expected_hash": expected,
        "actual_hash": entry.hash,
    }


async def get_audit_logs(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    action_filter: str | None = None,
    actor_filter: str | None = None,
) -> list[AuditLog]:
    query = select(AuditLog)
    if action_filter:
        query = query.where(AuditLog.action == action_filter)
    if actor_filter:
        query = query.where(AuditLog.actor_id == actor_filter)
    query = query.order_by(AuditLog.id.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_chain_stats(db: AsyncSession) -> dict:
    count_result = await db.execute(select(func.count()).select_from(AuditLog))
    total = count_result.scalar_one()

    first_result = await db.execute(select(AuditLog).order_by(AuditLog.id).limit(1))
    first = first_result.scalar_one_or_none()

    last_result = await db.execute(select(AuditLog).order_by(AuditLog.id.desc()).limit(1))
    last = last_result.scalar_one_or_none()

    action_rows = await db.execute(
        select(AuditLog.action, func.count().label("cnt")).group_by(AuditLog.action)
    )
    action_breakdown = {row.action: row.cnt for row in action_rows}

    return {
        "total_entries": total,
        "first_entry_at": first.created_at if first else None,
        "last_entry_at": last.created_at if last else None,
        "action_breakdown": action_breakdown,
    }
