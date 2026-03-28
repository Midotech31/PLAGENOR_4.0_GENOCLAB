# utils/__init__.py — PLAGENOR 4.0 Utilities
import html
import re


def sanitize_html(text: str) -> str:
    """Sanitize user input to prevent HTML/JS injection."""
    if not text:
        return ""
    return html.escape(str(text))


def sanitize_dict(d: dict, keys: list = None) -> dict:
    """Sanitize specific string fields in a dictionary."""
    result = dict(d)
    for k, v in result.items():
        if keys and k not in keys:
            continue
        if isinstance(v, str):
            result[k] = sanitize_html(v)
    return result


# QC-05: Shared password hashing — single source of truth
def hash_password(pw: str) -> str:
    """Hash a password using werkzeug (hard dependency)."""
    from werkzeug.security import generate_password_hash
    return generate_password_hash(pw, method="pbkdf2:sha256")
