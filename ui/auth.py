# ui/auth.py — PLAGENOR 4.0 Auth & Role Guards

from __future__ import annotations
import streamlit as st
from datetime import datetime, timezone
from typing import Optional
import config


def get_current_user() -> Optional[dict]:
    """Get the currently authenticated user from session state."""
    if not st.session_state.get("authenticated"):
        return None
    return st.session_state.get("user")


def require_auth():
    """Ensure user is authenticated. Stops execution if not."""
    if not st.session_state.get("authenticated") or not st.session_state.get("user"):
        st.error("⚠️ Vous devez être connecté pour accéder à cette page.")
        st.stop()


def require_roles(*allowed_roles):
    """Ensure current user has one of the allowed roles."""
    require_auth()
    user = st.session_state.get("user", {})
    role = user.get("role", "")
    if role not in allowed_roles and role != config.ROLE_SUPER_ADMIN:
        st.error(f"⚠️ Accès refusé. Rôle requis: {', '.join(allowed_roles)}")
        st.stop()


def is_super_admin() -> bool:
    user = get_current_user()
    return user.get("role") == config.ROLE_SUPER_ADMIN if user else False


def is_admin() -> bool:
    user = get_current_user()
    if not user:
        return False
    return user.get("role") in (config.ROLE_SUPER_ADMIN, config.ROLE_PLATFORM_ADMIN)


def has_role(role: str) -> bool:
    user = get_current_user()
    if not user:
        return False
    return user.get("role") == role or user.get("role") == config.ROLE_SUPER_ADMIN


def logout():
    """Clear session and force re-run."""
    try:
        from core.audit_engine import log_action
        user = st.session_state.get("user")
        if user:
            log_action("LOGOUT", "AUTH", user.get("id", ""), actor=user)
    except Exception:
        pass
    st.session_state.clear()
    st.rerun()
