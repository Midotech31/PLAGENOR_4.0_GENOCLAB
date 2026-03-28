# core/audit_engine.py — PLAGENOR 4.0 Audit Engine
# Every action must be logged immutably.

from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Optional
import uuid
from core.repository import save_audit_log, get_all_audit_logs
from core.logger import get_logger

_log = get_logger("audit_engine")


def log_action(
    action: str,
    entity_type: str,
    entity_id: str,
    actor: Optional[dict] = None,
    details: Optional[dict] = None,
    channel: Optional[str] = None,
) -> dict:
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "entity_type": entity_type,
        "entity_id": str(entity_id),
        "actor_id": (actor or {}).get("id", "system"),
        "actor_username": (actor or {}).get("username", "system"),
        "actor_role": (actor or {}).get("role", "SYSTEM"),
        "details": details or {},
        "channel": channel,
    }
    try:
        save_audit_log(entry)
    except Exception:
        _log.warning("Failed to save audit log: action=%s entity=%s", action, entity_id, exc_info=True)
    return entry


def log_workflow_transition(request: dict, from_state: str, to_state: str,
                            actor: dict, details: Optional[dict] = None) -> dict:
    return log_action(
        action=f"TRANSITION:{from_state}->{to_state}",
        entity_type="REQUEST",
        entity_id=request.get("id", ""),
        actor=actor,
        details={
            "from_state": from_state,
            "to_state": to_state,
            "channel": request.get("channel", ""),
            **(details or {}),
        },
        channel=request.get("channel"),
    )


def log_financial_action(action: str, entity_id: str, actor: dict,
                         amount: float = 0, details: Optional[dict] = None) -> dict:
    return log_action(
        action=f"FINANCIAL:{action}",
        entity_type="FINANCIAL",
        entity_id=entity_id,
        actor=actor,
        details={"amount": amount, **(details or {})},
    )


def log_budget_override(request_id: str, actor: dict, amount: float,
                        justification: str) -> dict:
    return log_action(
        action="BUDGET_OVERRIDE",
        entity_type="REQUEST",
        entity_id=request_id,
        actor=actor,
        details={
            "amount": amount,
            "justification": justification,
            "override_type": "IBTIKAR_ANNUAL_CAP",
            "permanent_record": True,
        },
        channel="IBTIKAR",
    )


def safe_get_all_audit_logs() -> list:
    try:
        return get_all_audit_logs() or []
    except Exception:
        _log.warning("Failed to retrieve audit logs", exc_info=True)
        return []


def get_audit_logs_for_entity(entity_id: str) -> list:
    return [log for log in safe_get_all_audit_logs()
            if log.get("entity_id") == entity_id]


def get_audit_logs_by_action(action: str) -> list:
    return [log for log in safe_get_all_audit_logs()
            if action in log.get("action", "")]


def get_audit_logs_by_user(user_id: str) -> list:
    return [log for log in safe_get_all_audit_logs()
            if log.get("actor_id") == user_id]
