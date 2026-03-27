# core/logger.py — PLAGENOR 4.0 Structured Logging
from __future__ import annotations
import logging
import os


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(f"plagenor.{name}")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        ))
        logger.addHandler(handler)
        logger.setLevel(
            getattr(logging, os.environ.get("PLAGENOR_LOG_LEVEL", "INFO").upper(), logging.INFO)
        )
    return logger
