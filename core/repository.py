# core/repository.py — PLAGENOR 4.0 Data Repository Layer
# All JSON file I/O. Thread-safe. No business logic.

from __future__ import annotations
import json, os, threading, uuid, shutil
from datetime import datetime, timezone
from typing import Optional, Any
import config

try:
    import streamlit as st
    _HAS_ST = True
except Exception:
    _HAS_ST = False

# ── File paths ────────────────────────────────────────────────────────────────
USERS_FILE             = config.USERS_FILE
MEMBERS_FILE           = config.MEMBERS_FILE
SERVICES_FILE          = config.SERVICES_FILE
ACTIVE_REQUESTS_FILE   = config.ACTIVE_REQUESTS_FILE
ARCHIVED_REQUESTS_FILE = config.ARCHIVED_REQUESTS_FILE
INVOICES_FILE          = config.INVOICES_FILE
INVOICE_SEQUENCE_FILE  = config.INVOICE_SEQUENCE_FILE
REQUEST_SEQUENCE_FILE  = config.REQUEST_SEQUENCE_FILE
REVENUE_ARCHIVES_FILE  = config.REVENUE_ARCHIVES_FILE
AUDIT_LOGS_FILE        = config.AUDIT_LOGS_FILE
DOCUMENTS_FILE         = config.DOCUMENTS_FILE
NOTIFICATIONS_FILE     = config.NOTIFICATIONS_FILE

ALL_DATA_FILES = [
    USERS_FILE, MEMBERS_FILE, SERVICES_FILE,
    ACTIVE_REQUESTS_FILE, ARCHIVED_REQUESTS_FILE,
    INVOICES_FILE, INVOICE_SEQUENCE_FILE,
    AUDIT_LOGS_FILE, DOCUMENTS_FILE, NOTIFICATIONS_FILE,
]

_LOCKS = {path: threading.Lock() for path in ALL_DATA_FILES}

def _lock_for(path):
    if path not in _LOCKS:
        _LOCKS[path] = threading.Lock()
    return _LOCKS[path]


# ── Low-level I/O ─────────────────────────────────────────────────────────────
def _read_json(path):
    lock = _lock_for(path)
    with lock:
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, Exception):
            return []

def _write_json(path, data):
    lock = _lock_for(path)
    with lock:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        os.replace(tmp, path)

def _read_json_obj(path):
    lock = _lock_for(path)
    with lock:
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

def _write_json_obj(path, data):
    lock = _lock_for(path)
    with lock:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        os.replace(tmp, path)


