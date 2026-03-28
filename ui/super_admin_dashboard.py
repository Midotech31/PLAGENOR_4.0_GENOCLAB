# ui/super_admin_dashboard.py — PLAGENOR 4.0 Super Admin Dashboard
from __future__ import annotations
import streamlit as st
import uuid
from datetime import datetime, timezone
import config
from ui.styles import get_global_css
from ui.shared_components import (
    render_sidebar_user, render_kpi_card, render_request_card,
    render_empty_state, render_workflow_progress, render_progress_bar,
    fmt_date, fmt_datetime, fmt_currency, resolve_username,
    resolve_service_name, section_header,
    get_status_badge_html, get_channel_badge_html, get_role_badge_html,
    render_export_button, render_pagination, get_urgency_badge_html,
)
from core.repository import (
    get_all_users, save_user, delete_user,
    get_all_members, save_member, delete_member,
    get_all_services, save_service, delete_service,
    get_all_active_requests, get_all_archived_requests,
    get_all_invoices, get_request, save_request,
    get_all_documents, get_all_notifications,
    get_platform_stats, backup_all,
    get_payment_methods, save_payment_methods,
    get_all_techniques, save_technique, delete_technique,
)
from core.audit_engine import safe_get_all_audit_logs, log_action
from core.workflow_engine import transition, force_transition, get_allowed_transitions
from core.financial_engine import get_budget_dashboard
from core.productivity_engine import recalculate_all, get_all_productivity_stats
from services.notification_service import get_unread_count
from core.logger import get_logger
from utils.i18n import t

_log = get_logger("super_admin_dashboard")

def _hash_pw(pw):
    from utils import hash_password
    return hash_password(pw)

def render_super_admin_dashboard(user):
    try:
        _render_super_admin_dashboard_inner(user)
    except Exception as e:
        _log.exception("Erreur dans le tableau Super Admin")
        st.error(f"❌ Une erreur inattendue s'est produite dans le tableau Super Admin. Veuillez réessayer ou contacter l'administrateur.\n\nDétail: {e}")

def _render_super_admin_dashboard_inner(user):
    st.session_state["user"] = user
    st.session_state["authenticated"] = True
    st.markdown(get_global_css(), unsafe_allow_html=True)
    render_sidebar_user(user)
    unread = get_unread_count(user.get("id", ""))
    badge = f" ({unread} nouvelles)" if unread > 0 else ""
    st.markdown(f'<div style="margin-bottom:24px"><h2 style="color:#1B2838;margin:0">👑 {t("welcome_super_admin")}</h2><p style="color:#7F8C9B;margin:4px 0 0">{t("platform_overview")}{badge}</p></div>', unsafe_allow_html=True)

    stats = get_platform_stats()
    budget = get_budget_dashboard()
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    with c1: render_kpi_card("📋", stats["total_requests"], t("active"), "blue")
    with c2: render_kpi_card("✅", stats["completed"], t("completed"), "green")
    with c3: render_kpi_card("👥", stats["total_users"], t("users"), "purple")
    with c4: render_kpi_card("🔬", stats["total_members"], t("analysts"), "teal")
    with c5: render_kpi_card("🏛", stats["ibtikar_active"], t("ibtikar"), "blue")
    with c6: render_kpi_card("🧬", stats["genoclab_active"], t("genoclab"), "teal")
    st.markdown("<br/>", unsafe_allow_html=True)

    # ── SYMMETRIC REVENUE DISPLAY: IBTIKAR (virtual) | GENOCLAB (real) ──
    ibk = budget.get("ibtikar", {})
    gcl = budget.get("genoclab", {})
    c1, c2 = st.columns(2)
    with c1:
        section_header(f"{t('revenue_virtual')} IBTIKAR", "🏛")
        ca, cb, cc = st.columns(3)
        with ca: render_kpi_card("💰", fmt_currency(ibk.get('total', 0)), t("total_revenue"), "orange")
        with cb: render_kpi_card("📋", str(ibk.get('count', 0)), t("requests"), "blue")
        with cc: render_kpi_card("🎓", str(ibk.get('students', 0)), t("students"), "purple")
        st.markdown(f'<div style="font-size:13px;color:#64748B;margin-top:8px">ℹ️ {t("budget")} : <strong>{fmt_currency(ibk.get("budget_per_student", 200000))}</strong> {t("per_student_year")} (DGRSDT)</div>', unsafe_allow_html=True)
    with c2:
        section_header(f"{t('revenue_real')} GENOCLAB", "🧬")
        ca, cb = st.columns(2)
        with ca: render_kpi_card("💵", fmt_currency(gcl.get('total', 0)), t("total_revenue"), "green")
        with cb: render_kpi_card("🧾", str(gcl.get('count', 0)), t("invoices"), "teal")

    tabs = st.tabs([f"📋 {t('requests')}",f"👥 {t('users')}",f"🔬 {t('analysts')}",f"🧪 {t('services')}",f"📝 {t('forms')}",f"💳 {t('payments')}",f"📊 {t('productivity')}",f"📄 {t('documents')}",f"📜 {t('audit')}",f"⚙️ {t('system')}"])
    with tabs[0]: _tab_requests(user)
    with tabs[1]: _tab_users(user)
    with tabs[2]: _tab_members(user)
    with tabs[3]: _tab_services(user)
    with tabs[4]: _tab_forms(user)
    with tabs[5]: _tab_payments(user)
    with tabs[6]: _tab_productivity()
    with tabs[7]: _tab_documents(user)
    with tabs[8]: _tab_audit()
    with tabs[9]: _tab_system(user)

