# core/migrations.py — PLAGENOR 4.0 Schema Migrations
# Ensures backward compatibility when loading old data.

from __future__ import annotations
import json
import os
from datetime import datetime, timezone
import config
from core.logger import get_logger

_log = get_logger("migrations")

CURRENT_SCHEMA_VERSION = "4.0.0"
SCHEMA_VERSION_FILE = os.path.join(config.DATA_DIR, "schema_version.json")


def _read_schema_version() -> str:
    if not os.path.exists(SCHEMA_VERSION_FILE):
        return "0.0.0"
    try:
        with open(SCHEMA_VERSION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("version", "0.0.0")
    except Exception:
        return "0.0.0"


def _write_schema_version(version: str):
    os.makedirs(os.path.dirname(os.path.abspath(SCHEMA_VERSION_FILE)), exist_ok=True)
    with open(SCHEMA_VERSION_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "version": version,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }, f, ensure_ascii=False, indent=2)


def _read_json_list(path: str) -> list:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _write_json_list(path: str, data: list):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    os.replace(tmp, path)


def _ensure_file_exists(path: str, default_content):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default_content, f, ensure_ascii=False, indent=2)
        _log.info("Fichier créé: %s", path)


def _migrate_requests(path: str) -> int:
    """Ensure all requests have display_id, urgency, title, and comments fields."""
    items = _read_json_list(path)
    changed = 0
    for req in items:
        if "display_id" not in req or not req.get("display_id"):
            req["display_id"] = (req.get("id") or "")[:8].upper()
            changed += 1
        if "urgency" not in req or req.get("urgency") is None:
            req["urgency"] = "Normal"
            changed += 1
        if "title" not in req or not req.get("title"):
            svc = req.get("service_id") or req.get("service_code") or "Demande"
            req["title"] = f"{svc} — {req.get('display_id', '')}"
            changed += 1
        if "comments" not in req:
            req["comments"] = []
            changed += 1
        if "history" not in req:
            req["history"] = []
            changed += 1
    if changed:
        _write_json_list(path, items)
    return changed


def _migrate_members() -> int:
    """Ensure all members have total_points and cheers fields."""
    items = _read_json_list(config.MEMBERS_FILE)
    changed = 0
    for m in items:
        if "total_points" not in m:
            m["total_points"] = 0
            changed += 1
        if "cheers" not in m:
            m["cheers"] = []
            changed += 1
        if "points_history" not in m:
            m["points_history"] = []
            changed += 1
    if changed:
        _write_json_list(config.MEMBERS_FILE, items)
    return changed


def _migrate_services() -> int:
    """Ensure all services have channel_availability, ibtikar_price, genoclab_price, turnaround_days."""
    items = _read_json_list(config.SERVICES_FILE)
    changed = 0
    for s in items:
        if "channel_availability" not in s:
            ch = s.get("channel", "")
            if ch == config.CHANNEL_IBTIKAR:
                s["channel_availability"] = "IBTIKAR"
            elif ch == config.CHANNEL_GENOCLAB:
                s["channel_availability"] = "GENOCLAB"
            else:
                s["channel_availability"] = "BOTH"
            changed += 1
        if "ibtikar_price" not in s or s.get("ibtikar_price") is None:
            s["ibtikar_price"] = s.get("base_price") or s.get("price") or 0
            changed += 1
        if "genoclab_price" not in s or s.get("genoclab_price") is None:
            s["genoclab_price"] = s.get("base_price") or s.get("price") or 0
            changed += 1
        if "turnaround_days" not in s or s.get("turnaround_days") is None:
            s["turnaround_days"] = 7
            changed += 1
        if "description" not in s or s.get("description") is None:
            s["description"] = ""
            changed += 1
    if changed:
        _write_json_list(config.SERVICES_FILE, items)
    return changed


def run_migrations():
    """Run all pending migrations. Safe to call multiple times."""
    current = _read_schema_version()
    if current == CURRENT_SCHEMA_VERSION:
        _log.info("Schéma à jour (v%s), aucune migration nécessaire.", current)
        return

    _log.info("Migration du schéma: v%s → v%s", current, CURRENT_SCHEMA_VERSION)

    # Ensure data files exist
    _ensure_file_exists(config.REQUEST_SEQUENCE_FILE, {})
    _ensure_file_exists(config.REVENUE_ARCHIVES_FILE, [])

    # Migrate requests
    n = _migrate_requests(config.ACTIVE_REQUESTS_FILE)
    if n:
        _log.info("Demandes actives migrées: %d champs ajoutés", n)
    n = _migrate_requests(config.ARCHIVED_REQUESTS_FILE)
    if n:
        _log.info("Demandes archivées migrées: %d champs ajoutés", n)

    # Migrate members
    n = _migrate_members()
    if n:
        _log.info("Membres migrés: %d champs ajoutés", n)

    # Migrate services
    n = _migrate_services()
    if n:
        _log.info("Services migrés: %d champs ajoutés", n)

    _write_schema_version(CURRENT_SCHEMA_VERSION)
    _log.info("Migration terminée. Schéma v%s", CURRENT_SCHEMA_VERSION)
