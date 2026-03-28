# ui/platform_admin_dashboard.py — PLAGENOR 4.0 Platform Admin Dashboard
# Admin validates requests, reviews prices, generates platform notes
from __future__ import annotations
import streamlit as st, uuid, os
from datetime import datetime, timezone
import config
from ui.styles import get_global_css
from ui.shared_components import (
    render_sidebar_user, render_kpi_card, render_request_card,
    render_empty_state, render_workflow_progress, render_progress_bar,
    fmt_date, fmt_datetime, fmt_currency, resolve_username,
    section_header, get_status_badge_html, get_channel_badge_html,
    render_export_button, render_pagination, get_urgency_badge_html,
)
from core.repository import (
    get_all_active_requests, get_all_members, get_all_services,
    get_request, save_request, get_platform_stats, get_all_invoices,
    get_all_documents, add_points_to_member, add_cheer_to_member,
    add_comment_to_request, get_member, save_member,
)
from core.workflow_engine import transition, get_allowed_transitions
from core.assignment_engine import get_recommended_members
from core.financial_engine import get_budget_dashboard, generate_invoice
from core.audit_engine import log_action
from services.document_service import generate_platform_note, generate_ibtikar_form, generate_genoclab_quote, generate_invoice_document
from services.pricing_engine import format_price
from core.logger import get_logger
from utils.i18n import t

_log = get_logger("platform_admin_dashboard")

def render_platform_admin_dashboard(user):
    try:
        _render_platform_admin_dashboard_inner(user)
    except Exception as e:
        _log.exception("Erreur dans le tableau Admin Plateforme")
        st.error(f"❌ Une erreur inattendue s'est produite dans le tableau Admin Plateforme. Veuillez réessayer ou contacter l'administrateur.\n\nDétail: {e}")

def _render_platform_admin_dashboard_inner(user):
    st.session_state["user"] = user
    st.session_state["authenticated"] = True
    st.markdown(get_global_css(), unsafe_allow_html=True)
    render_sidebar_user(user)
    st.markdown(f'<div style="margin-bottom:24px"><h2 style="color:#1B2838;margin:0">⚙️ {t("welcome_admin")}</h2><p style="color:#7F8C9B;margin:4px 0 0">{t("requests")}, {t("validation")}, {t("documents")}</p></div>', unsafe_allow_html=True)

    stats = get_platform_stats()
    budget = get_budget_dashboard()
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: render_kpi_card("📋", stats["total_requests"], t("requests"), "blue")
    with c2: render_kpi_card("🏛", stats["ibtikar_active"], t("ibtikar"), "blue")
    with c3: render_kpi_card("🧬", stats["genoclab_active"], t("genoclab"), "teal")
    with c4: render_kpi_card("✅", stats["completed"], t("completed"), "green")
    with c5: render_kpi_card("💰", f"{budget['pct']:.0f}%", t("budget"), "orange" if budget["pct"]>70 else "blue")
    st.markdown("<br/>", unsafe_allow_html=True)

    tabs = st.tabs([f"⏳ {t('pending')}",f"📋 {t('all_requests')}",f"🎯 {t('assignment')}",f"💰 {t('budget')}",f"📄 {t('documents')}"])
    with tabs[0]: _pending(user)
    with tabs[1]: _all_requests(user)
    with tabs[2]: _assignment(user)
    with tabs[3]: _budget()
    with tabs[4]: _documents(user)