def ensure_data_directory():
    os.makedirs(config.DATA_DIR, exist_ok=True)
    for path in ALL_DATA_FILES:
        if not os.path.exists(path):
            ext_data = [] if path != INVOICE_SEQUENCE_FILE else {"last": 0}
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(ext_data, f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════════════════
# USERS
# ═══════════════════════════════════════════════════════════════════════════
def get_all_users():
    return _read_json(USERS_FILE)

def get_user(user_id):
    for u in get_all_users():
        if u.get("id") == user_id:
            return u
    return None

def get_user_by_username(username):
    for u in get_all_users():
        if u.get("username") == username:
            return u
    return None

def save_user(user):
    users = get_all_users()
    idx = next((i for i, u in enumerate(users) if u.get("id") == user.get("id")), None)
    if idx is not None:
        users[idx] = user
    else:
        if not user.get("id"):
            user["id"] = str(uuid.uuid4())
        users.append(user)
    _write_json(USERS_FILE, users)
    return user

def delete_user(user_id):
    users = [u for u in get_all_users() if u.get("id") != user_id]
    _write_json(USERS_FILE, users)


# ═══════════════════════════════════════════════════════════════════════════
# MEMBERS
# ═══════════════════════════════════════════════════════════════════════════
def get_all_members():
    return _read_json(MEMBERS_FILE)

def get_member(member_id):
    for m in get_all_members():
        if m.get("id") == member_id:
            return m
    return None

def get_member_by_user_id(user_id):
    for m in get_all_members():
        if m.get("user_id") == user_id:
            return m
    return None

def save_member(member):
    members = get_all_members()
    idx = next((i for i, m in enumerate(members) if m.get("id") == member.get("id")), None)
    if idx is not None:
        members[idx] = member
    else:
        if not member.get("id"):
            member["id"] = str(uuid.uuid4())
        members.append(member)
    _write_json(MEMBERS_FILE, members)
    return member

def delete_member(member_id):
    members = [m for m in get_all_members() if m.get("id") != member_id]
    _write_json(MEMBERS_FILE, members)

def get_available_members_for_service(service_id):
    results = []
    for m in get_all_members():
        if not m.get("available", True):
            continue
        skills = m.get("skills", [])
        if service_id in skills or not skills:
            results.append(m)
    return results

def increment_member_load(member_id):
    m = get_member(member_id)
    if m:
        m["current_load"] = m.get("current_load", 0) + 1
        save_member(m)
    return m

def decrement_member_load(member_id):
    m = get_member(member_id)
    if m:
        m["current_load"] = max(0, m.get("current_load", 0) - 1)
        save_member(m)
    return m


# ═══════════════════════════════════════════════════════════════════════════
# SERVICES
# ═══════════════════════════════════════════════════════════════════════════
def get_all_services():
    return _read_json(SERVICES_FILE)

def get_service(service_id):
    for s in get_all_services():
        if s.get("id") == service_id:
            return s
    return None

def get_services_for_channel(channel):
    """Get services available for a specific channel (supports multi-channel services)."""
    results = []
    for s in get_all_services():
        channels = s.get("channels", [s.get("channel", "")])
        if channel in channels:
            results.append(s)
    return results

def save_service(service):
    services = get_all_services()
    idx = next((i for i, s in enumerate(services) if s.get("id") == service.get("id")), None)
    if idx is not None:
        services[idx] = service
    else:
        if not service.get("id"):
            service["id"] = str(uuid.uuid4())
        services.append(service)
    _write_json(SERVICES_FILE, services)
    return service


# ═══════════════════════════════════════════════════════════════════════════
# REQUESTS
# ═══════════════════════════════════════════════════════════════════════════
def get_all_active_requests():
    return _read_json(ACTIVE_REQUESTS_FILE)

def get_all_archived_requests():
    return _read_json(ARCHIVED_REQUESTS_FILE)

def get_request(request_id):
    for r in get_all_active_requests():
        if r.get("id") == request_id:
            return r
    for r in get_all_archived_requests():
        if r.get("id") == request_id:
            return r
    return None

def save_request(request):
    requests = get_all_active_requests()
    idx = next((i for i, r in enumerate(requests) if r.get("id") == request.get("id")), None)
    if idx is not None:
        requests[idx] = request
    else:
        if not request.get("id"):
            request["id"] = str(uuid.uuid4())
        if not request.get("created_at"):
            request["created_at"] = datetime.now(timezone.utc).isoformat()
        requests.append(request)
    _write_json(ACTIVE_REQUESTS_FILE, requests)
    return request

def archive_request(request_id):
    actives = get_all_active_requests()
    req = None
    remaining = []
    for r in actives:
        if r.get("id") == request_id:
            req = r
        else:
            remaining.append(r)
    if req:
        req["archived_at"] = datetime.now(timezone.utc).isoformat()
        archived = get_all_archived_requests()
        archived.append(req)
        _write_json(ACTIVE_REQUESTS_FILE, remaining)
        _write_json(ARCHIVED_REQUESTS_FILE, archived)
    return req

def get_requests_by_channel(channel):
    return [r for r in get_all_active_requests() if r.get("channel") == channel]

def get_requests_by_user(user_id):
    return [r for r in get_all_active_requests()
            if r.get("requester_id") == user_id or r.get("client_id") == user_id]

def get_requests_by_member(member_id):
    return [r for r in get_all_active_requests() if r.get("assigned_to") == member_id]


# ═══════════════════════════════════════════════════════════════════════════
# INVOICES
# ═══════════════════════════════════════════════════════════════════════════
def get_all_invoices():
    return _read_json(INVOICES_FILE)

def get_invoice(invoice_id):
    for inv in get_all_invoices():
        if inv.get("id") == invoice_id:
            return inv
    return None

def save_invoice(invoice):
    invoices = get_all_invoices()
    idx = next((i for i, inv in enumerate(invoices) if inv.get("id") == invoice.get("id")), None)
    if idx is not None:
        invoices[idx] = invoice
    else:
        if not invoice.get("id"):
            invoice["id"] = str(uuid.uuid4())
        invoices.append(invoice)
    _write_json(INVOICES_FILE, invoices)
    return invoice

def get_next_invoice_number():
    seq = _read_json_obj(INVOICE_SEQUENCE_FILE)
    last = seq.get("last", 0) + 1
    seq["last"] = last
    _write_json_obj(INVOICE_SEQUENCE_FILE, seq)
    year = datetime.now().year
    return f"{config.INVOICE_PREFIX}-{year}-{last:04d}"


# ═══════════════════════════════════════════════════════════════════════════
# AUDIT LOGS
# ═══════════════════════════════════════════════════════════════════════════
def get_all_audit_logs():
    return _read_json(AUDIT_LOGS_FILE)

def save_audit_log(entry):
    logs = get_all_audit_logs()
    if not entry.get("id"):
        entry["id"] = str(uuid.uuid4())
    if not entry.get("timestamp"):
        entry["timestamp"] = datetime.now(timezone.utc).isoformat()
    logs.append(entry)
    _write_json(AUDIT_LOGS_FILE, logs)
    return entry


# ═══════════════════════════════════════════════════════════════════════════
# NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════════════════
def get_all_notifications():
    return _read_json(NOTIFICATIONS_FILE)

def create_notification(notification):
    notifs = get_all_notifications()
    if not notification.get("id"):
        notification["id"] = str(uuid.uuid4())
    notification["created_at"] = datetime.now(timezone.utc).isoformat()
    notification["read"] = False
    notifs.append(notification)
    _write_json(NOTIFICATIONS_FILE, notifs)
    return notification

def get_notifications_for_user(user_id):
    return [n for n in get_all_notifications()
            if n.get("user_id") == user_id or n.get("role") in (
                get_user(user_id) or {}).get("role", "")]

def mark_notification_read(notif_id):
    notifs = get_all_notifications()
    for n in notifs:
        if n.get("id") == notif_id:
            n["read"] = True
            break
    _write_json(NOTIFICATIONS_FILE, notifs)


# ═══════════════════════════════════════════════════════════════════════════
# DOCUMENTS
# ═══════════════════════════════════════════════════════════════════════════
def get_all_documents():
    return _read_json(DOCUMENTS_FILE)

def save_document(doc):
    docs = get_all_documents()
    if not doc.get("id"):
        doc["id"] = str(uuid.uuid4())
    docs.append(doc)
    _write_json(DOCUMENTS_FILE, docs)
    return doc


# ═══════════════════════════════════════════════════════════════════════════
# UTILITY
# ═══════════════════════════════════════════════════════════════════════════
def backup_all():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(config.BACKUPS_DIR, ts)
    os.makedirs(backup_dir, exist_ok=True)
    for path in ALL_DATA_FILES:
        if os.path.exists(path):
            shutil.copy2(path, os.path.join(backup_dir, os.path.basename(path)))
    return backup_dir

def get_platform_stats():
    active = get_all_active_requests()
    archived = get_all_archived_requests()
    members = get_all_members()
    users = get_all_users()
    invoices = get_all_invoices()

    ibtikar_active   = [r for r in active if r.get("channel") == config.CHANNEL_IBTIKAR]
    genoclab_active  = [r for r in active if r.get("channel") == config.CHANNEL_GENOCLAB]
    completed        = [r for r in active + archived if r.get("status") == "COMPLETED"]

    total_revenue = sum(inv.get("total_ttc", 0) for inv in invoices)
    ibtikar_budget = sum(r.get("budget_amount", 0) for r in ibtikar_active
                         if r.get("status") not in config.REJECTION_STATES)

    return {
        "total_requests": len(active),
        "total_archived": len(archived),
        "ibtikar_active": len(ibtikar_active),
        "genoclab_active": len(genoclab_active),
        "completed": len(completed),
        "total_members": len(members),
        "total_users": len(users),
        "total_invoices": len(invoices),
        "total_revenue": total_revenue,
        "ibtikar_budget_used": ibtikar_budget,
        "ibtikar_budget_cap": config.IBTIKAR_BUDGET_CAP,
        "ibtikar_budget_pct": round(ibtikar_budget / config.IBTIKAR_BUDGET_CAP * 100, 1) if config.IBTIKAR_BUDGET_CAP > 0 else 0,
    }


# ═══════════════════════════════════════════════════════════════════════════
# GUEST TOKENS
# ═══════════════════════════════════════════════════════════════════════════
def get_request_by_guest_token(token):
    """Find a request by its guest tracking token."""
    if not token:
        return None
    for r in get_all_active_requests():
        if r.get("guest_token") == token:
            if r.get("guest_token_expires_at"):
                try:
                    expires = datetime.fromisoformat(r["guest_token_expires_at"])
                    if datetime.now(timezone.utc) > expires:
                        continue  # Token expired, skip
                except Exception:
                    pass
            return r
    for r in get_all_archived_requests():
        if r.get("guest_token") == token:
            if r.get("guest_token_expires_at"):
                try:
                    expires = datetime.fromisoformat(r["guest_token_expires_at"])
                    if datetime.now(timezone.utc) > expires:
                        continue  # Token expired, skip
                except Exception:
                    pass
            return r
    return None


def get_requests_by_guest_email(email):
    """Find all requests submitted by a guest email (for account upgrade)."""
    if not email:
        return []
    results = []
    for r in get_all_active_requests() + get_all_archived_requests():
        if r.get("submitted_as_guest") and r.get("guest_email", "").lower() == email.lower():
            results.append(r)
    return results


def link_guest_requests_to_client(email, client_id):
    """Link all guest submissions to a new CLIENT account."""
    requests = get_all_active_requests()
    updated = 0
    for r in requests:
        if r.get("submitted_as_guest") and r.get("guest_email", "").lower() == email.lower():
            r["client_id"] = client_id
            r["requester_id"] = client_id
            r["guest_upgraded"] = True
            updated += 1
    if updated:
        _write_json(ACTIVE_REQUESTS_FILE, requests)
    return updated


# ═══════════════════════════════════════════════════════════════════════════
# OVERRIDE LOGS (separate file for permanent record)
# ═══════════════════════════════════════════════════════════════════════════
def get_override_logs():
    path = config.OVERRIDE_LOG_FILE
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_override_log(entry):
    path = config.OVERRIDE_LOG_FILE
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    logs = get_override_logs()
    logs.append(entry)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2, default=str)


