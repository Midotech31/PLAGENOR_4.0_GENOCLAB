# core/budget_engine.py — PLAGENOR 4.0 Budget Engine
# Hardened budget cap validation for IBTIKAR.
# SUPER_ADMIN override with mandatory justification.

from __future__ import annotations
import os, uuid
from datetime import datetime, timezone
from typing import Optional
import config
from core.exceptions import BudgetExceededError, BudgetOverrideRequiredError


def _get_ibtikar_budget_used(year: Optional[int] = None, requester_id: str = "") -> float:
    """Calculate IBTIKAR budget consumed this year BY A SPECIFIC REQUESTER.
    Budget is 200K DZD per requester per year, NOT a global cap."""
    if year is None:
        year = datetime.now().year
    from core.repository import get_all_active_requests, get_all_archived_requests
    total = 0.0
    for req in get_all_active_requests() + get_all_archived_requests():
        if req.get("channel") != config.CHANNEL_IBTIKAR:
            continue
        if req.get("status") in ("REJECTED", "DRAFT"):
            continue
        # Filter by requester if specified
        if requester_id and req.get("requester_id") != requester_id:
            continue
        created = req.get("created_at", "")
        try:
            req_year = datetime.fromisoformat(created.replace("Z", "+00:00")).year
        except Exception:
            req_year = year
        if req_year == year:
            total += float(req.get("budget_amount", 0))
    return total


def validate_annual_cap(amount: float, actor: dict, request_id: str = "",
                        requester_id: str = "") -> dict:
    """
    Validate that adding `amount` does not exceed the IBTIKAR annual cap
    FOR THE SPECIFIC REQUESTER (200K DZD per student per year).
    Raises BudgetExceededError if exceeded and actor is NOT SUPER_ADMIN.
    Raises BudgetOverrideRequiredError if exceeded and actor IS SUPER_ADMIN.
    """
    used = _get_ibtikar_budget_used(requester_id=requester_id)
    cap = config.IBTIKAR_BUDGET_CAP
    projected = used + amount

    result = {
        "used": used,
        "cap": cap,
        "amount": amount,
        "projected": projected,
        "exceeded": projected > cap,
        "remaining": max(0, cap - used),
        "pct_used": round(used / cap * 100, 1) if cap > 0 else 0,
        "request_id": request_id,
    }

    if not result["exceeded"]:
        result["approved"] = True
        return result

    # Budget exceeded
    if actor.get("role") == config.ROLE_SUPER_ADMIN:
        result["override_possible"] = True
        result["approved"] = False
        raise BudgetOverrideRequiredError(
            f"Budget IBTIKAR dépassé: {projected:,.0f} / {cap:,.0f} DZD. "
            f"Override SUPER_ADMIN possible avec justification."
        )
    else:
        result["override_possible"] = False
        result["approved"] = False
        raise BudgetExceededError(
            f"Budget IBTIKAR dépassé: {projected:,.0f} / {cap:,.0f} DZD. "
            f"Restant: {result['remaining']:,.0f} DZD. "
            f"Seul le SUPER_ADMIN peut autoriser un dépassement."
        )


def approve_with_override(request_id: str, actor: dict, amount: float,
                           justification: str) -> dict:
    """SUPER_ADMIN approves budget override. Permanently logged."""
    if actor.get("role") != config.ROLE_SUPER_ADMIN:
        raise BudgetExceededError("Seul le SUPER_ADMIN peut autoriser un override.")

    if not justification or len(justification.strip()) < 10:
        raise BudgetExceededError(
            "Justification obligatoire (minimum 10 caractères) pour un override budgétaire."
        )

    # Log to override_logs.json (permanent, immutable)
    override_entry = {
        "id": str(uuid.uuid4()),
        "request_id": request_id,
        "actor_id": actor.get("id", ""),
        "actor_username": actor.get("username", ""),
        "amount": amount,
        "justification": justification.strip(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "budget_used_at_time": _get_ibtikar_budget_used(),
        "budget_cap": config.IBTIKAR_BUDGET_CAP,
    }

    _save_override_log(override_entry)

    # Also log in main audit
    from core.audit_engine import log_budget_override
    log_budget_override(request_id, actor, amount, justification)

    return {"approved": True, "override": True, "entry": override_entry}


def _save_override_log(entry: dict):
    """Save override log to SQLite via repository."""
    from core.repository import save_override_log
    save_override_log(entry)


def get_override_logs() -> list:
    """Read all override logs from SQLite."""
    from core.repository import get_override_logs as _repo_get_overrides
    return _repo_get_overrides()


def get_budget_status(requester_id: str = "") -> dict:
    """Get current budget status for display. Per-requester if ID provided."""
    used = _get_ibtikar_budget_used(requester_id=requester_id)
    cap = config.IBTIKAR_BUDGET_CAP
    return {
        "used": used,
        "cap": cap,
        "remaining": max(0, cap - used),
        "pct": round(used / cap * 100, 1) if cap > 0 else 0,
        "overrides": len(get_override_logs()),
    }