def _pending(user):
    requests = get_all_active_requests()
    actionable_states = {"SUBMITTED","VALIDATION_PEDAGOGIQUE","VALIDATION_FINANCE",
                         "PLATFORM_NOTE_GENERATED","SAMPLE_RECEIVED","ANALYSIS_FINISHED",
                         "REPORT_UPLOADED","REPORT_VALIDATED",
                         "REQUEST_CREATED","QUOTE_DRAFT","QUOTE_SENT","QUOTE_VALIDATED_BY_CLIENT",
                         "INVOICE_GENERATED","PAYMENT_CONFIRMED","COMPLETED"}
    pending = [r for r in requests if r.get("status") in actionable_states]
    section_header(f"En attente d'action ({len(pending)})", "⏳")

    if not pending: render_empty_state("✅","Aucune action requise"); return

    for req in sorted(pending, key=lambda x: x.get("created_at",""), reverse=True):
        render_request_card(req)
        with st.expander(f"🔧 Traiter — {req.get('title','')[:50]}"):
            render_workflow_progress(req)
            c1, c2 = st.columns([2,1])
            with c1:
                st.markdown(f"**Statut:** {get_status_badge_html(req.get('status',''))}", unsafe_allow_html=True)
                st.markdown(f"**Canal:** {get_channel_badge_html(req.get('channel',''))}", unsafe_allow_html=True)
                urgency_h = get_urgency_badge_html(req.get("urgency",""))
                if urgency_h: st.markdown(f"**Urgence:** {urgency_h}", unsafe_allow_html=True)
                if req.get("display_id"): st.write(f"**Réf:** {req['display_id']}")
                if req.get("requester"): st.write(f"**Demandeur:** {req['requester'].get('full_name','')}")
                if req.get("service_code"): st.write(f"**Service:** {req['service_code']}")
                st.write(f"**Échantillons:** {req.get('sample_count','—')}")
            with c2:
                st.write(f"**Créée:** {fmt_datetime(req.get('created_at',''))}")
                if req.get("budget_amount"): st.write(f"**Budget:** {fmt_currency(req['budget_amount'])}")
                if req.get("pricing"):
                    p = req["pricing"]
                    st.write(f"**Prix calculé:** {format_price(p.get('total',0))}")

            # ── APPOINTMENT STATUS ──
            if req.get("appointment_date"):
                appt_confirmed = "✅ Confirmé" if req.get("appointment_confirmed") else "⏳ En attente"
                st.info(f"📅 Rendez-vous: {req['appointment_date']} — {appt_confirmed}")
                if not req.get("appointment_confirmed"):
                    if st.button("✅ Confirmer le rendez-vous", key=f"pa_appt_confirm_{req['id']}"):
                        req["appointment_confirmed"] = True
                        req["appointment_confirmed_at"] = datetime.now(timezone.utc).isoformat()
                        save_request(req)
                        st.success("✅ Rendez-vous confirmé"); st.rerun()
            # ── Assignment status ──
            if req.get("status") == "ASSIGNED":
                if req.get("assignment_accepted"):
                    st.success(f"✅ Assignation acceptée le {fmt_datetime(req.get('assignment_accepted_at',''))}")
                elif req.get("assignment_declined"):
                    st.error(f"❌ Assignation déclinée — Raison: {req.get('assignment_decline_reason','')}")

            # ── PRICE REVIEW (admin can modify) ──
            st.markdown("---")
            pricing = req.get("pricing", {})
            if pricing:
                st.markdown("##### 💰 Révision du prix")
                auto_total = pricing.get("total", 0)
                c1,c2 = st.columns(2)
                with c1:
                    st.write(f"Prix auto-calculé: **{format_price(auto_total)}**")
                    st.write(f"Modèle: {pricing.get('pricing_model','—')}")
                    bd = pricing.get("breakdown",{})
                    if bd: st.write(f"Base: {bd.get('base_price',0)} × {bd.get('multiplier',1)} × {bd.get('rows_billed',0)} = {auto_total}")
                with c2:
                    admin_price = st.number_input("Prix validé (DZD)", value=float(auto_total), min_value=0.0, key=f"ap_{req['id']}")
                    if admin_price != auto_total:
                        st.info(f"Prix modifié: {format_price(auto_total)} → {format_price(admin_price)}")

                if st.button("✅ Valider le prix", key=f"vp_{req['id']}"):
                    req["admin_validated_price"] = admin_price
                    req["price_modified"] = (admin_price != auto_total)
                    save_request(req)
                    log_action("PRICE_VALIDATED", "REQUEST", req["id"], actor=user, details={"auto": auto_total, "validated": admin_price})
                    st.success(f"Prix validé: {format_price(admin_price)}")

            # ── WORKFLOW ACTIONS ──
            st.markdown("---")
            allowed = get_allowed_transitions(req)
            if allowed:
                c1,c2,c3 = st.columns([2,2,1])
                with c1: ns = st.selectbox("Transition →", sorted(allowed), key=f"pa_t_{req['id']}")
                with c2: notes = st.text_input("Notes", key=f"pa_n_{req['id']}")
                kwargs = {"details": {"notes": notes}}

                if ns in ("REJECTED",):
                    kwargs["rejection_reason"] = st.text_area("Raison du rejet", key=f"pa_rj_{req['id']}")

                if ns == "ASSIGNED":
                    members = get_all_members()
                    avail = [m for m in members if m.get("available",True)]
                    if avail:
                        recs = get_recommended_members(req.get("service_id",""))
                        mopts = {f"{m.get('full_name',m.get('name',''))} (score:{m.get('_score',0):.0f})": m.get("id") for m in (recs or avail)}
                        sel = st.selectbox("Assigner à", list(mopts.keys()), key=f"pa_a_{req['id']}")
                        kwargs["member_id"] = mopts[sel]

                with c3:
                    st.markdown("<br/>", unsafe_allow_html=True)
                    if st.button("✅ Exécuter", key=f"pa_e_{req['id']}", type="primary"):
                        with st.spinner("⏳ Transition en cours..."):
                            try:
                                transition(req["id"], ns, user, **kwargs)
                                # Auto-generate documents on certain transitions
                                if ns in ("VALIDATION_PEDAGOGIQUE","VALIDATION_FINANCE"):
                                    try:
                                        from services.registry_loader import get_service_def
                                        svc = get_service_def(req.get("service_code",""))
                                        generate_platform_note(req, user, svc)
                                    except: pass
                                if ns == "QUOTE_DRAFT":
                                    try:
                                        svc = get_service_def(req.get("service_code",""))
                                        if svc: generate_genoclab_quote(req, svc, user)
                                    except: pass
                                if ns == "INVOICE_GENERATED":
                                    try:
                                        inv = generate_invoice(req, user)
                                        generate_invoice_document(inv, req)
                                    except: pass
                                st.success(f"✅ → {ns}"); st.rerun()
                            except Exception as e: st.error(f"❌ {e}")

            # ── REPORT REVIEW (when REPORT_UPLOADED or ADMIN_REVIEW) ──
            if req.get("status") in ("REPORT_UPLOADED", "REPORT_VALIDATED"):
                st.markdown("---")
                st.markdown("##### 📄 Révision du rapport")
                report_file = req.get("report_file", "")
                if report_file and os.path.exists(report_file):
                    with open(report_file, "rb") as rf:
                        st.download_button("📄 Télécharger le rapport", rf.read(),
                                          file_name=os.path.basename(report_file),
                                          key=f"dl_rpt_{req['id']}")
                else:
                    st.info("Aucun fichier de rapport disponible")
                revision_notes = st.text_area("📝 Commentaire de révision",
                                              key=f"rev_notes_{req['id']}",
                                              placeholder="Remarques sur le rapport...")
                uploaded_rev = st.file_uploader("📤 Uploader la version corrigée",
                                               key=f"rev_upload_{req['id']}",
                                               type=["pdf","docx","xlsx","csv","zip"])
                if uploaded_rev:
                    base, ext = os.path.splitext(uploaded_rev.name)
                    rev_path = os.path.join(config.REPORTS_DIR,
                                           f"{req['id'][:8]}_{base}_admin_revised{ext}")
                    with open(rev_path, "wb") as wf:
                        wf.write(uploaded_rev.getbuffer())
                    req["report_file"] = rev_path
                    req["admin_revision_notes"] = revision_notes
                    save_request(req)
                    st.success(f"📎 Version corrigée uploadée: {uploaded_rev.name}")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Valider le rapport", key=f"val_rpt_{req['id']}", type="primary"):
                        try:
                            if revision_notes.strip():
                                req["admin_revision_notes"] = revision_notes
                                save_request(req)
                            transition(req["id"], "REPORT_VALIDATED", user,
                                      details={"notes": revision_notes})
                            st.success("✅ Rapport validé"); st.rerun()
                        except Exception as e:
                            st.error(f"❌ {e}")
                with c2:
                    if st.button("🔄 Renvoyer à l'analyste", key=f"ren_rpt_{req['id']}"):
                        try:
                            req["admin_revision_notes"] = revision_notes
                            save_request(req)
                            transition(req["id"], "ANALYSIS_STARTED", user,
                                      details={"notes": f"Rapport renvoyé: {revision_notes}"})
                            st.success("🔄 Rapport renvoyé à l'analyste"); st.rerun()
                        except Exception as e:
                            st.error(f"❌ {e}")

            # ── COMMENTS ──
            st.markdown("---")
            st.markdown("##### 💬 Commentaires")
            comments = req.get("comments", [])
            if comments:
                for cmt in comments:
                    st.markdown(f'<div style="padding:6px 12px;border-left:3px solid #2E86C1;margin-bottom:4px;font-size:13px"><strong>{cmt.get("author_name","")}</strong> <span style="color:#ABB2B9">({cmt.get("step","")}) {fmt_datetime(cmt.get("created_at",""))}</span><br/>{cmt.get("text","")}</div>', unsafe_allow_html=True)
            else:
                st.caption("Aucun commentaire")
            cmt_text = st.text_area("Ajouter un commentaire", key=f"cmt_{req['id']}",
                                    placeholder="Votre commentaire...", height=80)
            if st.button("💬 Envoyer", key=f"cmt_btn_{req['id']}"):
                if cmt_text.strip():
                    add_comment_to_request(req["id"], cmt_text.strip(), user)
                    log_action("COMMENT_ADDED", "REQUEST", req["id"], actor=user,
                              details={"text": cmt_text[:100]})
                    st.success("💬 Commentaire ajouté"); st.rerun()
                else:
                    st.warning("Le commentaire ne peut pas être vide")

