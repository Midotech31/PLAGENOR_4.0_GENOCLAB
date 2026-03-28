# core/repository.py — PLAGENOR 4.0 Data Repository Layer
# SQLite storage. Thread-safe via thread-local connections. No business logic.

from __future__ import annotations
import json, os, sqlite3, threading, uuid, shutil
from datetime import datetime, timezone
from typing import Optional, Any
import config

try:
    import streamlit as st
    _HAS_ST = True
except Exception:
    _HAS_ST = False

# ── Legacy JSON file paths (kept for migration detection) ────────────────────
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

# ── Thread-local SQLite connections ──────────────────────────────────────────
_local = threading.local()

def _get_db() -> sqlite3.Connection:
    """Return a thread-local SQLite connection."""
    conn = getattr(_local, "conn", None)
    if conn is None:
        os.makedirs(config.DATA_DIR, exist_ok=True)
        conn = sqlite3.connect(config.DATABASE_FILE, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        _local.conn = conn
    return conn


# ── JSON field helpers ───────────────────────────────────────────────────────
_JSON_FIELDS_MEMBERS = {"skills", "points_history", "cheers"}
_JSON_FIELDS_REQUESTS = {
    "pricing", "requester", "service_params",
    "sample_table", "comments", "history", "samples", "tasks",
}
_JSON_FIELDS_INVOICES = {"line_items"}
_JSON_FIELDS_AUDIT = {"details"}


def _json_dumps(val) -> str:
    if val is None:
        return "null"
    return json.dumps(val, ensure_ascii=False, default=str)


def _json_loads(val, default=None):
    if val is None:
        return default
    if isinstance(val, (dict, list)):
        return val
    try:
        return json.loads(val)
    except Exception:
        return default


def _row_to_dict(row: sqlite3.Row | None, json_fields: set | None = None) -> dict | None:
    if row is None:
        return None
    d = dict(row)
    # Convert SQLite integer booleans back where appropriate
    for k in ("active", "available", "locked", "read", "archived",
              "self_registered", "receipt_confirmed", "submitted_as_guest",
              "guest_upgraded", "price_modified",
              "appointment_confirmed", "assignment_accepted", "assignment_declined",
              "gift_unlocked", "gift_collected"):
        if k in d and d[k] is not None:
            d[k] = bool(d[k])
    if json_fields:
        for field in json_fields:
            if field in d:
                default = {} if field in ("pricing", "requester", "service_params", "details") else []
                d[field] = _json_loads(d[field], default)
    return d


def _rows_to_list(cursor, json_fields: set | None = None) -> list:
    return [_row_to_dict(row, json_fields) for row in cursor.fetchall()]


# ── Schema creation ──────────────────────────────────────────────────────────
_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL DEFAULT '',
    password_hash TEXT NOT NULL DEFAULT '',
    role TEXT NOT NULL DEFAULT '',
    email TEXT DEFAULT '',
    organization_id TEXT DEFAULT 'ESSBO',
    phone TEXT DEFAULT '',
    student_level TEXT DEFAULT '',
    supervisor TEXT DEFAULT '',
    laboratory TEXT DEFAULT '',
    active INTEGER DEFAULT 1,
    self_registered INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS members (
    id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL DEFAULT '',
    name TEXT DEFAULT '',
    user_id TEXT DEFAULT '',
    max_load INTEGER DEFAULT 5,
    current_load INTEGER DEFAULT 0,
    skills TEXT DEFAULT '[]',
    available INTEGER DEFAULT 1,
    productivity_score REAL DEFAULT 50.0,
    productivity_status TEXT DEFAULT 'NORMAL',
    total_points INTEGER DEFAULT 0,
    points_history TEXT DEFAULT '[]',
    cheers TEXT DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS services (
    id TEXT PRIMARY KEY,
    code TEXT DEFAULT '',
    name TEXT NOT NULL DEFAULT '',
    description TEXT DEFAULT '',
    channel TEXT DEFAULT '',
    channels TEXT DEFAULT '',
    channel_availability TEXT DEFAULT 'BOTH',
    type TEXT DEFAULT 'Analysis',
    base_price REAL DEFAULT 0,
    price REAL DEFAULT 0,
    ibtikar_price REAL DEFAULT 0,
    genoclab_price REAL DEFAULT 0,
    turnaround_days INTEGER DEFAULT 7,
    service_code TEXT DEFAULT '',
    active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT '',
    updated_at TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS requests (
    id TEXT PRIMARY KEY,
    display_id TEXT DEFAULT '',
    title TEXT DEFAULT '',
    description TEXT DEFAULT '',
    channel TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT '',
    urgency TEXT DEFAULT 'Normal',
    service_id TEXT DEFAULT '',
    service_code TEXT DEFAULT '',
    requester_id TEXT DEFAULT '',
    client_id TEXT DEFAULT '',
    assigned_to TEXT DEFAULT '',
    budget_amount REAL DEFAULT 0,
    declared_ibtikar_balance REAL DEFAULT 0,
    quote_amount REAL DEFAULT 0,
    admin_validated_price REAL,
    price_modified INTEGER DEFAULT 0,
    sample_count INTEGER DEFAULT 0,
    requester_name TEXT DEFAULT '',
    client_name TEXT DEFAULT '',
    organization TEXT DEFAULT '',
    contact TEXT DEFAULT '',
    rejection_reason TEXT DEFAULT '',
    report_file TEXT DEFAULT '',
    admin_revision_notes TEXT DEFAULT '',
    ibtikar_form_path TEXT DEFAULT '',
    receipt_confirmed INTEGER DEFAULT 0,
    receipt_confirmed_at TEXT,
    receipt_confirmed_by TEXT,
    service_rating INTEGER,
    rated_at TEXT,
    rating_comment TEXT DEFAULT '',
    submitted_as_guest INTEGER DEFAULT 0,
    guest_token TEXT,
    guest_email TEXT DEFAULT '',
    guest_name TEXT DEFAULT '',
    guest_phone TEXT DEFAULT '',
    guest_token_expires_at TEXT,
    guest_upgraded INTEGER DEFAULT 0,
    archived INTEGER DEFAULT 0,
    archived_at TEXT,
    pricing TEXT DEFAULT '{}',
    requester TEXT DEFAULT '{}',
    service_params TEXT DEFAULT '{}',
    sample_table TEXT DEFAULT '[]',
    comments TEXT DEFAULT '[]',
    history TEXT DEFAULT '[]',
    samples TEXT DEFAULT '[]',
    tasks TEXT DEFAULT '[]',
    payment_reference TEXT DEFAULT '',
    justification TEXT DEFAULT '',
    appointment_date TEXT DEFAULT '',
    updated_by TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT '',
    updated_at TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS invoices (
    id TEXT PRIMARY KEY,
    invoice_number TEXT UNIQUE,
    request_id TEXT DEFAULT '',
    client_id TEXT DEFAULT '',
    client_name TEXT DEFAULT '',
    channel TEXT DEFAULT 'GENOCLAB',
    line_items TEXT DEFAULT '[]',
    subtotal_ht REAL DEFAULT 0,
    vat_rate REAL DEFAULT 0.19,
    vat_amount REAL DEFAULT 0,
    total_ttc REAL DEFAULT 0,
    status TEXT DEFAULT 'GENERATED',
    locked INTEGER DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT '',
    created_by TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    action TEXT NOT NULL DEFAULT '',
    entity_type TEXT DEFAULT '',
    entity_id TEXT DEFAULT '',
    actor_id TEXT DEFAULT '',
    actor_username TEXT DEFAULT '',
    actor_role TEXT DEFAULT '',
    channel TEXT DEFAULT '',
    details TEXT DEFAULT '{}',
    timestamp TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    type TEXT DEFAULT '',
    filename TEXT DEFAULT '',
    filepath TEXT DEFAULT '',
    request_id TEXT DEFAULT '',
    created_at TEXT DEFAULT '',
    created_by TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS notifications (
    id TEXT PRIMARY KEY,
    user_id TEXT DEFAULT '',
    role TEXT DEFAULT '',
    title TEXT DEFAULT '',
    message TEXT DEFAULT '',
    type TEXT DEFAULT 'INFO',
    request_id TEXT DEFAULT '',
    channel TEXT DEFAULT '',
    read INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS sequences (
    key TEXT PRIMARY KEY,
    value INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS revenue_archives (
    id TEXT PRIMARY KEY,
    period TEXT DEFAULT '',
    month TEXT DEFAULT '',
    archived_at TEXT DEFAULT '',
    archived_by TEXT DEFAULT '',
    genoclab_invoices_count INTEGER DEFAULT 0,
    genoclab_total_ht REAL DEFAULT 0,
    genoclab_total_vat REAL DEFAULT 0,
    genoclab_total_ttc REAL DEFAULT 0,
    ibtikar_virtual_revenue REAL DEFAULT 0,
    ibtikar_budget_used REAL DEFAULT 0,
    ibtikar_requests_count INTEGER DEFAULT 0,
    ibtikar_students_count INTEGER DEFAULT 0,
    ibtikar_budget_per_student REAL DEFAULT 200000,
    ibtikar_budget_cap REAL DEFAULT 200000
);

CREATE TABLE IF NOT EXISTS override_logs (
    id TEXT PRIMARY KEY,
    request_id TEXT DEFAULT '',
    actor_id TEXT DEFAULT '',
    actor_username TEXT DEFAULT '',
    amount REAL DEFAULT 0,
    justification TEXT DEFAULT '',
    timestamp TEXT DEFAULT '',
    budget_used_at_time REAL DEFAULT 0,
    budget_cap REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS payment_methods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS login_attempts (
    username TEXT PRIMARY KEY,
    count INTEGER DEFAULT 0,
    locked_until TEXT
);

CREATE TABLE IF NOT EXISTS schema_version (
    key TEXT PRIMARY KEY DEFAULT 'version',
    version TEXT NOT NULL DEFAULT '0.0.0',
    updated_at TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS techniques (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    category TEXT DEFAULT '',
    active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT ''
);
"""

_INDEXES_SQL = """
CREATE INDEX IF NOT EXISTS idx_requests_channel ON requests(channel);
CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status);
CREATE INDEX IF NOT EXISTS idx_requests_requester ON requests(requester_id);
CREATE INDEX IF NOT EXISTS idx_requests_client ON requests(client_id);
CREATE INDEX IF NOT EXISTS idx_requests_assigned ON requests(assigned_to);
CREATE INDEX IF NOT EXISTS idx_requests_archived ON requests(archived);
CREATE INDEX IF NOT EXISTS idx_requests_created ON requests(created_at);
CREATE INDEX IF NOT EXISTS idx_requests_guest_token ON requests(guest_token);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read);
CREATE INDEX IF NOT EXISTS idx_invoices_client ON invoices(client_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_members_user_id ON members(user_id);
CREATE INDEX IF NOT EXISTS idx_requests_channel_status ON requests(channel, status);
CREATE INDEX IF NOT EXISTS idx_requests_channel_archived ON requests(channel, archived);
CREATE INDEX IF NOT EXISTS idx_requests_assigned_status ON requests(assigned_to, status);
"""


_EXTRA_COLUMNS = [
    ("requests", "appointment_proposed_by", "TEXT DEFAULT ''"),
    ("requests", "appointment_confirmed", "INTEGER DEFAULT 0"),
    ("requests", "appointment_confirmed_at", "TEXT DEFAULT ''"),
    ("requests", "assignment_accepted", "INTEGER DEFAULT 0"),
    ("requests", "assignment_accepted_at", "TEXT DEFAULT ''"),
    ("requests", "assignment_declined", "INTEGER DEFAULT 0"),
    ("requests", "assignment_decline_reason", "TEXT DEFAULT ''"),
    ("members", "gift_unlocked", "INTEGER DEFAULT 0"),
    ("members", "gift_image", "TEXT DEFAULT ''"),
    ("members", "gift_collected", "INTEGER DEFAULT 0"),
]


def _ensure_extra_columns():
    """Add missing columns to existing tables (safe for SQLite — ignores if exists)."""
    db = _get_db()
    for table, col, col_type in _EXTRA_COLUMNS:
        try:
            db.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
        except Exception:
            pass  # Column already exists
    db.commit()
    # Clear column cache after adding columns
    _TABLE_COLUMNS.clear()


def _ensure_database():
    """Create all tables and indexes if they don't exist."""
    db = _get_db()
    db.executescript(_SCHEMA_SQL)
    db.executescript(_INDEXES_SQL)
    db.commit()
    _ensure_extra_columns()


def ensure_data_directory():
    """Bootstrap data directory and SQLite database."""
    os.makedirs(config.DATA_DIR, exist_ok=True)
    # OPS-04: Check write permissions
    if not os.access(config.DATA_DIR, os.W_OK):
        raise RuntimeError(
            f"Data directory {config.DATA_DIR} is not writable. "
            f"Check permissions or set PLAGENOR_DATA_DIR."
        )
    os.makedirs(config.BACKUPS_DIR, exist_ok=True)
    _ensure_database()


# ── Table column cache ────────────────────────────────────────────────────────
_TABLE_COLUMNS: dict[str, set] = {}

def _get_table_columns(table: str) -> set:
    if table not in _TABLE_COLUMNS:
        db = _get_db()
        _TABLE_COLUMNS[table] = {r["name"] for r in db.execute(f"PRAGMA table_info({table})").fetchall()}
    return _TABLE_COLUMNS[table]


# ── Generic upsert helper ────────────────────────────────────────────────────
def _upsert(table: str, data: dict, json_fields: set | None = None):
    """Insert or replace a row in the given table. Returns the data dict."""
    db = _get_db()
    # Serialize JSON fields
    row = dict(data)
    if json_fields:
        for f in json_fields:
            if f in row and not isinstance(row[f], str):
                row[f] = _json_dumps(row[f])

    # Get column names the table actually has (cached)
    valid_cols = _get_table_columns(table)

    # Filter to only known columns
    cols = [k for k in row if k in valid_cols]
    vals = [row[k] for k in cols]

    placeholders = ",".join(["?"] * len(cols))
    col_names = ",".join(cols)
    updates = ",".join([f"{c}=excluded.{c}" for c in cols if c != "id"])

    db.execute(
        f"INSERT INTO {table} ({col_names}) VALUES ({placeholders}) "
        f"ON CONFLICT(id) DO UPDATE SET {updates}",
        vals
    )
    db.commit()
    return data


def _get_all(table: str, json_fields: set | None = None,
             where: str = "", params: tuple = ()) -> list:
    db = _get_db()
    sql = f"SELECT * FROM {table}"
    if where:
        sql += f" WHERE {where}"
    return _rows_to_list(db.execute(sql, params), json_fields)


def _get_one(table: str, pk: str, json_fields: set | None = None) -> dict | None:
    db = _get_db()
    row = db.execute(f"SELECT * FROM {table} WHERE id=?", (pk,)).fetchone()
    return _row_to_dict(row, json_fields)


def _delete(table: str, pk: str):
    db = _get_db()
    db.execute(f"DELETE FROM {table} WHERE id=?", (pk,))
    db.commit()


# ═══════════════════════════════════════════════════════════════════════════
# USERS
# ═══════════════════════════════════════════════════════════════════════════
def get_all_users():
    return _get_all("users")

def get_user(user_id):
    return _get_one("users", user_id)

def get_user_by_username(username):
    db = _get_db()
    row = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    return _row_to_dict(row)

def save_user(user):
    if not user.get("id"):
        user["id"] = str(uuid.uuid4())
    if not user.get("created_at"):
        user["created_at"] = datetime.now(timezone.utc).isoformat()
    _upsert("users", user)
    return user

def delete_user(user_id):
    """Soft-delete: set active=False instead of hard delete to preserve referential integrity."""
    user = get_user(user_id)
    if user:
        user["active"] = False
        save_user(user)


# ═══════════════════════════════════════════════════════════════════════════
# MEMBERS
# ═══════════════════════════════════════════════════════════════════════════
def get_all_members():
    return _get_all("members", _JSON_FIELDS_MEMBERS)

def get_member(member_id):
    return _get_one("members", member_id, _JSON_FIELDS_MEMBERS)

def get_member_by_user_id(user_id):
    db = _get_db()
    row = db.execute("SELECT * FROM members WHERE user_id=?", (user_id,)).fetchone()
    return _row_to_dict(row, _JSON_FIELDS_MEMBERS)

def save_member(member):
    if not member.get("id"):
        member["id"] = str(uuid.uuid4())
    if not member.get("created_at"):
        member["created_at"] = datetime.now(timezone.utc).isoformat()
    _upsert("members", member, _JSON_FIELDS_MEMBERS)
    return member

def delete_member(member_id):
    _delete("members", member_id)

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
    rows = _get_all("services")
    # Deserialize channels stored as JSON string
    for s in rows:
        if isinstance(s.get("channels"), str):
            s["channels"] = _json_loads(s["channels"], [])
    return rows

def get_service(service_id):
    s = _get_one("services", service_id)
    if s and isinstance(s.get("channels"), str):
        s["channels"] = _json_loads(s["channels"], [])
    return s

def get_services_for_channel(channel):
    """Get services available for a specific channel (supports multi-channel services)."""
    results = []
    for s in get_all_services():
        channels = s.get("channels", [s.get("channel", "")])
        if channel in channels:
            results.append(s)
    return results

def save_service(service):
    if not service.get("id"):
        service["id"] = str(uuid.uuid4())
    row = dict(service)
    if "channels" in row and not isinstance(row["channels"], str):
        row["channels"] = _json_dumps(row["channels"])
    _upsert("services", row)
    return service


# ═══════════════════════════════════════════════════════════════════════════
# REQUESTS
# ═══════════════════════════════════════════════════════════════════════════
def get_all_active_requests():
    return _get_all("requests", _JSON_FIELDS_REQUESTS, "archived=0")

def get_all_archived_requests():
    return _get_all("requests", _JSON_FIELDS_REQUESTS, "archived=1")

def get_request(request_id):
    return _get_one("requests", request_id, _JSON_FIELDS_REQUESTS)

def save_request(request):
    if not request.get("id"):
        request["id"] = str(uuid.uuid4())
    if not request.get("created_at"):
        request["created_at"] = datetime.now(timezone.utc).isoformat()
    if "archived" not in request:
        request["archived"] = 0
    _upsert("requests", request, _JSON_FIELDS_REQUESTS)
    return request

def archive_request(request_id):
    req = get_request(request_id)
    if not req:
        return None
    # INT-04: Decrement member load if request is non-terminal and assigned
    assigned = req.get("assigned_to")
    if assigned and req.get("status") not in config.TERMINAL_STATES:
        decrement_member_load(assigned)
    req["archived"] = 1
    req["archived_at"] = datetime.now(timezone.utc).isoformat()
    save_request(req)
    return req

def get_requests_by_channel(channel):
    return _get_all("requests", _JSON_FIELDS_REQUESTS,
                     "archived=0 AND channel=?", (channel,))

def get_requests_by_user(user_id):
    return _get_all("requests", _JSON_FIELDS_REQUESTS,
                     "archived=0 AND (requester_id=? OR client_id=?)",
                     (user_id, user_id))

def get_requests_by_member(member_id):
    return _get_all("requests", _JSON_FIELDS_REQUESTS,
                     "archived=0 AND assigned_to=?", (member_id,))


# ═══════════════════════════════════════════════════════════════════════════
# INVOICES
# ═══════════════════════════════════════════════════════════════════════════
def get_all_invoices():
    return _get_all("invoices", _JSON_FIELDS_INVOICES)

def get_invoice(invoice_id):
    return _get_one("invoices", invoice_id, _JSON_FIELDS_INVOICES)

def save_invoice(invoice):
    if not invoice.get("id"):
        invoice["id"] = str(uuid.uuid4())
    if not invoice.get("created_at"):
        invoice["created_at"] = datetime.now(timezone.utc).isoformat()
    _upsert("invoices", invoice, _JSON_FIELDS_INVOICES)
    return invoice

def get_next_invoice_number():
    db = _get_db()
    db.execute("BEGIN IMMEDIATE")
    db.execute(
        "INSERT INTO sequences (key, value) VALUES (?, 0) "
        "ON CONFLICT(key) DO NOTHING",
        ("invoice_last",)
    )
    db.execute("UPDATE sequences SET value = value + 1 WHERE key=?", ("invoice_last",))
    row = db.execute("SELECT value FROM sequences WHERE key=?", ("invoice_last",)).fetchone()
    db.commit()
    last = row["value"] if row else 1
    year = datetime.now().year
    return f"{config.INVOICE_PREFIX}-{year}-{last:04d}"


# ═══════════════════════════════════════════════════════════════════════════
# AUDIT LOGS
# ═══════════════════════════════════════════════════════════════════════════
def get_all_audit_logs():
    return _get_all("audit_logs", _JSON_FIELDS_AUDIT)

def save_audit_log(entry):
    if not entry.get("id"):
        entry["id"] = str(uuid.uuid4())
    if not entry.get("timestamp"):
        entry["timestamp"] = datetime.now(timezone.utc).isoformat()
    _upsert("audit_logs", entry, _JSON_FIELDS_AUDIT)
    return entry


# ═══════════════════════════════════════════════════════════════════════════
# NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════════════════
def get_all_notifications():
    return _get_all("notifications")

def create_notification(notification):
    if not notification.get("id"):
        notification["id"] = str(uuid.uuid4())
    notification["created_at"] = datetime.now(timezone.utc).isoformat()
    notification["read"] = False
    _upsert("notifications", notification)
    return notification

def get_notifications_for_user(user_id):
    user = get_user(user_id)
    user_role = (user or {}).get("role", "")
    db = _get_db()
    rows = db.execute(
        "SELECT * FROM notifications WHERE user_id=? OR role=? ORDER BY created_at DESC LIMIT 200",
        (user_id, user_role)
    ).fetchall()
    return [_row_to_dict(r) for r in rows]

def mark_notification_read(notif_id):
    db = _get_db()
    db.execute("UPDATE notifications SET read=1 WHERE id=?", (notif_id,))
    db.commit()


# ═══════════════════════════════════════════════════════════════════════════
# DOCUMENTS
# ═══════════════════════════════════════════════════════════════════════════
def get_all_documents():
    return _get_all("documents")

def save_document(doc):
    if not doc.get("id"):
        doc["id"] = str(uuid.uuid4())
    _upsert("documents", doc)
    return doc


# ═══════════════════════════════════════════════════════════════════════════
# UTILITY
# ═══════════════════════════════════════════════════════════════════════════
def backup_all(max_backups: int = 30):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(config.BACKUPS_DIR, ts)
    os.makedirs(backup_dir, exist_ok=True)
    if os.path.exists(config.DATABASE_FILE):
        # Use SQLite backup API for safe copy
        dst_path = os.path.join(backup_dir, "plagenor.db")
        src = _get_db()
        dst = sqlite3.connect(dst_path)
        src.backup(dst)
        dst.close()
        # Verify backup integrity
        test = sqlite3.connect(dst_path)
        test.execute("PRAGMA integrity_check").fetchone()
        test.close()
    # Prune old backups — keep last max_backups
    from pathlib import Path
    existing = sorted(Path(config.BACKUPS_DIR).iterdir(), key=lambda p: p.stat().st_mtime)
    for old in existing[:-max_backups]:
        shutil.rmtree(old, ignore_errors=True)
    return backup_dir

def get_platform_stats():
    """Use efficient SQL aggregation instead of loading all records."""
    db = _get_db()

    r = db.execute("SELECT COUNT(*) as c FROM requests WHERE archived=0").fetchone()
    total_requests = r["c"]
    r = db.execute("SELECT COUNT(*) as c FROM requests WHERE archived=1").fetchone()
    total_archived = r["c"]
    r = db.execute("SELECT COUNT(*) as c FROM requests WHERE archived=0 AND channel=?",
                   (config.CHANNEL_IBTIKAR,)).fetchone()
    ibtikar_active = r["c"]
    r = db.execute("SELECT COUNT(*) as c FROM requests WHERE archived=0 AND channel=?",
                   (config.CHANNEL_GENOCLAB,)).fetchone()
    genoclab_active = r["c"]
    r = db.execute("SELECT COUNT(*) as c FROM requests WHERE status='COMPLETED'").fetchone()
    completed = r["c"]
    r = db.execute("SELECT COUNT(*) as c FROM members").fetchone()
    total_members = r["c"]
    r = db.execute("SELECT COUNT(*) as c FROM users").fetchone()
    total_users = r["c"]
    r = db.execute("SELECT COUNT(*) as c FROM invoices").fetchone()
    total_invoices = r["c"]
    r = db.execute("SELECT COALESCE(SUM(total_ttc),0) as s FROM invoices").fetchone()
    total_revenue = r["s"]

    placeholders = ",".join("?" * len(config.REJECTION_STATES))
    r = db.execute(
        f"SELECT COALESCE(SUM(budget_amount),0) as s FROM requests "
        f"WHERE archived=0 AND channel=? AND status NOT IN ({placeholders})",
        (config.CHANNEL_IBTIKAR, *config.REJECTION_STATES)
    ).fetchone()
    ibtikar_budget = r["s"]

    return {
        "total_requests": total_requests,
        "total_archived": total_archived,
        "ibtikar_active": ibtikar_active,
        "genoclab_active": genoclab_active,
        "completed": completed,
        "total_members": total_members,
        "total_users": total_users,
        "total_invoices": total_invoices,
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
    db = _get_db()
    rows = db.execute(
        "SELECT * FROM requests WHERE guest_token=? ORDER BY archived ASC", (token,)
    ).fetchall()
    for row in rows:
        r = _row_to_dict(row, _JSON_FIELDS_REQUESTS)
        if r and r.get("guest_token_expires_at"):
            try:
                expires = datetime.fromisoformat(r["guest_token_expires_at"])
                if datetime.now(timezone.utc) > expires:
                    continue
            except Exception:
                pass
        return r
    return None


def get_requests_by_guest_email(email):
    """Find all requests submitted by a guest email (for account upgrade)."""
    if not email:
        return []
    db = _get_db()
    rows = db.execute(
        "SELECT * FROM requests WHERE submitted_as_guest=1 AND LOWER(guest_email)=LOWER(?)",
        (email,)
    ).fetchall()
    return [_row_to_dict(r, _JSON_FIELDS_REQUESTS) for r in rows]


def link_guest_requests_to_client(email, client_id):
    """Link all guest submissions to a new CLIENT account."""
    db = _get_db()
    cursor = db.execute(
        "UPDATE requests SET client_id=?, requester_id=?, guest_upgraded=1 "
        "WHERE submitted_as_guest=1 AND LOWER(guest_email)=LOWER(?) AND archived=0",
        (client_id, client_id, email)
    )
    db.commit()
    return cursor.rowcount


# ═══════════════════════════════════════════════════════════════════════════
# OVERRIDE LOGS (separate table for permanent record)
# ═══════════════════════════════════════════════════════════════════════════
def get_override_logs():
    return _get_all("override_logs")

def save_override_log(entry):
    if not entry.get("id"):
        entry["id"] = str(uuid.uuid4())
    _upsert("override_logs", entry)


# ═══════════════════════════════════════════════════════════════════════════
# REQUEST SEQUENCE (Readable IDs: IBK-2026-0001 / GCL-2026-0001)
# ═══════════════════════════════════════════════════════════════════════════
def generate_request_id(channel: str) -> str:
    """Generate a human-readable request ID like IBK-2026-0001 or GCL-2026-0001."""
    prefix = "IBK" if channel == config.CHANNEL_IBTIKAR else "GCL"
    year = datetime.now().year
    key = f"{prefix}_{year}"
    db = _get_db()
    db.execute("BEGIN IMMEDIATE")
    db.execute(
        "INSERT INTO sequences (key, value) VALUES (?, 0) ON CONFLICT(key) DO NOTHING",
        (key,)
    )
    db.execute("UPDATE sequences SET value = value + 1 WHERE key=?", (key,))
    row = db.execute("SELECT value FROM sequences WHERE key=?", (key,)).fetchone()
    db.commit()
    last = row["value"] if row else 1
    return f"{prefix}-{year}-{last:04d}"


# ═══════════════════════════════════════════════════════════════════════════
# DELETE SERVICE
# ═══════════════════════════════════════════════════════════════════════════
def delete_service(service_id: str):
    _delete("services", service_id)


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
    db = _get_db()
    rows = db.execute("SELECT name FROM payment_methods WHERE active=1 ORDER BY id").fetchall()
    if not rows:
        return list(config.DEFAULT_PAYMENT_METHODS)
    return [r["name"] for r in rows]


def save_payment_methods(methods: list):
    db = _get_db()
    db.execute("DELETE FROM payment_methods")
    for name in methods:
        db.execute("INSERT OR IGNORE INTO payment_methods (name) VALUES (?)", (name,))
    db.commit()


# ═══════════════════════════════════════════════════════════════════════════
# REVENUE ARCHIVES
# ═══════════════════════════════════════════════════════════════════════════
def get_revenue_archives() -> list:
    return _get_all("revenue_archives")


def save_revenue_archive(archive: dict):
    if not archive.get("id"):
        archive["id"] = str(uuid.uuid4())
    _upsert("revenue_archives", archive)


# ═══════════════════════════════════════════════════════════════════════════
# LOGIN ATTEMPTS (DB-persisted brute-force protection)
# ═══════════════════════════════════════════════════════════════════════════
def get_login_attempts(username: str) -> dict:
    db = _get_db()
    row = db.execute("SELECT * FROM login_attempts WHERE username=?", (username,)).fetchone()
    if row:
        return {"username": row["username"], "count": row["count"], "locked_until": row["locked_until"]}
    return {"username": username, "count": 0, "locked_until": None}

def increment_login_attempts(username: str):
    db = _get_db()
    db.execute(
        "INSERT INTO login_attempts (username, count) VALUES (?, 1) "
        "ON CONFLICT(username) DO UPDATE SET count = count + 1",
        (username,)
    )
    db.commit()

def clear_login_attempts(username: str):
    db = _get_db()
    db.execute("DELETE FROM login_attempts WHERE username=?", (username,))
    db.commit()

def set_lockout(username: str, until: str):
    db = _get_db()
    db.execute(
        "INSERT INTO login_attempts (username, count, locked_until) VALUES (?, 0, ?) "
        "ON CONFLICT(username) DO UPDATE SET locked_until=?",
        (username, until, until)
    )
    db.commit()


# ═══════════════════════════════════════════════════════════════════════════
# TECHNIQUES
# ═══════════════════════════════════════════════════════════════════════════
def get_all_techniques():
    return _get_all("techniques")


def save_technique(technique):
    if not technique.get("id"):
        technique["id"] = str(uuid.uuid4())
    if not technique.get("created_at"):
        technique["created_at"] = datetime.now(timezone.utc).isoformat()
    _upsert("techniques", technique)
    return technique


def delete_technique(technique_id):
    _delete("techniques", technique_id)


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

    def invalidate_caches():
        """Explicitly clear cached data after writes."""
        cached_get_all_services.clear()
        cached_get_all_members.clear()
        cached_get_platform_stats.clear()
else:
    cached_get_all_services = get_all_services
    cached_get_all_members = get_all_members
    cached_get_platform_stats = get_platform_stats

    def invalidate_caches():
        pass
