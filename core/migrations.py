# core/migrations.py — PLAGENOR 4.0 Schema Migrations
# Handles JSON → SQLite data migration on first run.
# Ensures backward compatibility when upgrading from JSON-based versions.

from __future__ import annotations
import json
import os
from datetime import datetime, timezone
import config
from core.logger import get_logger

_log = get_logger("migrations")

CURRENT_SCHEMA_VERSION = "4.1.0"  # SQLite version


def _read_json_list(path: str) -> list:
    """Read a JSON file containing a list. Returns [] if missing or invalid."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _read_json_obj(path: str) -> dict:
    """Read a JSON file containing an object. Returns {} if missing or invalid."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _rename_to_backup(path: str):
    """Rename a JSON file to .json.migrated to mark it as imported."""
    if os.path.exists(path):
        bak = path + ".migrated"
        try:
            os.rename(path, bak)
            _log.info("Fichier JSON archivé: %s → %s", path, bak)
        except Exception as e:
            _log.warning("Impossible de renommer %s: %s", path, e)


def _get_schema_version_from_db() -> str:
    """Read schema version from SQLite database."""
    try:
        from core.repository import _get_db
        db = _get_db()
        # Check if schema_version table exists
        row = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
        ).fetchone()
        if not row:
            return "0.0.0"
        row = db.execute("SELECT version FROM schema_version WHERE key='version'").fetchone()
        return row["version"] if row else "0.0.0"
    except Exception:
        return "0.0.0"


def _write_schema_version_to_db(version: str):
    """Write schema version to SQLite database."""
    from core.repository import _get_db
    db = _get_db()
    db.execute(
        "INSERT INTO schema_version (key, version, updated_at) VALUES (?, ?, ?) "
        "ON CONFLICT(key) DO UPDATE SET version=excluded.version, updated_at=excluded.updated_at",
        ("version", version, datetime.now(timezone.utc).isoformat())
    )
    db.commit()


def _table_has_data(table: str) -> bool:
    """Check if a SQLite table has any rows."""
    try:
        from core.repository import _get_db
        db = _get_db()
        row = db.execute(f"SELECT COUNT(*) as c FROM {table}").fetchone()
        return row["c"] > 0
    except Exception:
        return False


def _has_json_files() -> bool:
    """Check if any legacy JSON data files exist."""
    json_files = [
        config.USERS_FILE, config.MEMBERS_FILE, config.SERVICES_FILE,
        config.ACTIVE_REQUESTS_FILE, config.ARCHIVED_REQUESTS_FILE,
        config.INVOICES_FILE, config.AUDIT_LOGS_FILE,
        config.DOCUMENTS_FILE, config.NOTIFICATIONS_FILE,
    ]
    return any(os.path.exists(f) for f in json_files)


# ═══════════════════════════════════════════════════════════════════════════
# JSON → SQLite Migration
# ═══════════════════════════════════════════════════════════════════════════