def _all_requests(user):
    all_requests = get_all_active_requests()
    # ── Filtres avancés ──────────────────────────────────────────────
    st.markdown("#### 🔍 Filtres")
    filter_cols = st.columns(4)
    with filter_cols[0]:
        filter_channel = st.selectbox("Canal", ["Tous", "IBTIKAR", "GENOCLAB"], key="filter_channel")
    with filter_cols[1]:
        filter_status = st.selectbox("Statut", ["Tous"] + sorted(set(r.get("status","") for r in all_requests)), key="filter_status")
    with filter_cols[2]:
        filter_period = st.selectbox("Période", ["Tous", "Aujourd'hui", "Cette semaine", "Ce mois", "Cette année"], key="filter_period")
    with filter_cols[3]:
        filter_search = st.text_input("🔎 Recherche", key="filter_search", placeholder="Titre, demandeur...")

    # Apply filters
    filtered = all_requests
    if filter_channel != "Tous":
        filtered = [r for r in filtered if r.get("channel") == filter_channel]
    if filter_status != "Tous":
        filtered = [r for r in filtered if r.get("status") == filter_status]
    if filter_period != "Tous":
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        period_filtered = []
        for r in filtered:
            try:
                created = datetime.fromisoformat(r.get("created_at","").replace("Z","+00:00"))
                if filter_period == "Aujourd'hui" and created.date() != now.date():
                    continue
                elif filter_period == "Cette semaine" and (now - created).days > 7:
                    continue
                elif filter_period == "Ce mois" and created.month != now.month:
                    continue
                elif filter_period == "Cette année" and created.year != now.year:
                    continue
                period_filtered.append(r)
            except Exception:
                period_filtered.append(r)
        filtered = period_filtered
    if filter_search:
        q = filter_search.lower()
        filtered = [r for r in filtered if q in r.get("title","").lower() or q in r.get("requester_name","").lower() or q in r.get("id","").lower()]

    filtered.sort(key=lambda x: x.get("created_at",""), reverse=True)
    st.write(f"**{len(filtered)}** demande(s)")
    render_export_button(filtered, filename="demandes_plateforme.csv", columns=["id","title","channel","status","created_at","service_code","requester_name"])
    if not filtered:
        render_empty_state("📭", "Aucune demande pour le moment. Les nouvelles demandes apparaîtront ici.")
        return
    page = render_pagination(filtered, page_key="pa_all_page")
    for r in page:
        render_request_card(r)

