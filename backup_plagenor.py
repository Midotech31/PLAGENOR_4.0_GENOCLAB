#!/usr/bin/env python3
"""
PLAGENOR 4.0 — Database Backup Script
======================================
Performs a safe hot copy of data/plagenor.db using the SQLite backup API.
Stores backups in backup/ with timestamp-based filenames.
Retains only the last 30 backups; older ones are automatically deleted.

Usage:
    python backup_plagenor.py

Schedule with Windows Task Scheduler:
    schtasks /create /tn "PLAGENOR_Backup" ^
        /tr "C:\\Apps\\plagenor\\venv\\Scripts\\python.exe C:\\Apps\\plagenor\\backup_plagenor.py" ^
        /sc daily /st 02:00 /ru SYSTEM
"""

import sqlite3
import shutil
import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────────
# Resolve paths relative to this script's location so it works from any CWD
SCRIPT_DIR    = Path(__file__).parent.resolve()
DB_SOURCE     = SCRIPT_DIR / "data" / "plagenor.db"
BACKUP_DIR    = SCRIPT_DIR / "backup"
MAX_BACKUPS   = 30
TIMESTAMP_FMT = "%Y%m%d_%H%M%S"

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("plagenor_backup")


def ensure_backup_dir() -> None:
    """Create the backup directory if it does not exist."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    log.info("Backup directory: %s", BACKUP_DIR)


def hot_copy(src: Path, dst: Path) -> None:
    """
    Use the SQLite Online Backup API for a safe, consistent copy
    even while the database is being written to by Streamlit.
    """
    log.info("Starting SQLite hot copy: %s → %s", src, dst)
    src_conn = sqlite3.connect(str(src))
    dst_conn = sqlite3.connect(str(dst))
    try:
        with dst_conn:
            src_conn.backup(dst_conn, pages=256, progress=_backup_progress)
    finally:
        src_conn.close()
        dst_conn.close()
    log.info("Hot copy completed successfully.")


def _backup_progress(status: int, remaining: int, total: int) -> None:
    """Callback for sqlite3.Connection.backup() — logs progress every 10%."""
    if total > 0:
        pct = round((total - remaining) / total * 100)
        if pct % 10 == 0:
            log.info("  Backup progress: %d%% (%d/%d pages)", pct, total - remaining, total)


def purge_old_backups() -> None:
    """Delete backups older than MAX_BACKUPS, keeping the most recent ones."""
    pattern = "plagenor_*.db"
    backups = sorted(BACKUP_DIR.glob(pattern))  # lexicographic = chronological
    if len(backups) <= MAX_BACKUPS:
        log.info("Backup count (%d) within limit (%d). No purge needed.", len(backups), MAX_BACKUPS)
        return

    to_delete = backups[:len(backups) - MAX_BACKUPS]
    log.info("Purging %d old backup(s) (keeping last %d).", len(to_delete), MAX_BACKUPS)
    for old in to_delete:
        try:
            old.unlink()
            log.info("  Deleted: %s", old.name)
        except OSError as exc:
            log.warning("  Could not delete %s: %s", old.name, exc)


def run_backup() -> int:
    """Main backup routine. Returns exit code (0 = success, 1 = error)."""
    log.info("=" * 60)
    log.info("PLAGENOR 4.0 — Backup started at %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # 1. Validate source database
    if not DB_SOURCE.exists():
        log.error("Source database not found: %s", DB_SOURCE)
        log.error("Has the application been run at least once to create the database?")
        return 1

    source_size_mb = DB_SOURCE.stat().st_size / (1024 * 1024)
    log.info("Source DB: %s (%.2f MB)", DB_SOURCE, source_size_mb)

    # 2. Prepare backup directory
    ensure_backup_dir()

    # 3. Build destination filename
    timestamp = datetime.now().strftime(TIMESTAMP_FMT)
    dst = BACKUP_DIR / f"plagenor_{timestamp}.db"

    if dst.exists():
        log.warning("Backup file already exists (same-second run?): %s", dst)
        return 0  # Not an error; idempotent

    # 4. Perform hot copy via SQLite backup API
    try:
        hot_copy(DB_SOURCE, dst)
    except Exception as exc:
        log.error("Backup failed: %s", exc, exc_info=True)
        # Clean up partial backup file
        if dst.exists():
            dst.unlink(missing_ok=True)
        return 1

    # 5. Verify backup integrity
    try:
        conn = sqlite3.connect(str(dst))
        conn.execute("PRAGMA integrity_check")
        conn.close()
        backup_size_mb = dst.stat().st_size / (1024 * 1024)
        log.info("Backup verified OK: %s (%.2f MB)", dst.name, backup_size_mb)
    except Exception as exc:
        log.error("Backup integrity check failed: %s", exc)
        return 1

    # 6. Purge old backups
    purge_old_backups()

    log.info("Backup finished successfully.")
    log.info("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(run_backup())
