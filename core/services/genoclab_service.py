# core/services/genoclab_service.py — PLAGENOR 4.0 GENOCLAB Service Layer
# Business logic for GENOCLAB requests. Called from dashboards, never bypassed.

from __future__ import annotations
from datetime import datetime, timezone
import uuid
import config
from core.exceptions import ValidationError
from core.repository import save_request
from core.audit_engine import log_action


def submit_genoclab_request(data: dict, actor: dict) -> dict:
    """Create and save a new GENOCLAB request. Server-side validation."""
    # Validate required fields
    if not data.get("title", "").strip():
        raise ValidationError("Le titre est obligatoire.")
    if not data.get("service_code", "") and not data.get("service_id", ""):
        raise ValidationError("Le service est obligatoire.")
    if not data.get("description", "").strip():
        raise ValidationError("La description est obligatoire.")

    # Validate client info
    if not actor.get("id") and not data.get("client_name", "").strip():
        raise ValidationError("Les informations du client sont obligatoires.")

    # Validate samples if provided
    samples = data.get("sample_table", [])
    pricing = data.get("pricing", {})

    now = datetime.now(timezone.utc).isoformat()
    request = {
        "id": data.get("id") or str(uuid.uuid4()),
        "title": data.get("title", "").strip(),
        "description": data.get("description", "").strip(),
        "channel": config.CHANNEL_GENOCLAB,
        "status": "REQUEST_CREATED",
        "service_code": data.get("service_code", data.get("service_id", "")),
        "service_id": data.get("service_id", data.get("service_code", "")),
        "client_id": actor.get("id", ""),
        "requester_id": actor.get("id", ""),
        "client_name": actor.get("full_name", data.get("client_name", "")),
        "organization": data.get("organization", ""),
        "contact": data.get("contact", ""),
        "urgency": data.get("urgency", "Normal"),
        "service_params": data.get("service_params", {}),
        "sample_table": samples,
        "pricing": pricing,
        "quote_amount": pricing.get("total", 0) if pricing else 0,
        "sample_count": pricing.get("number_of_units", len(samples)) if pricing else len(samples),
        "created_at": now,
        "updated_at": now,
        "history": [{"from": None, "to": "REQUEST_CREATED",
                     "by": actor.get("username", ""), "at": now}],
    }

    saved = save_request(request)
    log_action("REQUEST_CREATED", "REQUEST", saved["id"], actor=actor,
               details={"title": data.get("title"), "channel": "GENOCLAB",
                        "service_code": request["service_code"]},
               channel="GENOCLAB")
    return saved