def _migrate_json_to_sqlite():
    """Import all data from JSON files into SQLite tables.
    Only runs if JSON files exist AND SQLite tables are empty."""
    from core.repository import (
        save_user, save_member, save_service, save_request,
        save_invoice, save_audit_log, save_document, create_notification,
        save_revenue_archive, save_override_log, save_payment_methods,
        _get_db,
    )

    if not _has_json_files():
        _log.info("Aucun fichier JSON détecté, pas de migration nécessaire.")
        return

    _log.info("═══ Début de la migration JSON → SQLite ═══")
    total_migrated = 0

    # ── Users ──
    if not _table_has_data("users"):
        users = _read_json_list(config.USERS_FILE)
        for u in users:
            try:
                save_user(u)
            except Exception as e:
                _log.warning("Erreur migration user %s: %s", u.get("id", "?"), e)
        if users:
            _log.info("  ✓ %d utilisateurs migrés", len(users))
            total_migrated += len(users)
            _rename_to_backup(config.USERS_FILE)

    # ── Members ──
    if not _table_has_data("members"):
        members = _read_json_list(config.MEMBERS_FILE)
        for m in members:
            # Ensure required fields
            m.setdefault("total_points", 0)
            m.setdefault("points_history", [])
            m.setdefault("cheers", [])
            try:
                save_member(m)
            except Exception as e:
                _log.warning("Erreur migration member %s: %s", m.get("id", "?"), e)
        if members:
            _log.info("  ✓ %d analystes migrés", len(members))
            total_migrated += len(members)
            _rename_to_backup(config.MEMBERS_FILE)

    # ── Services ──
    if not _table_has_data("services"):
        services = _read_json_list(config.SERVICES_FILE)
        for s in services:
            # Ensure required fields
            s.setdefault("channel_availability", "BOTH")
            s.setdefault("ibtikar_price", s.get("base_price") or s.get("price") or 0)
            s.setdefault("genoclab_price", s.get("base_price") or s.get("price") or 0)
            s.setdefault("turnaround_days", 7)
            s.setdefault("description", "")
            try:
                save_service(s)
            except Exception as e:
                _log.warning("Erreur migration service %s: %s", s.get("id", "?"), e)
        if services:
            _log.info("  ✓ %d services migrés", len(services))
            total_migrated += len(services)
            _rename_to_backup(config.SERVICES_FILE)

    # ── Active Requests ──
    if not _table_has_data("requests"):
        active = _read_json_list(config.ACTIVE_REQUESTS_FILE)
        for req in active:
            req.setdefault("archived", 0)
            req["archived"] = 0
            req.setdefault("display_id", (req.get("id") or "")[:8].upper())
            req.setdefault("urgency", "Normal")
            req.setdefault("comments", [])
            req.setdefault("history", [])
            if not req.get("title"):
                svc = req.get("service_id") or req.get("service_code") or "Demande"
                req["title"] = f"{svc} — {req.get('display_id', '')}"
            try:
                save_request(req)
            except Exception as e:
                _log.warning("Erreur migration request %s: %s", req.get("id", "?"), e)

        archived = _read_json_list(config.ARCHIVED_REQUESTS_FILE)
        for req in archived:
            req["archived"] = 1
            req.setdefault("display_id", (req.get("id") or "")[:8].upper())
            req.setdefault("urgency", "Normal")
            req.setdefault("comments", [])
            req.setdefault("history", [])
            if not req.get("title"):
                svc = req.get("service_id") or req.get("service_code") or "Demande"
                req["title"] = f"{svc} — {req.get('display_id', '')}"
            try:
                save_request(req)
            except Exception as e:
                _log.warning("Erreur migration archived request %s: %s", req.get("id", "?"), e)

        total_reqs = len(active) + len(archived)
        if total_reqs:
            _log.info("  ✓ %d demandes migrées (%d actives, %d archivées)",
                       total_reqs, len(active), len(archived))
            total_migrated += total_reqs
            _rename_to_backup(config.ACTIVE_REQUESTS_FILE)
            _rename_to_backup(config.ARCHIVED_REQUESTS_FILE)

    # ── Invoices ──
    if not _table_has_data("invoices"):
        invoices = _read_json_list(config.INVOICES_FILE)
        for inv in invoices:
            try:
                save_invoice(inv)
            except Exception as e:
                _log.warning("Erreur migration invoice %s: %s", inv.get("id", "?"), e)
        if invoices:
            _log.info("  ✓ %d factures migrées", len(invoices))
            total_migrated += len(invoices)
            _rename_to_backup(config.INVOICES_FILE)

    # ── Audit Logs ──
    if not _table_has_data("audit_logs"):
        logs = _read_json_list(config.AUDIT_LOGS_FILE)
        for entry in logs:
            try:
                save_audit_log(entry)
            except Exception as e:
                _log.warning("Erreur migration audit log: %s", e)
        if logs:
            _log.info("  ✓ %d entrées d'audit migrées", len(logs))
            total_migrated += len(logs)
            _rename_to_backup(config.AUDIT_LOGS_FILE)

    # ── Documents ──
    if not _table_has_data("documents"):
        docs = _read_json_list(config.DOCUMENTS_FILE)
        for doc in docs:
            try:
                save_document(doc)
            except Exception as e:
                _log.warning("Erreur migration document: %s", e)
        if docs:
            _log.info("  ✓ %d documents migrés", len(docs))
            total_migrated += len(docs)
            _rename_to_backup(config.DOCUMENTS_FILE)

    # ── Notifications ──
    if not _table_has_data("notifications"):
        notifs = _read_json_list(config.NOTIFICATIONS_FILE)
        for n in notifs:
            try:
                # Use raw upsert since create_notification sets read=False
                from core.repository import _upsert
                if not n.get("id"):
                    import uuid
                    n["id"] = str(uuid.uuid4())
                _upsert("notifications", n)
            except Exception as e:
                _log.warning("Erreur migration notification: %s", e)
        if notifs:
            _log.info("  ✓ %d notifications migrées", len(notifs))
            total_migrated += len(notifs)
            _rename_to_backup(config.NOTIFICATIONS_FILE)

    # ── Invoice Sequence ──
    if os.path.exists(config.INVOICE_SEQUENCE_FILE):
        seq = _read_json_obj(config.INVOICE_SEQUENCE_FILE)
        if seq.get("last"):
            try:
                db = _get_db()
                db.execute(
                    "INSERT INTO sequences (key, value) VALUES (?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    ("invoice_last", seq["last"])
                )
                db.commit()
                _log.info("  ✓ Séquence factures migrée: %d", seq["last"])
            except Exception as e:
                _log.warning("Erreur migration séquence factures: %s", e)
        _rename_to_backup(config.INVOICE_SEQUENCE_FILE)

    # ── Request Sequence ──
    if os.path.exists(config.REQUEST_SEQUENCE_FILE):
        seq = _read_json_obj(config.REQUEST_SEQUENCE_FILE)
        if seq:
            try:
                db = _get_db()
                for key, val in seq.items():
                    db.execute(
                        "INSERT INTO sequences (key, value) VALUES (?, ?) "
                        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                        (key, val)
                    )
                db.commit()
                _log.info("  ✓ Séquences demandes migrées: %s", list(seq.keys()))
            except Exception as e:
                _log.warning("Erreur migration séquences: %s", e)
        _rename_to_backup(config.REQUEST_SEQUENCE_FILE)

    # ── Revenue Archives ──
    if not _table_has_data("revenue_archives"):
        if os.path.exists(config.REVENUE_ARCHIVES_FILE):
            archives = _read_json_list(config.REVENUE_ARCHIVES_FILE)
            for arch in archives:
                try:
                    save_revenue_archive(arch)
                except Exception as e:
                    _log.warning("Erreur migration archive revenus: %s", e)
            if archives:
                _log.info("  ✓ %d archives revenus migrées", len(archives))
                total_migrated += len(archives)
            _rename_to_backup(config.REVENUE_ARCHIVES_FILE)

    # ── Override Logs ──
    if not _table_has_data("override_logs"):
        override_path = config.OVERRIDE_LOG_FILE
        if os.path.exists(override_path):
            overrides = _read_json_list(override_path)
            for o in overrides:
                try:
                    save_override_log(o)
                except Exception as e:
                    _log.warning("Erreur migration override log: %s", e)
            if overrides:
                _log.info("  ✓ %d override logs migrés", len(overrides))
            _rename_to_backup(override_path)

    # ── Payment Methods ──
    if not _table_has_data("payment_methods"):
        pm_path = config.PAYMENT_METHODS_FILE
        if os.path.exists(pm_path):
            methods = _read_json_list(pm_path)
            if methods:
                try:
                    save_payment_methods(methods)
                    _log.info("  ✓ %d modes de paiement migrés", len(methods))
                except Exception as e:
                    _log.warning("Erreur migration payment methods: %s", e)
            _rename_to_backup(pm_path)

    # Clean up old schema version JSON file
    old_schema = os.path.join(config.DATA_DIR, "schema_version.json")
    if os.path.exists(old_schema):
        _rename_to_backup(old_schema)

    _log.info("═══ Migration JSON → SQLite terminée: %d éléments migrés ═══", total_migrated)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

def run_migrations():
    """Run all pending migrations. Safe to call multiple times.
    INT-07: Uses BEGIN EXCLUSIVE to prevent concurrent migration runs."""
    current = _get_schema_version_from_db()

    if current == CURRENT_SCHEMA_VERSION:
        _log.info("Schéma à jour (v%s), aucune migration nécessaire.", current)
        return

    _log.info("Migration du schéma: v%s → v%s", current, CURRENT_SCHEMA_VERSION)

    from core.repository import _get_db
    db = _get_db()
    db.execute("BEGIN EXCLUSIVE")
    try:
        # Step 1: Import JSON data into SQLite (if JSON files exist)
        _migrate_json_to_sqlite()

        # Step 2: Write new schema version to DB
        _write_schema_version_to_db(CURRENT_SCHEMA_VERSION)
        db.commit()
    except Exception:
        db.rollback()
        _log.error("Migration failed, rolling back", exc_info=True)
        raise

    _log.info("Migration terminée. Schéma v%s (SQLite)", CURRENT_SCHEMA_VERSION)