def _assignment(user):
    section_header("Recommandation d'Assignation","🎯")
    from services.registry_loader import get_all_service_codes
    codes = get_all_service_codes()
    if codes:
        sel = st.selectbox("Service", codes, key="pa_asvc")
        recs = get_recommended_members(sel)
        if recs:
            for m in recs:
                sc = m.get("_score",0)
                co = "#27AE60" if sc>=70 else "#F39C12" if sc>=50 else "#E74C3C"
                st.markdown(f'<div class="data-card" style="display:flex;justify-content:space-between;align-items:center"><div><strong>{m.get("full_name",m.get("name",""))}</strong> · Charge: {m.get("current_load",0)}/{m.get("max_load",5)}</div><div><span style="font-weight:700;font-family:monospace;font-size:18px;color:{co}">{sc:.0f}</span></div></div>', unsafe_allow_html=True)
        else: render_empty_state("👥","Aucun analyste disponible")

    # ── Points & Cheers ──
    st.markdown("---")
    section_header("Points & Encouragements","🏆")
    members = get_all_members()
    if not members:
        render_empty_state("👥","Aucun analyste"); return
    member_opts = {f"{m.get('full_name',m.get('name',''))} (pts: {m.get('total_points',0)})": m.get("id") for m in members}
    sel_m = st.selectbox("Analyste", list(member_opts.keys()), key="pa_cheer_m")
    mid = member_opts[sel_m]
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("##### ⭐ Attribuer des points")
        pts = st.number_input("Points (1-100)", min_value=1, max_value=100, value=10, key="pa_pts")
        pts_reason = st.text_input("Raison", key="pa_pts_reason", placeholder="Ex: Excellent travail sur le séquençage")
        if st.button("⭐ Attribuer", key="pa_pts_btn", type="primary"):
            if pts_reason.strip():
                updated_m = add_points_to_member(mid, pts, pts_reason.strip(), user)
                log_action("POINTS_AWARDED","MEMBER",mid,actor=user,details={"points":pts,"reason":pts_reason})
                # Check if gift should be unlocked
                if updated_m and updated_m.get("total_points", 0) >= 100 and not updated_m.get("gift_unlocked"):
                    updated_m["gift_unlocked"] = True
                    save_member(updated_m)
                    st.balloons()
                    st.success(f"✅ {pts} points attribués! 🎁 Récompense débloquée!"); st.rerun()
                else:
                    st.success(f"✅ {pts} points attribués!"); st.rerun()
            else:
                st.warning("Raison obligatoire")
    with c2:
        st.markdown("##### 💬 Envoyer un encouragement")
        cheer = st.text_area("Message", key="pa_cheer_msg", placeholder="Ex: Bravo pour la ponctualité!", height=80)
        if st.button("💬 Envoyer", key="pa_cheer_btn", type="primary"):
            if cheer.strip():
                add_cheer_to_member(mid, cheer.strip(), user)
                log_action("CHEER_SENT","MEMBER",mid,actor=user,details={"message":cheer[:100]})
                st.success("✅ Encouragement envoyé!"); st.rerun()
            else:
                st.warning("Message obligatoire")
    # ── Gift image upload ──
    st.markdown("---")
    section_header("Récompense (Cadeau)", "🎁")
    sel_member = get_member(mid) if mid else None
    if sel_member:
        if sel_member.get("gift_unlocked"):
            st.success(f"🎁 Récompense débloquée pour cet analyste ({sel_member.get('total_points',0)} pts)")
            gift_img = st.file_uploader("📷 Image du cadeau", key="pa_gift_img", type=["png","jpg","jpeg","gif"])
            if gift_img:
                import os
                gift_path = os.path.join(config.DATA_DIR, f"gift_{mid[:8]}_{gift_img.name}")
                with open(gift_path, "wb") as f:
                    f.write(gift_img.getbuffer())
                sel_member["gift_image"] = gift_path
                save_member(sel_member)
                st.success("✅ Image du cadeau enregistrée")
            if sel_member.get("gift_image"):
                st.image(sel_member["gift_image"], caption="Cadeau actuel", width=200)
        else:
            remaining = 100 - sel_member.get("total_points", 0)
            st.info(f"⏳ Encore {remaining} points avant le déverrouillage de la récompense")

