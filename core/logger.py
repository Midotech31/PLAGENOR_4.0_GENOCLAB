# core/logger.py — PLAGENOR 4.0 Structured Logging
from __future__ import annotations
import logging
import logging.handlers
import os


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(f"plagenor.{name}")
    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
        # Console handler
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        logger.addHandler(console)
        # ARCH-05: RotatingFileHandler — 5 MB max, 3 backups
        log_dir = os.environ.get("PLAGENOR_LOG_DIR", "")
        if not log_dir:
            try:
                import config
                log_dir = getattr(config, "DATA_DIR", "")
            except Exception:
                pass
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "plagenor.log")
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        logger.setLevel(
            getattr(logging, os.environ.get("PLAGENOR_LOG_LEVEL", "INFO").upper(), logging.INFO)
        )
    return logger
