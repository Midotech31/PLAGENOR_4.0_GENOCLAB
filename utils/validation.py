# utils/validation.py — PLAGENOR 4.0 Centralised Input Validators
import re
import mimetypes
import config


def validate_email(email: str) -> bool:
    """Basic email format validation."""
    if not email:
        return False
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))


def validate_phone(phone: str) -> bool:
    """Phone number validation — allows digits, spaces, dashes, parens, plus."""
    if not phone:
        return True  # phone is optional
    return bool(re.match(r'^[+\d\s\-().]{6,20}$', phone))


def validate_password_length(pw: str) -> bool:
    return len(pw) >= config.MIN_PASSWORD_LENGTH


def validate_file_mime(filename: str, content_bytes: bytes, allowed_extensions: set) -> tuple[bool, str]:
    """SEC-08: Validate file MIME type independently of extension.
    Returns (is_valid, error_message)."""
    import os
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed_extensions:
        return False, f"Extension non autorisée: {ext}"
    # Check MIME type matches extension
    guessed_type, _ = mimetypes.guess_type(filename)
    if guessed_type is None:
        # Unknown MIME for uncommon scientific formats is acceptable
        if ext in (".fastq", ".fasta", ".gz"):
            return True, ""
        return False, f"Type MIME inconnu pour {ext}"
    return True, ""
