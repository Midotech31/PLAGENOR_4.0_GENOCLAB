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
    get_member_points, add_comment_to_request, save_member,
)
from utils.qrcode_gen import generate_qr_html
from core.workflow_engine import transition, get_allowed_transitions
from core.productivity_engine import compute_member_productivity
from services.notification_service import get_user_notifications, get_unread_count
from core.logger import get_logger
from utils.i18n import t

_log = get_logger("member_dashboard")

def render_member_dashboard(user):
    try:
        _render_member_dashboard_inner(user)
    except Exception as e:
        _log.exception("Erreur dans le tableau Analyste / Opérateur")
        st.error(f"❌ Une erreur inattendue s'est produite dans le tableau Analyste / Opérateur. Veuillez réessayer ou contacter l'administrateur.\n\nDétail: {e}")

def _render_member_dashboard_inner(user):
    st.session_state["user"] = user
    st.session_state["authenticated"] = True
    st.markdown(get_global_css(), unsafe_allow_html=True)
    render_sidebar_user(user)
    unread = get_unread_count(user.get("id",""))
    badge = f" · 🔔 {unread}" if unread else ""
    st.markdown(f'<div style="margin-bottom:24px"><h2 style="color:#1B2838;margin:0">🔬 {t("welcome_member")}</h2><p style="color:#7F8C9B;margin:4px 0 0">{t("requests")}{badge}</p></div>', unsafe_allow_html=True)
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
    with c1: render_kpi_card("📋", len(my_reqs), t("assigned"), "blue")
    with c2: render_kpi_card("🔬", len(in_prog), t("in_progress"), "orange")
    with c3: render_kpi_card("✅", len(completed), t("completed"), "green")
    with c4: render_kpi_card(prod.get("emoji","⚪"), f"{prod.get('score',0):.0f}%", t("productivity"), "purple")
    st.markdown("<br/>", unsafe_allow_html=True)
    if member:
        load, mx = member.get("current_load",0), member.get("max_load",config.DEFAULT_MAX_LOAD)
        render_progress_bar(load, mx, "blue", "Charge de travail")
    st.markdown("<br/>", unsafe_allow_html=True)

    tabs = st.tabs([f"⏳ {t('pending')}",f"🔬 {t('in_progress')}",f"✅ {t('completed')}","👤 Mon Profil",f"🏆 {t('points_cheers')}",f"🔔 {t('notifications')}"])
    with tabs[0]:
        if not pending: render_empty_state("✅","Aucune tâche en attente")
        else:
            for req in pending:
                render_request_card(req)
                with st.expander(f"🔧 — {req.get('title','')[:40]}"):
                    render_workflow_progress(req)
                    # ── Accept / Decline assignment ──
                    if req.get("status") == "ASSIGNED" and not req.get("assignment_accepted") and not req.get("assignment_declined"):
                        st.markdown("##### 📋 Accepter ou décliner l'assignation")
                        ac1, ac2 = st.columns(2)
                        with ac1:
                            if st.button("✅ Accepter", key=f"m_accept_{req['id']}", type="primary"):
                                req["assignment_accepted"] = True
                                req["assignment_accepted_at"] = datetime.now(timezone.utc).isoformat()
                                save_request(req)
                                st.success("✅ Assignation acceptée"); st.rerun()
                        with ac2:
                            decline_reason = st.text_input("Raison du refus", key=f"m_decline_r_{req['id']}")
                            if st.button("❌ Décliner", key=f"m_decline_{req['id']}"):
                                if decline_reason.strip():
                                    req["assignment_declined"] = True
                                    req["assignment_decline_reason"] = decline_reason.strip()
                                    save_request(req)
                                    st.warning("❌ Assignation déclinée"); st.rerun()
                                else:
                                    st.warning("Raison obligatoire")
                        st.markdown("---")
                    # ── Appointment proposal (after accepted, no appointment yet) ──
                    if req.get("assignment_accepted") and not req.get("appointment_date"):
                        st.markdown("##### 📅 Proposer un rendez-vous")
                        appt_date = st.date_input("Date du rendez-vous", key=f"m_appt_{req['id']}")
                        if st.button("📅 Proposer", key=f"m_appt_btn_{req['id']}"):
                            req["appointment_date"] = str(appt_date)
                            req["appointment_proposed_by"] = user.get("id", "")
                            save_request(req)
                            st.success(f"📅 Rendez-vous proposé: {appt_date}"); st.rerun()
                        st.markdown("---")
                    elif req.get("appointment_date"):
                        appt_confirmed = "✅" if req.get("appointment_confirmed") else "⏳"
                        st.info(f"📅 Rendez-vous: {req['appointment_date']} {appt_confirmed}")
                    # ── Reception sheet ──
                    if req.get("appointment_confirmed"):
                        if st.button("📋 Fiche de réception", key=f"recv_{req['id']}"):
                            from services.document_service import generate_sample_reception_sheet
                            path = generate_sample_reception_sheet(req)
                            if path and os.path.exists(path):
                                with open(path, "rb") as f:
                                    st.download_button("⬇️ Télécharger", f.read(), file_name=os.path.basename(path), key=f"recv_dl_{req['id']}")
                    # ── QR Code ──
                    qr_data = f"PLAGENOR-REQ:{req.get('display_id') or req.get('id','')}"
                    st.markdown(generate_qr_html(qr_data, size=120), unsafe_allow_html=True)
                    st.markdown("---")
                    # ── Workflow transitions ──
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
                                # SEC-08: MIME-type validation
                                from utils.validation import validate_file_mime
                                mime_ok, mime_err = validate_file_mime(uploaded.name, uploaded.getvalue(), set(ALLOWED_UPLOAD_TYPES))
                                ext = os.path.splitext(uploaded.name)[1].lower()
                                if not mime_ok:
                                    st.error(f"❌ {mime_err}")
                                elif ext not in ALLOWED_UPLOAD_TYPES:
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
                            # UX-02: Require file upload before REPORT_UPLOADED
                            if ns == "REPORT_UPLOADED" and not req.get("report_file"):
                                st.error("❌ Veuillez uploader le rapport avant de valider cette transition.")
                            else:
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
        # Member Profile
        if member:
            st.markdown(f"### {member.get('full_name', '')}")
            st.write(f"**ID:** {member.get('id', '')[:8]}")
            from core.repository import get_all_techniques
            all_techs = get_all_techniques()
            tech_names = [tc.get("name", "") for tc in all_techs]
            current_techs = member.get("skills", [])
            # skills may be stored as IDs or names — normalize to names
            current_tech_names = []
            for s in current_techs:
                if s in tech_names:
                    current_tech_names.append(s)
                else:
                    # Try to find by ID
                    matched = [tc.get("name", "") for tc in all_techs if tc.get("id") == s]
                    if matched:
                        current_tech_names.append(matched[0])
            selected = st.multiselect("Mes techniques", tech_names, default=[t_n for t_n in current_tech_names if t_n in tech_names])
            if st.button("💾 Mettre à jour mes techniques", type="primary"):
                member["skills"] = selected
                save_member(member)
                st.success("Techniques mises à jour!")
                st.rerun()
        else:
            render_empty_state("👤", "Profil analyste non trouvé")
    with tabs[4]:
        # Points & Cheers
        if mid:
            points_data = get_member_points(mid)
            c1,c2 = st.columns(2)
            with c1:
                render_kpi_card("⭐", points_data["total_points"], "Points totaux", "orange")
            with c2:
                render_kpi_card("💬", len(points_data["cheers"]), "Encouragements", "teal")
            st.markdown("<br/>", unsafe_allow_html=True)
            # Progress bar to 100 points
            total_pts = points_data["total_points"]
            render_progress_bar(min(total_pts, 100), 100, "orange", f"Progression: {total_pts}/100 pts")
            # Gift box
            if member and member.get("gift_unlocked"):
                st.markdown('<div style="padding:16px;background:#FFFDE7;border-radius:12px;border:1px solid #F9A825;margin:12px 0;text-align:center">'
                            '<span style="font-size:48px">🎁</span><br/>'
                            '<strong style="color:#F57F17;font-size:18px">Félicitations ! Vous avez débloqué une récompense !</strong><br/>'
                            '<span style="color:#795548">Contactez votre administrateur pour récupérer votre cadeau.</span></div>',
                            unsafe_allow_html=True)
                if member.get("gift_image"):
                    st.image(member["gift_image"], caption="Votre récompense", width=200)
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
    with tabs[5]:
        notifs = get_user_notifications(user.get("id",""))
        if not notifs: render_empty_state("🔔","Aucune notification")
        else:
            for n in notifs[:30]:
                read = "opacity:0.5" if n.get("read") else ""
                st.markdown(f'<div style="padding:8px 12px;border-left:3px solid #2E86C1;margin-bottom:6px;font-size:13px;{read}">{n.get("message","")} <span style="color:#ABB2B9;margin-left:8px">{fmt_date(n.get("created_at",""))}</span></div>', unsafe_allow_html=True)