# ═══════════════════════════════════════════════════════════════════════════
# REQUEST SEQUENCE (Readable IDs: IBK-2026-0001 / GCL-2026-0001)
# ═══════════════════════════════════════════════════════════════════════════
def generate_request_id(channel: str) -> str:
    """Generate a human-readable request ID like IBK-2026-0001 or GCL-2026-0001."""
    prefix = "IBK" if channel == config.CHANNEL_IBTIKAR else "GCL"
    year = datetime.now().year
    seq = _read_json_obj(REQUEST_SEQUENCE_FILE)
    key = f"{prefix}_{year}"
    last = seq.get(key, 0) + 1
    seq[key] = last
    _write_json_obj(REQUEST_SEQUENCE_FILE, seq)
    return f"{prefix}-{year}-{last:04d}"


# ═══════════════════════════════════════════════════════════════════════════
# DELETE SERVICE
# ═══════════════════════════════════════════════════════════════════════════
def delete_service(service_id: str):
    services = [s for s in get_all_services() if s.get("id") != service_id]
    _write_json(SERVICES_FILE, services)


# ═══════════════════════════════════════════════════════════════════════════
# POINTS & CHEERS SYSTEM
# ═══════════════════════════════════════════════════════════════════════════
def add_points_to_member(member_id: str, points: int, reason: str, actor: dict):
    m = get_member(member_id)
    if not m:
        return None
    m["total_points"] = m.get("total_points", 0) + points
    if "points_history" not in m:
        m["points_history"] = []
    m["points_history"].append({
        "points": points,
        "reason": reason,
        "awarded_by": actor.get("id", ""),
        "awarded_by_name": actor.get("full_name", actor.get("username", "")),
        "at": datetime.now(timezone.utc).isoformat(),
    })
    save_member(m)
    return m