def _tab_requests(user):
    requests = get_all_active_requests()
    archived = get_all_archived_requests()
    f1,f2,f3,f4 = st.columns(4)
    with f1: ch_filter = st.selectbox("Canal", ["Tous", config.CHANNEL_IBTIKAR, config.CHANNEL_GENOCLAB], key="sa_ch")
    with f2:
        all_st = sorted({r.get("status","") for r in requests})
        st_filter = st.selectbox("Statut", ["Tous"]+all_st, key="sa_st")
    with f3: period_filter = st.selectbox("Période", ["Tous", "Aujourd'hui", "Cette semaine", "Ce mois", "Cette année"], key="sa_period")
    with f4: search = st.text_input("🔍 Rechercher", key="sa_search")
    filtered = requests
    if ch_filter != "Tous": filtered = [r for r in filtered if r.get("channel") == ch_filter]
    if st_filter != "Tous": filtered = [r for r in filtered if r.get("status") == st_filter]
    if period_filter != "Tous":
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        period_filtered = []
        for r in filtered:
            try:
                created = datetime.fromisoformat(r.get("created_at","").replace("Z","+00:00"))
                if period_filter == "Aujourd'hui" and created.date() != now.date():
                    continue
                elif period_filter == "Cette semaine" and (now - created).days > 7:
                    continue
                elif period_filter == "Ce mois" and created.month != now.month:
                    continue
                elif period_filter == "Cette année" and created.year != now.year:
                    continue
                period_filtered.append(r)
            except Exception:
                period_filtered.append(r)
        filtered = period_filtered
    if search:
        s = search.lower()
        filtered = [r for r in filtered if s in r.get("title","").lower() or s in r.get("id","").lower()]
    filtered.sort(key=lambda x: x.get("created_at",""), reverse=True)
    ibk = len([r for r in filtered if r.get("channel")==config.CHANNEL_IBTIKAR])
    geno = len(filtered) - ibk
    st.markdown(f'<div style="font-size:13px;margin:8px 0 16px">📋 <strong>{len(filtered)}</strong> demande(s) · <span style="color:#1B4F72">🏛 {ibk} IBTIKAR</span> · <span style="color:#117A65">🧬 {geno} GENOCLAB</span></div>', unsafe_allow_html=True)
    render_export_button(filtered, filename="demandes_admin.csv", columns=["id","title","channel","status","created_at","service_code","assigned_to","budget_amount"])
    if not filtered:
        render_empty_state("📭","Aucune demande trouvée"); return
    for req in filtered[:50]:
        render_request_card(req)
        with st.expander(f"🔧 Gestion — {req.get('title','')[:50]}"):
            c1,c2 = st.columns([2,1])
            with c1: render_workflow_progress(req)
            with c2:
                st.markdown(f"**ID:** `{req.get('display_id') or req.get('id','')[:12]}`")
                urgency_h = get_urgency_badge_html(req.get("urgency",""))
                if urgency_h: st.markdown(urgency_h, unsafe_allow_html=True)
                st.markdown(f"**Créée:** {fmt_datetime(req.get('created_at',''))}")
                if req.get("assigned_to"): st.markdown(f"**Assigné:** {resolve_username(req['assigned_to'])}")
                if req.get("budget_amount"): st.markdown(f"**Budget:** {fmt_currency(req['budget_amount'])}")
            st.markdown("---")
            allowed = get_allowed_transitions(req)
            if allowed:
                c1,c2,c3 = st.columns([2,2,1])
                with c1: new_state = st.selectbox("Transition →", sorted(allowed), key=f"sa_tr_{req['id']}")
                with c2: reason = st.text_input("Notes", key=f"sa_r_{req['id']}")
                with c3:
                    st.markdown("<br/>", unsafe_allow_html=True)
                    if st.button("✅", key=f"sa_e_{req['id']}", type="primary"):
                        with st.spinner("⏳ Transition en cours..."):
                            try:
                                kw = {"details": {"reason": reason}}
                                transition(req["id"], new_state, user, **kw)
                                st.success(f"✅ → {new_state}"); st.rerun()
                            except Exception as e: st.error(str(e))
                if new_state == "ASSIGNED":
                    members = get_all_members()
                    avail = [m for m in members if m.get("available", True)]
                    if avail:
                        mopts = {f"{m.get('full_name',m.get('name',''))} ({m.get('current_load',0)}/{m.get('max_load',5)})": m.get("id") for m in avail}
                        sel = st.selectbox("Assigner à", list(mopts.keys()), key=f"sa_a_{req['id']}")
                        if st.button("👤 Assigner", key=f"sa_da_{req['id']}"):
                            try:
                                transition(req["id"], "ASSIGNED", user, member_id=mopts[sel])
                                st.success("✅ Assigné"); st.rerun()
                            except Exception as e: st.error(str(e))
            else:
                st.info("État terminal — aucune transition possible")
            st.markdown("---")
            if st.checkbox("⚡ Forcer une transition (override SA)", key=f"sa_fc_{req['id']}"):
                all_states = sorted(set(config.IBTIKAR_STATES + config.GENOCLAB_STATES))
                fs = st.selectbox("Forcer →", all_states, key=f"sa_f_{req['id']}")
                fr = st.text_area("Justification", key=f"sa_fr_{req['id']}")
                if st.button("⚡ Forcer", key=f"sa_fe_{req['id']}"):
                    if not fr or len(fr)<10: st.warning("Justification requise (min 10 car.)")
                    else:
                        try:
                            force_transition(req["id"], fs, user, fr)
                            st.success(f"⚡ → {fs}"); st.rerun()
                        except Exception as e: st.error(str(e))
            history = req.get("history", [])
            if history and st.checkbox(f"📜 Historique ({len(history)})", key=f"sa_h_{req['id']}"):
                for h in reversed(history):
                    forced = " ⚡" if h.get("forced") else ""
                    st.markdown(f'<div style="padding:4px 0;font-size:12px;border-bottom:1px solid #f0f0f0"><strong>{h.get("from","?")}</strong> → <strong>{h.get("to","?")}</strong> <span style="color:#7F8C9B">par {h.get("by","?")}</span> <span style="color:#ABB2B9">{fmt_datetime(h.get("at",""))}</span><span style="color:#E74C3C">{forced}</span></div>', unsafe_allow_html=True)
    if archived:
        st.markdown("---")
        with st.expander(f"📦 Archives ({len(archived)})"):
            for r in archived[:20]: render_request_card(r)

