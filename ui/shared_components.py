# ui/shared_components.py — PLAGENOR 4.0 Shared UI Components

from __future__ import annotations
import streamlit as st
import csv
import io
import math
from datetime import datetime, timezone
from typing import Optional
import config
from utils.i18n import t, get_lang, set_lang


# ── Formatters ────────────────────────────────────────────────────────────────
def fmt_date(iso: str) -> str:
    if not iso: return "–"
    try:
        return datetime.fromisoformat(iso.replace("Z","+00:00")).strftime("%d/%m/%Y")
    except Exception:
        return iso[:10]

def fmt_datetime(iso: str) -> str:
    if not iso: return "–"
    try:
        return datetime.fromisoformat(iso.replace("Z","+00:00")).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return iso[:16]

def fmt_currency(amount, symbol="DZD") -> str:
    try:
        return f"{float(amount):,.0f} {symbol}"
    except Exception:
        return f"0 {symbol}"


# ── Resolvers ─────────────────────────────────────────────────────────────────
def resolve_username(user_id: str) -> str:
    if not user_id: return "–"
    try:
        from core.repository import get_user, get_member
        user = get_user(user_id)
        if user: return user.get("full_name", user.get("username", user_id))
        member = get_member(user_id)
        if member: return member.get("full_name", member.get("name", user_id))
    except Exception:
        pass
    return user_id[:8]

def resolve_service_name(service_id: str) -> str:
    if not service_id: return "–"
    try:
        from core.repository import get_service
        svc = get_service(service_id)
        if svc: return svc.get("name", service_id)
    except Exception:
        pass
    return service_id[:8]


