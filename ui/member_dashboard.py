# ui/member_dashboard.py — PLAGENOR 4.0 Member/Analyst Dashboard
from __future__ import annotations
import streamlit as st
import os
from datetime import datetime, timezone
import config
from ui.styles import get_global_css
from ui.shared_components import (
    render_sidebar_user, render_kpi_card, render_request_card,
    render_empty_state, render_workflow_progress, render_progress_bar,
    fmt_date, fmt_datetime, fmt_currency, section_header, get_status_badge_html,
)
from core.repository import (
    get_all_active_requests, get_all_archived_requests,
    get_member_by_user_id, get_requests_by_member, save_request,
    get_member_points, add_comment_to_request,
)
from core.workflow_engine import transition, get_allowed_transitions
from core.productivity_engine import compute_member_productivity
from services.notification_service import get_user_notifications, get_unread_count
from core.logger import get_logger

_log = get_logger("member_dashboard")

def render_member_dashboard(user):
    try:
        _render_member_dashboard_inner(user)
    except Exception as e:
        _log.exception("Erreur dans le tableau Analyste")
        st.error(f"❌ Une erreur inattendue s'est produite dans le tableau Analyste. Veuillez réessayer ou contacter l'administrateur.\n\nDétail: {e}")

def _render_member_dashboard_inner(user):
    st.session_state["user"] = user
    st.session_state["authenticated"] = True
    st.markdown(get_global_css(), unsafe_allow_html=True)
    render_sidebar_user(user)
    unread = get_unread_count(user.get("id",""))
    badge = f" · 🔔 {unread}" if unread else ""
    st.markdown(f'<div style="margin-bottom:24px"><h2 style="color:#1B2838;margin:0">🔬 Espace Analyste</h2><p style="color:#7F8C9B;margin:4px 0 0">Vos analyses et tâches{badge}</p></div>', unsafe_allow_html=True)
    member = get_member_by_user_id(user.get("id",""))
    mid = member.get("id","") if member else ""
    if mid:
        my_reqs = get_requests_by_member(mid)
        all_reqs = get_all_active_requests() + get_all_archived_requests()
        completed = [r for r in all_reqs if r.get("assigned_to")==mid and r.get("status")=="COMPLETED"]
        prod = compute_member_productivity(mid)
    else:
        my_reqs, completed = [], []
        prod = {"score":50,"status":"NORMAL","emoji":"🟡","completed":0,"total_assigned":0}
    pending = [r for r in my_reqs if r.get("status") in ("ASSIGNED","SAMPLE_RECEIVED")]
    in_prog = [r for r in my_reqs if r.get("status") in ("ANALYSIS_STARTED","ANALYSIS_FINISHED","SAMPLE_RECEIVED")]

    c1,c2,c3,c4 = st.columns(4)
    with c1: render_kpi_card("📋", len(my_reqs), "Assignées", "blue")
    with c2: render_kpi_card("🔬", len(in_prog), "En cours", "orange")
    with c3: render_kpi_card("✅", len(completed), "Complétées", "green")
    with c4: render_kpi_card(prod.get("emoji","⚪"), f"{prod.get('score',0):.0f}%", "Productivité", "purple")
    st.markdown("<br/>", unsafe_allow_html=True)
    if member:
        load, mx = member.get("current_load",0), member.get("max_load",config.DEFAULT_MAX_LOAD)
        render_progress_bar(load, mx, "blue", "Charge de travail")
    st.markdown("<br/>", unsafe_allow_html=True)

    tabs = st.tabs(["⏳ En attente","🔬 En cours","✅ Historique","🏆 Points & Cheers","🔔 Notifications"])
    with tabs[0]:
        if not pending: render_empty_state("✅","Aucune tâche en attente")
        else:
            for req in pending:
                render_request_card(req)
                with st.expander(f"🔧 — {req.get('title','')[:40]}"):
                    render_workflow_progress(req)
                    allowed = get_allowed_transitions(req)
                    member_ok = {s for s in allowed if s in ("ANALYSIS_STARTED","ANALYSIS_FINISHED","SAMPLE_RECEIVED","REPORT_UPLOADED","REPORT_VALIDATED")}
                    if member_ok:
                        ns = st.selectbox("Action →", sorted(member_ok), key=f"m_t_{req['id']}")
                        if st.button("✅ Exécuter", key=f"m_e_{req['id']}", type="primary"):
                            with st.spinner("⏳ Transition en cours..."):
                                try: transition(req["id"], ns, user); st.success(f"✅ {ns}"); st.rerun()
                                except Exception as e: st.error(str(e))
                    # Comments
                    st.markdown("---")
                    st.markdown("##### 💬 Commentaires")
                    comments = req.get("comments", [])
                    if comments:
                        for cmt in comments:
                            st.markdown(f'<div style="padding:6px 12px;border-left:3px solid #2E86C1;margin-bottom:4px;font-size:13px"><strong>{cmt.get("author_name","")}</strong> <span style="color:#ABB2B9">({cmt.get("step","")}) {fmt_datetime(cmt.get("created_at",""))}</span><br/>{cmt.get("text","")}</div>', unsafe_allow_html=True)
                    cmt_text = st.text_area("Commentaire", key=f"mc_{req['id']}", height=100)
                    if st.button("💬 Envoyer", key=f"mc_btn_{req['id']}"):
                        if cmt_text.strip():
                            add_comment_to_request(req["id"], cmt_text.strip(), user)
                            st.success("💬 Commentaire ajouté"); st.rerun()
    with tabs[1]:
        active = [r for r in my_reqs if r.get("status") in ("ANALYSIS_STARTED","ANALYSIS_FINISHED","SAMPLE_RECEIVED")]
        if not active: render_empty_state("🔬","Aucune analyse en cours")
        else:
            for req in active:
                render_request_card(req)
                with st.expander(f"🔧 — {req.get('title','')[:40]}"):
                    render_workflow_progress(req)
                    allowed = get_allowed_transitions(req)
                    if allowed:
                        ns = st.selectbox("Action →", sorted(allowed), key=f"m_p_{req['id']}")
                        notes = st.text_area("Observations", key=f"m_n_{req['id']}")
                        if ns == "REPORT_UPLOADED":
                            ALLOWED_UPLOAD_TYPES = [".pdf", ".docx", ".xlsx", ".csv", ".zip", ".fastq", ".fasta", ".gz"]
                            MAX_UPLOAD_MB = 50
                            uploaded = st.file_uploader("📄 Rapport", key=f"m_f_{req['id']}", type=["pdf","docx","xlsx","csv","zip","fastq","fasta","gz"])
                            if uploaded:
                                ext = os.path.splitext(uploaded.name)[1].lower()
                                if ext not in ALLOWED_UPLOAD_TYPES:
                                    st.error(f"❌ Type de fichier non autorisé: {ext}. Types acceptés: {', '.join(ALLOWED_UPLOAD_TYPES)}")
                                elif uploaded.size > MAX_UPLOAD_MB * 1024 * 1024:
                                    st.error(f"❌ Fichier trop volumineux ({uploaded.size / 1024 / 1024:.1f} Mo). Maximum: {MAX_UPLOAD_MB} Mo.")
                                else:
                                    fpath = os.path.join(config.REPORTS_DIR, f"{req['id'][:8]}_{uploaded.name}")
                                    with open(fpath, "wb") as f: f.write(uploaded.getbuffer())
                                    req["report_file"] = fpath
                                    save_request(req)
                                    st.success(f"📎 Fichier uploadé: {uploaded.name}")
                        if st.button("✅ Valider", key=f"m_e2_{req['id']}", type="primary"):
                            with st.spinner("⏳ Transition en cours..."):
                                try:
                                    transition(req["id"], ns, user, details={"notes": notes})
                                    st.success(f"✅ {ns}"); st.rerun()
                                except Exception as e: st.error(str(e))
                    # Admin revision notes
                    if req.get("admin_revision_notes"):
                        st.warning(f"📝 Notes de révision admin: {req['admin_revision_notes']}")
                    # Comments
                    st.markdown("---")
                    st.markdown("##### 💬 Commentaires")
                    comments = req.get("comments", [])
                    if comments:
                        for cmt in comments:
                            st.markdown(f'<div style="padding:6px 12px;border-left:3px solid #2E86C1;margin-bottom:4px;font-size:13px"><strong>{cmt.get("author_name","")}</strong> <span style="color:#ABB2B9">({cmt.get("step","")}) {fmt_datetime(cmt.get("created_at",""))}</span><br/>{cmt.get("text","")}</div>', unsafe_allow_html=True)
                    cmt_text2 = st.text_area("Commentaire", key=f"mc2_{req['id']}", height=100)
                    if st.button("💬 Envoyer", key=f"mc2_btn_{req['id']}"):
                        if cmt_text2.strip():
                            add_comment_to_request(req["id"], cmt_text2.strip(), user)
                            st.success("💬 Commentaire ajouté"); st.rerun()
    with tabs[2]:
        if not completed: render_empty_state("📦","Aucune analyse terminée")
        else:
            for req in completed[:20]: render_request_card(req)
    with tabs[3]:
        # Points & Cheers
        if mid:
            points_data = get_member_points(mid)
            c1,c2 = st.columns(2)
            with c1:
                render_kpi_card("⭐", points_data["total_points"], "Points totaux", "orange")
            with c2:
                render_kpi_card("💬", len(points_data["cheers"]), "Encouragements", "teal")
            st.markdown("<br/>", unsafe_allow_html=True)
            if points_data["points_history"]:
                section_header("Historique des points","⭐")
                for ph in reversed(points_data["points_history"][-20:]):
                    st.markdown(f'<div style="padding:6px 12px;border-left:3px solid #F39C12;margin-bottom:4px;font-size:13px">+{ph.get("points",0)} pts — {ph.get("reason","")} <span style="color:#7F8C9B;margin-left:8px">par {ph.get("awarded_by_name","")}</span> <span style="color:#ABB2B9">{fmt_date(ph.get("at",""))}</span></div>', unsafe_allow_html=True)
            if points_data["cheers"]:
                section_header("Encouragements reçus","💬")
                for ch in reversed(points_data["cheers"][-10:]):
                    st.markdown(f'<div class="data-card"><strong>💬 {ch.get("from","")}</strong> <span style="color:#ABB2B9">{fmt_date(ch.get("at",""))}</span><p style="margin:4px 0 0;color:#4A5568">{ch.get("message","")}</p></div>', unsafe_allow_html=True)
            if not points_data["points_history"] and not points_data["cheers"]:
                render_empty_state("🏆","Aucun point ou encouragement pour le moment")
        else:
            render_empty_state("👤","Profil analyste non trouvé")
    with tabs[4]:
        notifs = get_user_notifications(user.get("id",""))
        if not notifs: render_empty_state("🔔","Aucune notification")
        else:
            for n in notifs[:30]:
                read = "opacity:0.5" if n.get("read") else ""
                st.markdown(f'<div style="padding:8px 12px;border-left:3px solid #2E86C1;margin-bottom:6px;font-size:13px;{read}">{n.get("message","")} <span style="color:#ABB2B9;margin-left:8px">{fmt_date(n.get("created_at",""))}</span></div>', unsafe_allow_html=True)