def _tab_users(user):
    users = get_all_users()
    section_header(f"Utilisateurs ({len(users)})", "👥")
    with st.expander("➕ Ajouter un utilisateur"):
        with st.form("add_user_form", clear_on_submit=True):
            c1,c2 = st.columns(2)
            with c1:
                nu = st.text_input("Identifiant *"); nf = st.text_input("Nom complet *"); ne = st.text_input("Email")
            with c2:
                nr = st.selectbox("Rôle *", config.ALL_ROLES); np = st.text_input("Mot de passe *", type="password"); no = st.text_input("Organisation", value="ESSBO")
            if st.form_submit_button("✅ Créer", type="primary"):
                if not nu or not np or not nf: st.warning("Champs obligatoires manquants")
                elif any(u.get("username")==nu.strip() for u in users): st.error("Identifiant existe déjà")
                elif ne.strip() and any(u.get("email","").lower()==ne.strip().lower() for u in users): st.error("❌ Cette adresse email est déjà utilisée par un autre compte.")
                else:
                    new_u = {"id": str(uuid.uuid4()), "username": nu.strip(), "full_name": nf.strip(), "password_hash": _hash_pw(np), "role": nr, "email": ne.strip(), "organization_id": no.strip(), "active": True, "created_at": datetime.now(timezone.utc).isoformat()}
                    save_user(new_u); log_action("USER_CREATED", "USER", new_u["id"], actor=user, details={"username": nu, "role": nr})
                    st.success(f"✅ {nu} créé"); st.rerun()
    if not users:
        render_empty_state("👥", "Aucun utilisateur enregistré")
        return
    for u in users:
        c1,c2,c3,c4 = st.columns([3,2,2,1])
        with c1:
            dot = "🟢" if u.get("active",True) else "🔴"
            st.markdown(f"{dot} **{u.get('full_name',u.get('username',''))}** · `{u.get('username','')}`")
        with c2: st.markdown(get_role_badge_html(u.get("role","")), unsafe_allow_html=True)
        with c3: st.write(f"{u.get('organization_id','')} · {fmt_date(u.get('created_at',''))}")
        with c4:
            if u.get("id") != user.get("id"):
                lbl = "⏸️" if u.get("active",True) else "▶️"
                if st.button(lbl, key=f"tu_{u['id']}", help="Activer/Désactiver"):
                    u["active"] = not u.get("active",True); save_user(u)
                    log_action("USER_TOGGLED", "USER", u["id"], actor=user); st.rerun()
        st.markdown("<div style='border-bottom:1px solid #f0f2f6'></div>", unsafe_allow_html=True)
    st.markdown("---")
    with st.expander("🔑 Réinitialiser un mot de passe"):
        tu = {u.get("username",""): u.get("id","") for u in users}
        su = st.selectbox("Utilisateur", list(tu.keys()), key="rpw_u")
        npw = st.text_input("Nouveau mot de passe", type="password", key="rpw_v")
        if st.button("🔑 Réinitialiser", key="rpw_b"):
            if npw and len(npw) >= config.MIN_PASSWORD_LENGTH:
                uid = tu[su]; ux = next((x for x in users if x.get("id")==uid), None)
                if ux: ux["password_hash"] = _hash_pw(npw); save_user(ux); log_action("PASSWORD_RESET","USER",uid,actor=user); st.success(f"✅ MDP de {su} réinitialisé")
            else: st.warning(f"Min {config.MIN_PASSWORD_LENGTH} caractères")