def add_cheer_to_member(member_id: str, cheer_text: str, actor: dict):
    m = get_member(member_id)
    if not m:
        return None
    if "cheers" not in m:
        m["cheers"] = []
    m["cheers"].append({
        "message": cheer_text,
        "from": actor.get("full_name", actor.get("username", "")),
        "from_id": actor.get("id", ""),
        "at": datetime.now(timezone.utc).isoformat(),
    })
    save_member(m)
    return m


def get_member_points(member_id: str) -> dict:
    m = get_member(member_id)
    if not m:
        return {"total_points": 0, "points_history": [], "cheers": []}
    return {
        "total_points": m.get("total_points", 0),
        "points_history": m.get("points_history", []),
        "cheers": m.get("cheers", []),
    }


# ═══════════════════════════════════════════════════════════════════════════
# COMMENTS PER REQUEST
# ═══════════════════════════════════════════════════════════════════════════
def add_comment_to_request(request_id: str, comment_text: str, actor: dict, step: str = "") -> dict | None:
    """Append a comment to a request's comments list."""
    req = get_request(request_id)
    if not req:
        return None
    if "comments" not in req:
        req["comments"] = []
    comment = {
        "id": str(uuid.uuid4()),
        "text": comment_text,
        "author_id": actor.get("id", ""),
        "author_name": actor.get("full_name", actor.get("username", "")),
        "step": step or req.get("status", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    req["comments"].append(comment)
    save_request(req)
    return comment


def get_request_comments(request_id: str) -> list:
    """Get all comments for a request."""
    req = get_request(request_id)
    if not req:
        return []
    return req.get("comments", [])


# ═══════════════════════════════════════════════════════════════════════════
# PAYMENT METHODS
# ═══════════════════════════════════════════════════════════════════════════
def get_payment_methods() -> list:
    path = config.PAYMENT_METHODS_FILE
    if not os.path.exists(path):
        return list(config.DEFAULT_PAYMENT_METHODS)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else list(config.DEFAULT_PAYMENT_METHODS)
    except Exception:
        return list(config.DEFAULT_PAYMENT_METHODS)


def save_payment_methods(methods: list):
    path = config.PAYMENT_METHODS_FILE
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(methods, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


# ═══════════════════════════════════════════════════════════════════════════
# REVENUE ARCHIVES
# ═══════════════════════════════════════════════════════════════════════════
def get_revenue_archives() -> list:
    path = REVENUE_ARCHIVES_FILE
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_revenue_archive(archive: dict):
    path = REVENUE_ARCHIVES_FILE
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    archives = get_revenue_archives()
    archives.append(archive)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(archives, f, ensure_ascii=False, indent=2, default=str)
    os.replace(tmp, path)


# ═══════════════════════════════════════════════════════════════════════════
# CACHED WRAPPERS (st.cache_data with short TTL for dashboard reads)
# ═══════════════════════════════════════════════════════════════════════════
if _HAS_ST:
    @st.cache_data(ttl=30)
    def cached_get_all_services():
        return get_all_services()

    @st.cache_data(ttl=30)
    def cached_get_all_members():
        return get_all_members()

    @st.cache_data(ttl=30)
    def cached_get_platform_stats():
        return get_platform_stats()
else:
    cached_get_all_services = get_all_services
    cached_get_all_members = get_all_members
    cached_get_platform_stats = get_platform_stats