# ── KPI Card ──────────────────────────────────────────────────────────────────
def render_kpi_card(icon: str, value, label: str, color: str = "blue"):
    color_map = {
        "blue": "#EFF6FF", "green": "#ECFDF5", "purple": "#F5F3FF",
        "orange": "#FFF7ED", "red": "#FEF2F2", "teal": "#F0FDFA",
    }
    bg = color_map.get(color, "#F8FAFC")
    st.markdown(f"""
    <div class="kpi-card {color}">
        <div class="kpi-icon-box" style="background:{bg}">{icon}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)


# ── Status Badge ──────────────────────────────────────────────────────────────
def get_status_badge_html(status: str) -> str:
    info = config.STATUS_LABELS.get(status, ("⚪", status, "#95A5A6"))
    icon, label, color = info

    css_class = "status-default"
    s = status.upper()
    if "REJECT" in s: css_class = "status-rejected"
    elif "COMPLET" in s: css_class = "status-completed"
    elif "VALID" in s or "APPROV" in s: css_class = "status-validated"
    elif "ASSIGN" in s: css_class = "status-assigned"
    elif "PROGRESS" in s or "IN_PROGRESS" in s or "ANALYSIS_STARTED" in s: css_class = "status-in-progress"
    elif "SUBMIT" in s: css_class = "status-submitted"
    elif "QUOTE" in s: css_class = "status-quote"
    elif "INVOICE" in s: css_class = "status-invoice"
    elif "APPROVED" in s: css_class = "status-approved"

    return f'<span class="status-badge {css_class}">{icon} {label}</span>'


def render_status_badge(status: str):
    st.markdown(get_status_badge_html(status), unsafe_allow_html=True)


# ── Channel Badge ─────────────────────────────────────────────────────────────
def get_channel_badge_html(channel: str) -> str:
    css = "channel-ibtikar" if channel == config.CHANNEL_IBTIKAR else "channel-genoclab"
    return f'<span class="channel-badge {css}">{channel}</span>'


# ── Role Badge ────────────────────────────────────────────────────────────────
def get_role_badge_html(role: str) -> str:
    css_map = {
        config.ROLE_SUPER_ADMIN: "role-super-admin",
        config.ROLE_PLATFORM_ADMIN: "role-platform-admin",
        config.ROLE_MEMBER: "role-member",
        config.ROLE_FINANCE: "role-finance",
        config.ROLE_REQUESTER: "role-requester",
        config.ROLE_CLIENT: "role-client",
    }
    css = css_map.get(role, "role-requester")
    label = config.ROLE_LABELS.get(role, role)
    icon = config.ROLE_ICONS.get(role, "👤")
    return f'<span class="role-badge {css}">{icon} {label}</span>'


# ── Progress Bar ──────────────────────────────────────────────────────────────
def render_progress_bar(value: float, max_val: float = 100, color: str = "blue",
                        label: str = ""):
    pct = min(100, max(0, (value / max_val * 100) if max_val > 0 else 0))
    color_class = f"progress-{color}"
    if pct > 90: color_class = "progress-red"
    elif pct > 70: color_class = "progress-orange"

    if label:
        st.markdown(f"<div style='font-size:13px;color:#566573;margin-bottom:4px'>{label}</div>",
                    unsafe_allow_html=True)
    st.markdown(f"""
    <div class="progress-container">
        <div class="progress-bar {color_class}" style="width:{pct:.1f}%"></div>
    </div>
    <div style="font-size:12px;color:#7F8C9B;margin-top:2px">{pct:.1f}% ({fmt_currency(value)} / {fmt_currency(max_val)})</div>
    """, unsafe_allow_html=True)


# ── Workflow Pipeline ─────────────────────────────────────────────────────────
IBTIKAR_PIPELINE = [
    ("DRAFT","Brouillon"), ("SUBMITTED","Soumise"),
    ("VALIDATION_PEDAGOGIQUE","Valid. Péd."), ("VALIDATION_FINANCE","Valid. Fin."),
    ("PLATFORM_NOTE_GENERATED","Note"), ("ASSIGNED","Assignée"),
    ("SAMPLE_RECEIVED","Réception"), ("ANALYSIS_STARTED","Analyse"),
    ("ANALYSIS_FINISHED","Terminée"), ("REPORT_UPLOADED","Rapport"),
    ("REPORT_VALIDATED","Validé"), ("COMPLETED","Complétée"), ("CLOSED","Clôturée"),
]

GENOCLAB_PIPELINE = [
    ("REQUEST_CREATED","Créée"), ("QUOTE_DRAFT","Devis"),
    ("QUOTE_SENT","Envoyé"), ("QUOTE_VALIDATED_BY_CLIENT","Accepté"),
    ("INVOICE_GENERATED","Facture"), ("PAYMENT_CONFIRMED","Payé"),
    ("ASSIGNED","Assignée"), ("SAMPLE_RECEIVED","Réception"),
    ("ANALYSIS_STARTED","Analyse"), ("ANALYSIS_FINISHED","Terminée"),
    ("REPORT_UPLOADED","Rapport"), ("REPORT_VALIDATED","Validé"),
    ("COMPLETED","Complétée"), ("ARCHIVED","Archivée"),
]

def render_workflow_progress(request: dict):
    channel = request.get("channel", "")
    status = request.get("status", "")
    pipeline = IBTIKAR_PIPELINE if channel == config.CHANNEL_IBTIKAR else GENOCLAB_PIPELINE

    if status in ("REJECTED", "QUOTE_REJECTED_BY_CLIENT"):
        st.markdown(f"""
        <div style="text-align:center;padding:8px">
            <span class="status-badge status-rejected">❌ {status.replace('_',' ')}</span>
        </div>""", unsafe_allow_html=True)
        return

    steps_html = []
    found = False
    for state_key, label in pipeline:
        if state_key == status:
            found = True
            steps_html.append(f'<div class="pipeline-step pipeline-current">{label}</div>')
        elif not found:
            steps_html.append(f'<div class="pipeline-step pipeline-done">✓ {label}</div>')
        else:
            steps_html.append(f'<div class="pipeline-step pipeline-pending">{label}</div>')

    if not found:
        steps_html.append(f'<div class="pipeline-step pipeline-current">{status}</div>')

    st.markdown(f'<div class="pipeline-container">{"".join(steps_html)}</div>',
                unsafe_allow_html=True)


# ── Empty State ───────────────────────────────────────────────────────────────
def render_empty_state(icon: str = "📭", text: str = ""):
    display_text = text if text else t("no_data")
    st.markdown(f"""
    <div class="empty-state">
        <span class="empty-state-icon">{icon}</span>
        <span class="empty-state-text">{display_text}</span>
    </div>""", unsafe_allow_html=True)


# ── Request Card ──────────────────────────────────────────────────────────────
def _escape_html(text: str) -> str:
    """Escape HTML special characters to prevent injection."""
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def render_request_card(req: dict, show_actions: bool = False):
    status_html = get_status_badge_html(req.get("status", "") or "")
    channel_html = get_channel_badge_html(req.get("channel", "") or "")
    urgency_html = get_urgency_badge_html(req.get("urgency", "") or "")
    title = _escape_html(req.get("title") or "Sans titre")
    rid = _escape_html(req.get("display_id") or (req.get("id", "") or "")[:8])
    created = fmt_date(req.get("created_at", "") or "")

    # Build detail parts safely
    detail_parts = [f"Créée le {created}"]
    if req.get("assigned_to"):
        detail_parts.append(f"Assigné à {_escape_html(resolve_username(req['assigned_to']))}")
    if req.get("budget_amount"):
        detail_parts.append(f"Budget: {fmt_currency(req['budget_amount'])}")

    st.markdown(f"""
    <div class="data-card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <div>
                <span style="font-weight:700;font-size:15px;color:#1B2838">{title}</span>
                <span style="font-size:11px;color:#ABB2B9;margin-left:8px">#{rid}</span>
            </div>
            <div>{urgency_html} {channel_html} {status_html}</div>
        </div>
        <div style="font-size:12px;color:#7F8C9B">
            {' · '.join(detail_parts)}
        </div>
    </div>""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
def render_sidebar_user(user: dict):
    import os
    assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
    with st.sidebar:
        # ── Language Switcher ──
        current_lang = get_lang()
        switch_label = t("lang_switch")
        if st.button(f"🌐 {switch_label}", use_container_width=True, key="lang_toggle"):
            new_lang = "en" if current_lang == "fr" else "fr"
            set_lang(new_lang)
            st.rerun()

        logo_path = os.path.join(assets_dir, "logo_plagenor.png")
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)
        else:
            st.markdown("## 🧬 PLAGENOR 4.0")

        # Show ESSBO logo smaller below
        essbo_path = os.path.join(assets_dir, "logo_essbo.png")
        if os.path.exists(essbo_path):
            st.image(essbo_path, width=150)

        st.markdown("---")

        name = user.get("full_name", user.get("username", ""))
        role = user.get("role", "")
        role_html = get_role_badge_html(role)
        org = user.get("organization_id", "ESSBO")

        st.markdown(f"""
        <div class="sidebar-user-card">
            <div class="sidebar-user-name">👤 {name}</div>
            <div style="margin:6px 0">{role_html}</div>
            <div class="sidebar-user-role">🏛 {org}</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("---")

        if st.button(f"🚪 {t('logout')}", use_container_width=True):
            try:
                from core.audit_engine import log_action
                log_action("LOGOUT", "AUTH", user.get("id", ""), actor=user)
            except Exception:
                pass
            st.session_state.clear()
            st.rerun()

        st.markdown(f"""
        <div style="text-align:center;font-size:11px;color:#718096;margin-top:24px">
            PLAGENOR {config.PLATFORM_VERSION}<br/>
            © {config.PLATFORM_YEAR} {config.PLATFORM_AUTHOR}
        </div>""", unsafe_allow_html=True)


# ── Confirm Action ────────────────────────────────────────────────────────────
def confirm_action(label: str, key: str) -> bool:
    return st.button(label, key=key, type="primary")


# ── Section Header ────────────────────────────────────────────────────────────
def section_header(text: str, icon: str = ""):
    st.markdown(f'<div class="section-header">{icon} {text}</div>', unsafe_allow_html=True)


# ── CSV Export ───────────────────────────────────────────────────────────────
def render_export_button(data: list, filename: str = "export.csv", label: str = "📥 Exporter CSV", columns: list = None):
    """Render a CSV export button for a list of dicts."""
    if not data:
        return
    if columns is None:
        columns = list(data[0].keys())
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction='ignore')
    writer.writeheader()
    for row in data:
        writer.writerow(row)
    csv_data = output.getvalue()
    st.download_button(
        label=label,
        data=csv_data,
        file_name=filename,
        mime="text/csv",
        key=f"export_{filename}_{len(data)}"
    )


# ── Pagination ───────────────────────────────────────────────────────────────
def render_pagination(items: list, page_key: str = "page", items_per_page: int = 15) -> list:
    """Paginate a list and render navigation controls. Returns current page items."""
    if not items:
        return items
    total_pages = math.ceil(len(items) / items_per_page)
    if total_pages <= 1:
        return items

    if page_key not in st.session_state:
        st.session_state[page_key] = 1

    current_page = st.session_state[page_key]
    current_page = max(1, min(current_page, total_pages))

    start = (current_page - 1) * items_per_page
    end = start + items_per_page

    # Navigation
    nav_cols = st.columns([1, 2, 1])
    with nav_cols[0]:
        if current_page > 1:
            if st.button("◀ Précédent", key=f"{page_key}_prev"):
                st.session_state[page_key] = current_page - 1
                st.rerun()
    with nav_cols[1]:
        st.markdown(f"<div style='text-align:center; color:#7F8C9B;'>Page {current_page} / {total_pages} ({len(items)} éléments)</div>", unsafe_allow_html=True)
    with nav_cols[2]:
        if current_page < total_pages:
            if st.button("Suivant ▶", key=f"{page_key}_next"):
                st.session_state[page_key] = current_page + 1
                st.rerun()

    return items[start:end]


# ── Colored Status Badge ─────────────────────────────────────────────────────
def render_colored_status_badge(status: str) -> str:
    """Return HTML for a colored status badge with background."""
    label_data = config.STATUS_LABELS.get(status, ("❓", status, "#95A5A6"))
    emoji, label, color = label_data
    return f'<span style="background-color:{color}15; color:{color}; padding:4px 12px; border-radius:12px; font-size:13px; font-weight:600; border:1px solid {color}40;">{emoji} {label}</span>'


# ── Urgency Badge ────────────────────────────────────────────────────────────
def get_urgency_badge_html(urgency: str) -> str:
    """Return HTML for an urgency level badge."""
    if not urgency or urgency == "Normal":
        return ""
    color = config.URGENCY_COLORS.get(urgency, "#95A5A6")
    icon = config.URGENCY_ICONS.get(urgency, "⚪")
    return f'<span style="background-color:{color}15; color:{color}; padding:3px 10px; border-radius:10px; font-size:11px; font-weight:600; border:1px solid {color}40;">{icon} {urgency}</span>'


# ── Star Rating Display ──────────────────────────────────────────────────────
def render_star_rating_html(current_rating: int = 0) -> str:
    """Return HTML to display a star rating (read-only)."""
    stars = ""
    for i in range(1, 6):
        if i <= current_rating:
            stars += '<span style="color:#F39C12;font-size:20px">★</span>'
        else:
            stars += '<span style="color:#E2E8F0;font-size:20px">★</span>'
    return f'<div style="display:inline-block">{stars}</div>'