def _tab_members(user):
    members = get_all_members()
    section_header(f"Analystes ({len(members)})", "🔬")
    with st.expander("➕ Ajouter un analyste"):
        with st.form("add_m", clear_on_submit=True):
            c1,c2 = st.columns(2)
            with c1: mn = st.text_input("Nom *"); mu = st.text_input("ID Utilisateur")
            with c2:
                ml = st.number_input("Charge max", value=5, min_value=1, max_value=20)
                svcs = get_all_services()
                ms = st.multiselect("Compétences", [s.get("name","") for s in svcs])
            if st.form_submit_button("✅ Ajouter", type="primary"):
                if mn:
                    sids = [s.get("id") for s in svcs if s.get("name") in ms]
                    m = {"id": str(uuid.uuid4()), "full_name": mn.strip(), "name": mn.strip(), "user_id": mu.strip(), "max_load": ml, "current_load": 0, "skills": sids, "available": True, "productivity_score": 50.0, "productivity_status": "NORMAL", "created_at": datetime.now(timezone.utc).isoformat()}
                    save_member(m); log_action("MEMBER_CREATED","MEMBER",m["id"],actor=user); st.success(f"✅ {mn} ajouté"); st.rerun()
    if not members: render_empty_state("🔬","Aucun analyste"); return
    for m in members:
        c1,c2,c3,c4 = st.columns([3,2,2,1])
        with c1:
            av = "🟢" if m.get("available",True) else "🔴"
            st.markdown(f"{av} **{m.get('full_name',m.get('name',''))}**")
        with c2:
            load,mx = m.get("current_load",0), m.get("max_load",5)
            pct = (load/mx*100) if mx>0 else 0
            bc = "#27AE60" if pct<60 else "#F39C12" if pct<85 else "#E74C3C"
            st.markdown(f'<div style="font-size:13px">Charge: {load}/{mx}</div><div class="progress-container"><div class="progress-bar" style="width:{pct:.0f}%;background:{bc}"></div></div>', unsafe_allow_html=True)
        with c3:
            sc = m.get("productivity_score",50); ss = m.get("productivity_status","NORMAL")
            em = config.PRODUCTIVITY_EMOJI.get(ss,"⚪")
            co = "#27AE60" if sc>=85 else "#2E86C1" if sc>=70 else "#F39C12" if sc>=50 else "#E74C3C"
            st.markdown(f'<div style="font-size:22px;font-weight:700;color:{co};font-family:JetBrains Mono">{em} {sc:.0f}%</div>', unsafe_allow_html=True)
        with c4:
            if st.button("⏸️" if m.get("available",True) else "▶️", key=f"tm_{m['id']}"):
                m["available"] = not m.get("available",True); save_member(m); st.rerun()
        st.markdown("<div style='border-bottom:1px solid #f0f2f6'></div>", unsafe_allow_html=True)

    # ── Technique Management ──
    st.markdown("---")
    section_header("Gestion des Techniques", "🧪")
    techniques = get_all_techniques()
    if techniques:
        for tech in techniques:
            tc1, tc2, tc3, tc4 = st.columns([3, 2, 2, 1])
            with tc1:
                st.markdown(f"**{tech.get('name', '')}**")
            with tc2:
                st.write(tech.get("category", "") or "—")
            with tc3:
                st.write(fmt_date(tech.get("created_at", "")))
            with tc4:
                if st.button("🗑️", key=f"del_tech_{tech['id']}"):
                    delete_technique(tech["id"])
                    log_action("TECHNIQUE_DELETED", "TECHNIQUE", tech["id"], actor=user,
                              details={"name": tech.get("name", "")})
                    st.success(f"🗑️ Technique supprimée"); st.rerun()
            st.markdown("<div style='border-bottom:1px solid #f0f2f6'></div>", unsafe_allow_html=True)
    else:
        render_empty_state("🧪", "Aucune technique enregistrée")
    st.markdown("##### ➕ Ajouter une technique")
    with st.form("add_technique_form", clear_on_submit=True):
        tc1, tc2 = st.columns(2)
        with tc1:
            tech_name = st.text_input("Nom de la technique *", key="tech_name")
        with tc2:
            tech_category = st.text_input("Catégorie", key="tech_category",
                                          placeholder="Ex: Séquençage, Extraction, PCR")
        if st.form_submit_button("✅ Ajouter", type="primary"):
            if tech_name.strip():
                existing_names = [t.get("name", "").lower() for t in techniques]
                if tech_name.strip().lower() in existing_names:
                    st.error("❌ Cette technique existe déjà")
                else:
                    new_tech = save_technique({
                        "name": tech_name.strip(),
                        "category": tech_category.strip(),
                        "active": True,
                    })
                    log_action("TECHNIQUE_CREATED", "TECHNIQUE", new_tech["id"], actor=user,
                              details={"name": tech_name.strip()})
                    st.success(f"✅ Technique '{tech_name.strip()}' ajoutée"); st.rerun()
            else:
                st.warning("Nom obligatoire")

