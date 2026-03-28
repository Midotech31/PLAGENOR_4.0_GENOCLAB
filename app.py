# app.py — PLAGENOR 4.0 Main Router
"""
PLAGENOR 4.0 — Genomics Operations & Research Governance Engine
Main entry point. Routes to role-specific dashboards.
"""

from __future__ import annotations

# Load .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import streamlit as st
from datetime import datetime, timezone

st.set_page_config(
    page_title="PLAGENOR 4.0",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

import config
from utils.i18n import t
from core.repository import ensure_data_directory

# OPS-01: Health check endpoint via query params
if st.query_params.get("health") == "1":
    st.json({"status": "ok", "version": config.PLATFORM_VERSION})
    st.stop()

# Bootstrap data directory
ensure_data_directory()

# Run schema migrations on startup
from core.migrations import run_migrations
run_migrations()

# ── Session Init ──────────────────────────────────────────────────────────────
# SEC-09: Streamlit session_state lives server-side in the Tornado process.
# For multi-node deployments, consider a shared session store (Redis, DB).
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user" not in st.session_state:
    st.session_state["user"] = None

# ── Report viewing via token link ────────────────────────────────────────────
if st.query_params.get("report"):
    from ui.report_viewer import render_report_viewer
    render_report_viewer(st.query_params["report"])
    st.stop()

# ── Unauthenticated → Login ──────────────────────────────────────────────────
if not st.session_state.get("authenticated"):
    from ui.home_page import render_home_page
    render_home_page()
    st.stop()

# ── Authenticated → Route by Role ────────────────────────────────────────────
user = st.session_state.get("user")
if not user:
    st.session_state["authenticated"] = False
    from ui.home_page import render_home_page
    render_home_page()
    st.stop()

# ── Session Timeout Check ────────────────────────────────────────────────
if "last_activity" not in st.session_state:
    st.session_state["last_activity"] = datetime.now(timezone.utc).isoformat()
else:
    try:
        last = datetime.fromisoformat(st.session_state["last_activity"])
        elapsed = (datetime.now(timezone.utc) - last).total_seconds()
        if elapsed > config.SESSION_TIMEOUT_SECONDS:
            st.session_state.clear()
            st.warning(f"⏰ {t('session_expired')}")
            st.rerun()
    except Exception:
        pass
st.session_state["last_activity"] = datetime.now(timezone.utc).isoformat()

role = user.get("role")

if role == config.ROLE_SUPER_ADMIN:
    from ui.super_admin_dashboard import render_super_admin_dashboard
    render_super_admin_dashboard(user)

elif role == config.ROLE_PLATFORM_ADMIN:
    from ui.platform_admin_dashboard import render_platform_admin_dashboard
    render_platform_admin_dashboard(user)

elif role == config.ROLE_MEMBER:
    from ui.member_dashboard import render_member_dashboard
    render_member_dashboard(user)

elif role == config.ROLE_FINANCE:
    from ui.finance_dashboard import render_finance_dashboard
    render_finance_dashboard(user)

elif role == config.ROLE_REQUESTER:
    from ui.requester_dashboard import render_requester_dashboard
    render_requester_dashboard(user)

elif role == config.ROLE_CLIENT:
    from ui.client_dashboard import render_client_dashboard
    render_client_dashboard(user)

else:
    st.error(f"⚠️ Rôle inconnu: {role}")
    if st.button("🚪 Déconnexion"):
        st.session_state.clear()
        st.rerun()

st.stop()
