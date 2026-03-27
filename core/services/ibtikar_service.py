# core/services/ibtikar_service.py — PLAGENOR 4.0 IBTIKAR Service Layer
# Business logic for IBTIKAR requests. Called from dashboards, never bypassed.

from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
import uuid
import config
from core.exceptions import (
    BudgetExceededError, BudgetOverrideRequiredError,
    ValidationError, WorkflowError,
)
from core.budget_engine import validate_annual_cap, approve_with_override
from core.state_machine import validate_ibtikar_transition
from core.repository import get_request, save_request
from core.audit_engine import log_action, log_workflow_transition


def submit_ibtikar_request(data: dict, actor: dict) -> dict:
    """Create and save a new IBTIKAR request. Server-side validation."""
    # Validate required fields
    if not data.get("title", "").strip():
        raise ValidationError("Le titre est obligatoire.")
    if not data.get("service_id", "") and not data.get("service_code", ""):
        raise ValidationError("Le service est obligatoire.")
    if not data.get("requester") and not data.get("requester_name"):
        raise ValidationError("Les informations du demandeur sont obligatoires.")

    # Validate requester fields
    requester = data.get("requester", {})
    if requester:
        for field in ("full_name", "institution", "email"):
            if not requester.get(field, "").strip():
                raise ValidationError(f"Champ demandeur obligatoire manquant: {field}")

    # Validate sample table if present
    samples = data.get("sample_table", [])
    if samples:
        for i, s in enumerate(samples):
            if not s.get("sample_code", "").strip() and not any(
                v for k, v in s.items() if k != "_id" and v
            ):
                raise ValidationError(f"Échantillon #{i+1} est vide.")

    now = datetime.now(timezone.utc).isoformat()
    request = {
        "id": data.get("id") or str(uuid.uuid4()),
        "title": data.get("title", "").strip(),
        "description": data.get("description", "").strip(),
        "channel": config.CHANNEL_IBTIKAR,
        "status": "SUBMITTED",
        "service_code": data.get("service_code", data.get("service_id", "")),
        "service_id": data.get("service_id", data.get("service_code", "")),
        "requester_id": actor.get("id", ""),
        "requester_name": actor.get("full_name", actor.get("username", "")),
        "requester": requester,
        "service_params": data.get("service_params", {}),
        "sample_table": samples,
        "pricing": data.get("pricing", {}),
        "budget_amount": float(data.get("budget_amount", 0)),
        "sample_count": int(data.get("sample_count", len(samples) or 1)),
        "created_at": now,
        "updated_at": now,
        "history": [{"from": None, "to": "SUBMITTED", "by": actor.get("username", ""), "at": now}],
    }

    saved = save_request(request)
    log_action("REQUEST_CREATED", "REQUEST", saved["id"], actor=actor,
               details={"title": data.get("title"), "channel": "IBTIKAR",
                        "service_code": request["service_code"],
                        "budget": request["budget_amount"]},
               channel="IBTIKAR")

    # Auto-generate IBTIKAR DOCX form
    try:
        from services.document_service import generate_ibtikar_form
        from services.registry_loader import get_service_def
        svc = get_service_def(request["service_code"])
        path = generate_ibtikar_form(saved, svc, actor)
        if path:
            saved["ibtikar_form_path"] = path
            save_request(saved)
    except Exception:
        pass

    return saved


def validate_pedagogique(request_id: str, actor: dict, approved: bool,
                          reason: str = "") -> dict:
    """Pedagogical validation step. Called by PLATFORM_ADMIN or SUPER_ADMIN."""
    req = get_request(request_id)
    if not req:
        raise WorkflowError(f"Demande {request_id} introuvable.")

    from_state = req.get("status", "")
    to_state = "VALIDATION_PEDAGOGIQUE" if approved else "REJECTED"

    # Strict state machine check
    validate_ibtikar_transition(from_state, to_state)

    req["status"] = to_state
    req["updated_at"] = datetime.now(timezone.utc).isoformat()
    req["updated_by"] = actor.get("id", "")
    if not approved:
        req["rejection_reason"] = reason

    req.setdefault("history", []).append({
        "from": from_state, "to": to_state,
        "by": actor.get("username", ""),
        "at": req["updated_at"],
        "details": {"approved": approved, "reason": reason},
    })

    save_request(req)
    log_workflow_transition(req, from_state, to_state, actor,
                           {"approved": approved, "reason": reason})
    return req


def validate_finance(request_id: str, actor: dict, approved: bool,
                      reason: str = "", override_justification: str = "") -> dict:
    """
    Financial validation step. Budget cap checked HERE.
    Called by FINANCE role or SUPER_ADMIN.
    """
    req = get_request(request_id)
    if not req:
        raise WorkflowError(f"Demande {request_id} introuvable.")

    from_state = req.get("status", "")

    if not approved:
        to_state = "REJECTED"
        validate_ibtikar_transition(from_state, to_state)
        req["status"] = to_state
        req["rejection_reason"] = reason
        req["updated_at"] = datetime.now(timezone.utc).isoformat()
        req["updated_by"] = actor.get("id", "")
        req.setdefault("history", []).append({
            "from": from_state, "to": to_state,
            "by": actor.get("username", ""), "at": req["updated_at"],
        })
        save_request(req)
        log_workflow_transition(req, from_state, to_state, actor, {"reason": reason})
        return req

    # Budget check at VALIDATION_FINANCE (per-requester cap)
    to_state = "VALIDATION_FINANCE"
    validate_ibtikar_transition(from_state, to_state)

    amount = float(req.get("budget_amount", 0))
    requester_id = req.get("requester_id", "")
    try:
        validate_annual_cap(amount, actor, request_id, requester_id=requester_id)
    except BudgetOverrideRequiredError:
        # SUPER_ADMIN can override with justification
        if override_justification:
            approve_with_override(request_id, actor, amount, override_justification)
        else:
            raise
    except BudgetExceededError:
        raise

    req["status"] = to_state
    req["updated_at"] = datetime.now(timezone.utc).isoformat()
    req["updated_by"] = actor.get("id", "")
    req["budget_validated"] = True
    req["budget_validated_by"] = actor.get("id", "")
    req["budget_validated_at"] = req["updated_at"]

    req.setdefault("history", []).append({
        "from": from_state, "to": to_state,
        "by": actor.get("username", ""), "at": req["updated_at"],
        "details": {"budget_amount": amount, "override": bool(override_justification)},
    })

    save_request(req)
    log_workflow_transition(req, from_state, to_state, actor,
                           {"budget_amount": amount})

    # ── AUTO-TRIGGER: Generate Platform Note and advance to PLATFORM_NOTE_GENERATED ──
    try:
        note_state = "PLATFORM_NOTE_GENERATED"
        validate_ibtikar_transition(to_state, note_state)
        req["status"] = note_state
        req["updated_at"] = datetime.now(timezone.utc).isoformat()
        req.setdefault("history", []).append({
            "from": to_state, "to": note_state,
            "by": "SYSTEM", "at": req["updated_at"],
            "details": {"auto_generated": True},
        })
        save_request(req)
        log_workflow_transition(req, to_state, note_state, actor,
                               {"auto_generated": True})
        # Generate the actual platform note document
        try:
            from services.document_service import generate_platform_note
            from services.registry_loader import get_service_def
            svc = get_service_def(req.get("service_code", ""))
            path = generate_platform_note(req, actor, svc)
            if path:
                req["platform_note_path"] = path
                save_request(req)
        except Exception:
            pass
    except Exception:
        pass  # If auto-transition fails, admin can do it manually

    return req