def _tab_services(user):
    services = get_all_services()
    section_header(f"Services ({len(services)})", "🧪")
    # ── Add new service ──
    with st.expander("➕ Ajouter un service"):
        with st.form("add_s", clear_on_submit=True):
            c1,c2 = st.columns(2)
            with c1:
                sn = st.text_input("Nom *")
                s_avail = st.selectbox("Disponibilité canal", ["BOTH","IBTIKAR","GENOCLAB"], key="new_s_avail")
                sp_ibk = st.number_input("Prix IBTIKAR (DZD)", value=0.0, key="new_sp_ibk")
            with c2:
                scode = st.text_input("Code")
                stype = st.selectbox("Type", ["Analysis","Extraction","Sequencing","Other"])
                sp_gcl = st.number_input("Prix GENOCLAB (DZD)", value=0.0, key="new_sp_gcl")
            sd = st.number_input("Délai (j)", value=7, min_value=1)
            sdesc = st.text_area("Description")
            if st.form_submit_button("✅ Ajouter", type="primary"):
                if sn:
                    channel_val = config.CHANNEL_IBTIKAR if s_avail == "IBTIKAR" else config.CHANNEL_GENOCLAB if s_avail == "GENOCLAB" else config.CHANNEL_IBTIKAR
                    sv = {
                        "id": str(uuid.uuid4()),
                        "code": scode.strip() or f"SVC-{str(uuid.uuid4())[:4].upper()}",
                        "name": sn.strip(), "description": sdesc.strip(),
                        "channel": channel_val,
                        "channel_availability": s_avail,
                        "type": stype,
                        "base_price": sp_ibk if s_avail == "IBTIKAR" else sp_gcl,
                        "price": sp_ibk if s_avail == "IBTIKAR" else sp_gcl,
                        "ibtikar_price": sp_ibk, "genoclab_price": sp_gcl,
                        "turnaround_days": sd, "active": True,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                    save_service(sv); log_action("SERVICE_CREATED","SERVICE",sv["id"],actor=user)
                    st.success(f"✅ {sn} ajouté"); st.rerun()
    # ── Filter ──
    ch = st.selectbox("Filtrer", ["Tous",config.CHANNEL_IBTIKAR,config.CHANNEL_GENOCLAB,"BOTH"], key="sa_sf")
    if ch == "Tous":
        display = services
    elif ch == "BOTH":
        display = [s for s in services if s.get("channel_availability") == "BOTH"]
    else:
        display = [s for s in services if s.get("channel") == ch or s.get("channel_availability") in (ch, "BOTH")]
    # ── Display services ──
    for s in display:
        c1,c2,c3,c4 = st.columns([4,1,2,2])
        avail = s.get("channel_availability", s.get("channel",""))
        with c1: st.markdown(f"**{s.get('name','')}** <span style='font-size:11px;color:#7F8C9B'>{s.get('code','')} · {(s.get('description') or '')[:60]}</span>", unsafe_allow_html=True)
        with c2: st.markdown(f"<span style='font-size:11px;font-weight:600;color:#1B4F72'>{avail}</span>", unsafe_allow_html=True)
        with c3:
            ibk_p = s.get("ibtikar_price") or s.get("base_price") or s.get("price") or 0
            gcl_p = s.get("genoclab_price") or s.get("base_price") or s.get("price") or 0
            if avail == "BOTH":
                st.write(f"IBK: {fmt_currency(ibk_p)} / GCL: {fmt_currency(gcl_p)}")
            else:
                st.write(fmt_currency(s.get("base_price") or s.get("price") or 0))
        with c4: st.write(f"⏱ {s.get('turnaround_days','?')}j · {'🟢' if s.get('active',True) else '🔴'}")
        # ── Edit & Delete ──
        with st.expander(f"✏️ Modifier — {s.get('name','')[:30]}"):
            with st.form(f"edit_s_{s['id']}", clear_on_submit=False):
                ec1,ec2 = st.columns(2)
                with ec1:
                    e_name = st.text_input("Nom", value=s.get("name",""), key=f"en_{s['id']}")
                    e_avail = st.selectbox("Disponibilité canal", ["BOTH","IBTIKAR","GENOCLAB"],
                                           index=["BOTH","IBTIKAR","GENOCLAB"].index(s.get("channel_availability","BOTH") if s.get("channel_availability") else "BOTH"),
                                           key=f"ea_{s['id']}")
                    e_ibk = st.number_input("Prix IBTIKAR (DZD)", value=float(s.get("ibtikar_price") or s.get("base_price") or 0), key=f"epi_{s['id']}")
                with ec2:
                    e_desc = st.text_input("Description", value=(s.get("description") or "")[:200], key=f"ed_{s['id']}")
                    e_td = st.number_input("Délai (j)", value=int(s.get("turnaround_days") or 7), min_value=1, key=f"et_{s['id']}")
                    e_gcl = st.number_input("Prix GENOCLAB (DZD)", value=float(s.get("genoclab_price") or s.get("base_price") or 0), key=f"epg_{s['id']}")
                e_active = st.checkbox("Actif", value=s.get("active",True), key=f"eact_{s['id']}")
                if st.form_submit_button("💾 Sauvegarder", type="primary"):
                    s["name"] = e_name.strip(); s["description"] = e_desc.strip()
                    s["channel_availability"] = e_avail
                    s["channel"] = config.CHANNEL_IBTIKAR if e_avail == "IBTIKAR" else config.CHANNEL_GENOCLAB if e_avail == "GENOCLAB" else s.get("channel", config.CHANNEL_IBTIKAR)
                    s["ibtikar_price"] = e_ibk; s["genoclab_price"] = e_gcl
                    s["base_price"] = e_ibk if e_avail == "IBTIKAR" else e_gcl if e_avail == "GENOCLAB" else e_ibk
                    s["price"] = s["base_price"]
                    s["turnaround_days"] = e_td; s["active"] = e_active
                    s["updated_at"] = datetime.now(timezone.utc).isoformat()
                    save_service(s); log_action("SERVICE_UPDATED","SERVICE",s["id"],actor=user)
                    st.success("✅ Service mis à jour"); st.rerun()
            # Delete with confirmation
            if st.checkbox(f"🗑️ Supprimer ce service", key=f"del_chk_{s['id']}"):
                if st.button(f"⚠️ Confirmer la suppression", key=f"del_btn_{s['id']}"):
                    delete_service(s["id"])
                    log_action("SERVICE_DELETED","SERVICE",s["id"],actor=user,details={"name": s.get("name","")})
                    st.success(f"🗑️ Service supprimé"); st.rerun()
        st.markdown("<div style='border-bottom:1px solid #f0f2f6'></div>", unsafe_allow_html=True)

def _tab_forms(user):
    from services.registry_loader import get_all_yaml_files, save_service_yaml
    section_header("Configuration des Formulaires YAML", "📝")
    yamls = get_all_yaml_files()
    if not yamls:
        render_empty_state("📝", "Aucun fichier YAML trouvé dans templates/registry/")
        return
    for yf in yamls:
        svc_code = yf["service_code"]
        svc_name = yf["service_name"]
        data = yf["data"]
        fields = data.get("requester_fields", data.get("parameters", []))
        st.markdown(f"**{svc_name}** (`{svc_code}`) — {len(fields)} champ(s) · `{yf['filename']}`")
        with st.expander(f"✏️ Modifier — {svc_name}"):
            # Display existing fields
            for idx, field in enumerate(fields):
                c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
                with c1:
                    st.text_input("Nom", value=field.get("name", ""),
                                 key=f"ff_n_{svc_code}_{idx}", disabled=True)
                with c2:
                    st.text_input("Label", value=field.get("label", ""),
                                 key=f"ff_l_{svc_code}_{idx}", disabled=True)
                with c3:
                    st.text_input("Type", value=field.get("type", "string"),
                                 key=f"ff_t_{svc_code}_{idx}", disabled=True)
                with c4:
                    if st.button("🗑️", key=f"ff_del_{svc_code}_{idx}"):
                        fields.pop(idx)
                        if "requester_fields" in data:
                            data["requester_fields"] = fields
                        else:
                            data["parameters"] = fields
                        save_service_yaml(svc_code, data)
                        log_action("FORM_FIELD_REMOVED", "SERVICE", svc_code, actor=user,
                                  details={"field": field.get("name", "")})
                        st.success(f"🗑️ Champ supprimé"); st.rerun()
            # Add new field
            st.markdown("---")
            st.markdown("##### ➕ Ajouter un champ")
            ac1, ac2, ac3 = st.columns(3)
            with ac1:
                new_name = st.text_input("Nom technique", key=f"ff_nn_{svc_code}",
                                        placeholder="ex: sample_origin")
                new_label = st.text_input("Label affiché", key=f"ff_nl_{svc_code}",
                                         placeholder="ex: Origine de l'échantillon")
            with ac2:
                new_type = st.selectbox("Type", ["string", "text", "integer", "float", "enum", "boolean"],
                                       key=f"ff_nt_{svc_code}")
                new_req = st.checkbox("Obligatoire", value=True, key=f"ff_nr_{svc_code}")
            with ac3:
                new_opts = st.text_input("Options (enum, séparées par virgule)",
                                        key=f"ff_no_{svc_code}",
                                        placeholder="opt1,opt2,opt3")
            if st.button("➕ Ajouter le champ", key=f"ff_add_{svc_code}", type="primary"):
                if new_name.strip() and new_label.strip():
                    new_field = {
                        "name": new_name.strip(),
                        "label": new_label.strip(),
                        "type": new_type,
                        "required": new_req,
                    }
                    if new_type == "enum" and new_opts.strip():
                        new_field["options"] = [o.strip() for o in new_opts.split(",") if o.strip()]
                    fields.append(new_field)
                    if "requester_fields" in data:
                        data["requester_fields"] = fields
                    else:
                        data["parameters"] = fields
                    save_service_yaml(svc_code, data)
                    log_action("FORM_FIELD_ADDED", "SERVICE", svc_code, actor=user,
                              details={"field": new_name})
                    st.success(f"✅ Champ '{new_label}' ajouté"); st.rerun()
                else:
                    st.warning("Nom et label obligatoires")
        st.markdown("<div style='border-bottom:1px solid #f0f2f6'></div>", unsafe_allow_html=True)


def _tab_payments(user):
    section_header("Modes de Paiement GENOCLAB", "💳")
    methods = get_payment_methods()
    st.markdown(f"**{len(methods)}** mode(s) de paiement configuré(s)")
    for idx, method in enumerate(methods):
        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown(f"💳 **{method}**")
        with c2:
            if st.button("🗑️", key=f"pm_del_{idx}"):
                methods.pop(idx)
                save_payment_methods(methods)
                log_action("PAYMENT_METHOD_REMOVED", "SYSTEM", "payment_methods",
                          actor=user, details={"method": method})
                st.success(f"🗑️ '{method}' supprimé"); st.rerun()
        st.markdown("<div style='border-bottom:1px solid #f0f2f6'></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("##### ➕ Ajouter un mode de paiement")
    new_method = st.text_input("Nom du mode de paiement", key="pm_new",
                               placeholder="Ex: Carte bancaire")
    if st.button("➕ Ajouter", key="pm_add", type="primary"):
        if new_method.strip():
            if new_method.strip() in methods:
                st.warning("Ce mode de paiement existe déjà")
            else:
                methods.append(new_method.strip())
                save_payment_methods(methods)
                log_action("PAYMENT_METHOD_ADDED", "SYSTEM", "payment_methods",
                          actor=user, details={"method": new_method.strip()})
                st.success(f"✅ '{new_method.strip()}' ajouté"); st.rerun()
        else:
            st.warning("Nom obligatoire")


def _tab_productivity():
    section_header("Productivité", "📊")
    c1,c2 = st.columns([3,1])
    with c2:
        if st.button("🔄 Recalculer", key="rc", type="primary"):
            recalculate_all(); st.success("✅ Recalculé"); st.rerun()
    stats = get_all_productivity_stats()
    if not stats: render_empty_state("📊","Aucun analyste"); return
    avg = sum(s.get("score",0) for s in stats)/len(stats)
    exc = len([s for s in stats if s.get("status")=="EXCELLENT"])
    low = len([s for s in stats if s.get("status")=="LOW"])
    c1,c2,c3 = st.columns(3)
    with c1: render_kpi_card("📊", f"{avg:.0f}%", "Score moyen", "blue")
    with c2: render_kpi_card("🟢", str(exc), "Excellents", "green")
    with c3: render_kpi_card("🔴", str(low), "En difficulté", "red")
    st.markdown("<br/>", unsafe_allow_html=True)
    for s in sorted(stats, key=lambda x: x.get("score",0), reverse=True):
        em = config.PRODUCTIVITY_EMOJI.get(s.get("status","NORMAL"),"⚪")
        sc = s.get("score",0)
        co = "#27AE60" if sc>=85 else "#2E86C1" if sc>=70 else "#F39C12" if sc>=50 else "#E74C3C"
        c1,c2,c3,c4 = st.columns([3,1,3,1])
        with c1: st.markdown(f"**{s.get('name','?')}**")
        with c2: st.markdown(f"<div style='font-size:24px;font-weight:700;color:{co};font-family:JetBrains Mono'>{sc:.0f}%</div>", unsafe_allow_html=True)
        with c3: st.write(f"✅ {s.get('completed',0)} complétées · 🔬 {s.get('in_progress',0)} en cours · ⏱ {s.get('on_time_rate',0):.0f}% ponctualité")
        with c4: st.markdown(f"<div style='font-size:36px;text-align:center'>{em}</div>", unsafe_allow_html=True)
        st.markdown("<div style='border-bottom:1px solid #f0f2f6'></div>", unsafe_allow_html=True)

def _tab_documents(user):
    docs = get_all_documents()
    section_header(f"Documents ({len(docs)})", "📄")
    if not docs: render_empty_state("📄","Aucun document"); return
    for d in sorted(docs, key=lambda x: x.get("created_at",""), reverse=True)[:50]:
        dt = d.get("type","")
        icon = "📋" if "NOTE" in dt else "🧾" if "INVOICE" in dt else "📄"
        c1,c2,c3 = st.columns([4,2,2])
        with c1: st.markdown(f"{icon} **{d.get('filename','')}** · {dt}")
        with c2: st.write(fmt_datetime(d.get("created_at","")))
        with c3:
            if d.get("request_id"): st.write(f"#{d['request_id'][:8]}")
        st.markdown("<div style='border-bottom:1px solid #f0f2f6'></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("#### 📄 Générer un document")
    requests = get_all_active_requests()
    validated = [r for r in requests if r.get("status") in ("VALIDATION_PEDAGOGIQUE","VALIDATION_FINANCE","PLATFORM_NOTE_GENERATED","QUOTE_VALIDATED_BY_CLIENT")]
    if validated:
        ro = {f"{r.get('title','')} ({r.get('channel','')})": r.get("id") for r in validated}
        sel = st.selectbox("Demande", list(ro.keys()), key="gd_s")
        if st.button("📄 Générer", key="gd_b"):
            from services.document_service import generate_platform_note
            req = next((r for r in validated if r.get("id")==ro[sel]), None)
            if req:
                p = generate_platform_note(req, user)
                st.success(f"✅ Document généré" if p else "⚠️ Erreur")

def _tab_audit():
    section_header("Journal d'Audit", "📜")
    logs = safe_get_all_audit_logs()
    f1,f2,f3 = st.columns(3)
    with f1: af = st.text_input("🔍 Action", key="sa_af")
    with f2: uf = st.text_input("👤 Utilisateur", key="sa_uf")
    with f3: tf = st.selectbox("Type", ["Tous","AUTH","REQUEST","FINANCIAL","USER","MEMBER","SYSTEM"], key="sa_tf")
    filtered = logs
    if af: filtered = [l for l in filtered if af.lower() in l.get("action","").lower()]
    if uf: filtered = [l for l in filtered if uf.lower() in l.get("actor_username","").lower()]
    if tf != "Tous": filtered = [l for l in filtered if l.get("entity_type")==tf or tf in l.get("action","")]
    st.write(f"**{len(filtered)}** / {len(logs)} entrées")
    render_export_button(filtered, filename="audit_logs.csv", columns=["id","action","entity_type","actor_username","timestamp"])
    sorted_logs = sorted(filtered, key=lambda x: x.get("timestamp",""), reverse=True)
    paged_logs = render_pagination(sorted_logs, "audit_page", items_per_page=50)
    from utils import sanitize_html as _esc
    for e in paged_logs:
        a = _esc(e.get("action",""))
        icon = "🔑" if "LOGIN" in a else "🔄" if "TRANSITION" in a else "💰" if "FINANCIAL" in a or "BUDGET" in a else "⚠️" if "OVERRIDE" in a else "➕" if "CREATED" in a else "🔵"
        username = _esc(e.get("actor_username","system"))
        st.markdown(f'<div style="padding:6px 12px;border-left:3px solid #E8ECF1;margin-bottom:4px;font-size:13px">{icon} <strong>{a}</strong> <span style="color:#7F8C9B;margin-left:8px">par {username}</span> <span style="color:#ABB2B9;margin-left:8px">{fmt_datetime(e.get("timestamp",""))}</span></div>', unsafe_allow_html=True)

def _tab_system(user):
    section_header("Système", "⚙️")
    c1,c2,c3 = st.columns(3)
    with c1:
        st.markdown("#### 💾 Sauvegarde")
        if st.button("📦 Sauvegarder", key="bk", type="primary"):
            p = backup_all(); log_action("BACKUP","SYSTEM","backup",actor=user); st.success("✅ Sauvegarde créée")
        st.markdown("#### 📈 Archive mensuelle")
        if st.button("📈 Archiver les revenus du mois", key="archive_rev"):
            try:
                from core.financial_engine import archive_monthly_revenue
                result = archive_monthly_revenue(user)
                log_action("REVENUE_ARCHIVED","SYSTEM","revenue",actor=user)
                st.success(f"✅ Archive créée: {result.get('period','')}")
            except Exception as e:
                st.error(f"❌ {e}")
    with c2:
        st.markdown("#### 📊 Stats")
        s = get_platform_stats()
        st.write(f"👥 {s['total_users']} utilisateurs · 🔬 {s['total_members']} analystes")
        st.write(f"📋 {s['total_requests']} actives · 📦 {s['total_archived']} archives")
        st.write(f"🧾 {s['total_invoices']} factures")
    with c3:
        st.markdown("#### 🔧 Config")
        st.write(f"Budget: {fmt_currency(config.IBTIKAR_BUDGET_CAP)}")
        st.write(f"TVA: {config.VAT_RATE*100:.0f}% · SLA: {config.SLA_DAYS_IBTIKAR}j/{config.SLA_DAYS_GENOCLAB}j")
        st.write(f"Version: {config.PLATFORM_VERSION}")
