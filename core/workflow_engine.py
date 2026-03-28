# core/workflow_engine.py — PLAGENOR 4.0 Workflow Engine
# ALL transitions go through here. Uses state_machine.py for validation.
# No direct DB mutation outside this engine.

from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
import config
from core.exceptions import (
    InvalidTransitionError, RequestNotFoundError,
    WorkflowError, AuthorizationError,
)
from core.state_machine import (
    validate_transition as sm_validate,
    get_allowed_next_states,
    is_terminal,
)
from core.repository import (
    get_request, save_request, get_member,
    increment_member_load, decrement_member_load,
    create_notification, _get_db,
)
from core.audit_engine import log_workflow_transition
from core.logger import get_logger

_log = get_logger("workflow_engine")


def get_allowed_transitions(request: dict) -> set:
    """Get allowed next states for a request from the state machine."""
    channel = request.get("channel", "")
    current = request.get("status", "")
    try:
        return get_allowed_next_states(channel, current)
    except Exception:
        _log.warning("Failed to get allowed transitions for %s/%s", channel, current, exc_info=True)
        return set()


def transition(request_id: str, to_state: str, actor: dict, **kwargs) -> dict:
    """
    Execute a workflow transition. Enforces:
    1. State machine validation (no skips)
    2. Role authorization
    3. Audit logging
    4. Notification dispatch
    """
    req = get_request(request_id)
    if not req:
        raise RequestNotFoundError(f"Demande {request_id} introuvable")

    from_state = req.get("status", "")
    channel = req.get("channel", "")

    # ── 1. STATE MACHINE VALIDATION (strict, no bypass) ───────────────────
    sm_validate(channel, from_state, to_state)

    # ── 2. ROLE CHECK (SUPER_ADMIN can always transition) ─────────────────
    role = actor.get("role", "")
    if role != config.ROLE_SUPER_ADMIN:
        _check_role_permission(channel, to_state, role)

    # ── INT-03: Wrap state update + side effects in a single transaction ──
    db = _get_db()
    db.execute("BEGIN IMMEDIATE")
    try:
        # ── 3. UPDATE STATE ───────────────────────────────────────────────
        req["status"] = to_state
        req["updated_at"] = datetime.now(timezone.utc).isoformat()
        req["updated_by"] = actor.get("id", "")

        # ── 4. HISTORY ────────────────────────────────────────────────────
        req.setdefault("history", []).append({
            "from": from_state,
            "to": to_state,
            "by": actor.get("username", ""),
            "at": req["updated_at"],
            "details": kwargs.get("details", {}),
        })

        # ── 5. SIDE EFFECTS ──────────────────────────────────────────────
        # Assignment
        if to_state == "ASSIGNED" and kwargs.get("member_id"):
            req["assigned_to"] = kwargs["member_id"]
            increment_member_load(kwargs["member_id"])

        # Unassignment on backward move (force_transition only — normal flow is forward-only)
        if from_state == "ASSIGNED" and to_state not in (
            "SAMPLE_RECEIVED", "ANALYSIS_STARTED", "ANALYSIS_FINISHED"
        ):
            if req.get("assigned_to"):
                decrement_member_load(req["assigned_to"])
                req["assigned_to"] = None

        # Completion releases member load
        if to_state in ("COMPLETED", "CLOSED", "ARCHIVED") and req.get("assigned_to"):
            decrement_member_load(req["assigned_to"])

        # Store extra kwargs on request
        for key in ("rejection_reason", "quote_amount", "appointment_date",
                    "report_file", "budget_amount", "justification",
                    "payment_reference", "guest_token"):
            if key in kwargs:
                req[key] = kwargs[key]

        # Set guest token expiration (90 days)
        if "guest_token" in kwargs:
            req["guest_token_expires_at"] = (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()

        # ── 6. SAVE ──────────────────────────────────────────────────────
        save_request(req)
        db.commit()
    except Exception:
        db.rollback()
        raise

    # ── 7. AUDIT LOG ─────────────────────────────────────────────────────
    log_workflow_transition(req, from_state, to_state, actor, kwargs.get("details"))

    # ── 8. NOTIFICATIONS ─────────────────────────────────────────────────
    _send_notifications(req, to_state, actor)

    return req


def force_transition(request_id: str, to_state: str, actor: dict,
                     reason: str = "") -> dict:
    """SUPER_ADMIN forced transition — bypasses state machine graph."""
    if actor.get("role") != config.ROLE_SUPER_ADMIN:
        raise AuthorizationError("Seul le SUPER_ADMIN peut forcer une transition.")
    if not reason or len(reason.strip()) < 10:
        raise AuthorizationError("Justification requise (min 10 caractères) pour une transition forcée.")

    req = get_request(request_id)
    if not req:
        raise RequestNotFoundError(f"Demande {request_id} introuvable")

    from_state = req.get("status", "")
    req["status"] = to_state
    req["updated_at"] = datetime.now(timezone.utc).isoformat()
    req["updated_by"] = actor.get("id", "")

    req.setdefault("history", []).append({
        "from": from_state, "to": to_state,
        "by": actor.get("username", ""),
        "at": req["updated_at"],
        "forced": True, "reason": reason,
    })

    save_request(req)
    log_workflow_transition(req, from_state, to_state, actor, {
        "forced": True, "reason": reason,
    })
    return req


def _check_role_permission(channel: str, to_state: str, role: str):
    """Check if role is allowed to trigger a transition to to_state.
    ARCH-02: Uses config.IBTIKAR_TRANSITION_ROLES / GENOCLAB_TRANSITION_ROLES
    as single source of truth."""
    role_map = (config.IBTIKAR_TRANSITION_ROLES if channel == config.CHANNEL_IBTIKAR
                else config.GENOCLAB_TRANSITION_ROLES)
    allowed_roles = role_map.get(to_state, [])

    # Empty list = any role can trigger
    if allowed_roles and role not in allowed_roles:
        raise AuthorizationError(
            f"Rôle {role} non autorisé pour la transition vers {to_state}. "
            f"Rôles autorisés: {', '.join(allowed_roles)}"
        )


def _send_notifications(req: dict, to_state: str, actor: dict):
    """Send notifications on state transitions."""
    try:
        from services.notification_service import notify_workflow_transition
        notify_workflow_transition(req, to_state, actor)
    except Exception:
        _log.warning("Failed to send notifications for %s -> %s", req.get("id", ""), to_state, exc_info=True)