def _budget():
    budget = get_budget_dashboard()
    ibk = budget.get("ibtikar", {})
    gcl = budget.get("genoclab", {})
    c1,c2 = st.columns(2)
    with c1:
        section_header("Revenus IBTIKAR (virtuels)","🏛")
        render_kpi_card("💰", fmt_currency(ibk.get('total',0)), f"{ibk.get('count',0)} demandes · {ibk.get('students',0)} étudiants", "orange")
        st.markdown(f'<div style="font-size:13px;color:#64748B;margin-top:8px">ℹ️ {fmt_currency(ibk.get("budget_per_student",200000))} par étudiant / an</div>', unsafe_allow_html=True)
    with c2:
        section_header("Revenus GENOCLAB (réels)","🧬")
        render_kpi_card("💵", fmt_currency(gcl.get('total',0)), f"{gcl.get('count',0)} factures", "green")
    st.markdown("---"); section_header("Factures","🧾")
    invoices = get_all_invoices()
    if not invoices: render_empty_state("🧾","Aucune facture")
    else:
        for inv in sorted(invoices, key=lambda x: x.get("created_at",""), reverse=True):
            st.markdown(f"**{inv.get('invoice_number','')}** · {fmt_date(inv.get('created_at',''))} · **{fmt_currency(inv.get('total_ttc',0))}** {'🔒' if inv.get('locked') else ''}")
            st.markdown("<div style='border-bottom:1px solid #f0f2f6'></div>", unsafe_allow_html=True)

def _documents(user):
    docs = get_all_documents()
    section_header(f"Documents ({len(docs)})","📄")
    if not docs: render_empty_state("📄","Aucun document")
    else:
        for d in sorted(docs, key=lambda x: x.get("created_at",""), reverse=True)[:30]:
            dt=d.get("type",""); icon="📋" if "NOTE" in dt else "🧾" if "INVOICE" in dt else "📄" if "FORM" in dt else "📄"
            st.markdown(f"{icon} **{d.get('filename','')}** · {dt} · {fmt_datetime(d.get('created_at',''))}")
            fp = d.get("filepath","")
            if fp and os.path.exists(fp):
                with open(fp,"rb") as f:
                    st.download_button(f"⬇️ Télécharger", f.read(), file_name=os.path.basename(fp), key=f"dl_{d.get('id','')[:8]}")
            st.markdown("<div style='border-bottom:1px solid #f0f2f6'></div>", unsafe_allow_html=True)
