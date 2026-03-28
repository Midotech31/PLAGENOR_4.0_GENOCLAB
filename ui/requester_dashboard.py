# ui/requester_dashboard.py — PLAGENOR 4.0 Requester Dashboard
# Multi-step IBTIKAR form driven by YAML service registry
from __future__ import annotations
import streamlit as st, uuid, os
from datetime import datetime, timezone
import config
from ui.styles import get_global_css
from ui.shared_components import (
    render_sidebar_user, render_kpi_card, render_request_card,
    render_empty_state, render_workflow_progress, fmt_date, fmt_currency,
    section_header, get_status_badge_html, resolve_username,
    render_star_rating_html,
)
from core.repository import (
    get_all_active_requests, get_all_archived_requests,
    save_request, get_requests_by_user, generate_request_id,
)
from core.audit_engine import log_action
from services.registry_loader import load_service_registry, get_service_def, get_requester_fields
from services.form_renderer import render_requester_form, render_service_params, render_sample_table, validate_required_fields
from services.pricing_engine import calculate_price, format_price
from services.notification_service import get_user_notifications, get_unread_count
from core.logger import get_logger
from utils.i18n import t

_log = get_logger("requester_dashboard")

def render_requester_dashboard(user):
    try:
        _render_requester_dashboard_inner(user)
    except Exception as e:
        _log.exception("Erreur dans le tableau Demandeur")
        st.error(f"❌ Une erreur inattendue s'est produite dans le tableau Demandeur. Veuillez réessayer ou contacter l'administrateur.\n\nDétail: {e}")

def _render_requester_dashboard_inner(user):
    st.session_state["user"] = user
    st.session_state["authenticated"] = True
    st.markdown(get_global_css(), unsafe_allow_html=True)
    render_sidebar_user(user)
    unread = get_unread_count(user.get("id",""))
    badge = f" · 🔔 {unread}" if unread else ""
    st.markdown(f'<div style="margin-bottom:24px"><h2 style="color:#1B2838;margin:0">📋 {t("welcome_requester")}</h2><p style="color:#7F8C9B;margin:4px 0 0">{t("requests")}{badge}</p></div>', unsafe_allow_html=True)

    my = get_requests_by_user(user.get("id",""))
    active = [r for r in my if r.get("status") not in ("REJECTED","CLOSED","COMPLETED")]
    completed = [r for r in my if r.get("status") in ("COMPLETED","CLOSED")]
    rejected = [r for r in my if r.get("status") == "REJECTED"]
    c1,c2,c3,c4 = st.columns(4)
    with c1: render_kpi_card("📋", len(my), t("requests"), "blue")
    with c2: render_kpi_card("🔄", len(active), t("in_progress"), "orange")
    with c3: render_kpi_card("✅", len(completed), t("completed"), "green")
    with c4: render_kpi_card("❌", len(rejected), "❌", "red")
    st.markdown("<br/>", unsafe_allow_html=True)

    tabs = st.tabs([f"➕ {t('new_request')}", f"📋 {t('my_requests')}", f"📦 {t('archives')}", f"🔔 {t('notifications')}"])

    with tabs[0]:
        _new_request_form(user)

    with tabs[1]:
        _my_requests(user, active)

    with tabs[2]:
        archived = completed + rejected
        archived += [r for r in get_all_archived_requests() if r.get("requester_id")==user.get("id")]
        if not archived: render_empty_state("📦","Aucune archive")
        else:
            for r in archived[:20]: render_request_card(r)

    with tabs[3]:
        notifs = get_user_notifications(user.get("id",""))
        if not notifs: render_empty_state("🔔","Aucune notification")
        else:
            for n in notifs[:30]:
                op = "opacity:0.5" if n.get("read") else ""
                st.markdown(f'<div style="padding:8px 12px;border-left:3px solid #1B4F72;margin-bottom:6px;font-size:13px;{op}">{n.get("message","")} <span style="color:#ABB2B9;margin-left:8px">{fmt_date(n.get("created_at",""))}</span></div>', unsafe_allow_html=True)

def _new_request_form(user):
    section_header("Soumettre une demande IBTIKAR", "➕")

    registry = load_service_registry()
    if not registry:
        st.warning("Aucun service disponible dans le registre."); return

    codes = sorted(registry.keys())
    labels = {code: f"{code} — {registry[code].get('service_name','')}" for code in codes}

    # Step 1: Select service
    st.markdown("#### Étape 1 — Choisir le service")
    sel_label = st.selectbox("Service demandé *", ["— Sélectionner —"] + [labels[c] for c in codes], key="ibk_svc_sel")
    if sel_label == "— Sélectionner —":
        st.info("Sélectionnez un service pour continuer."); return

    sel_code = next((c for c in codes if labels[c] == sel_label), None)
    if not sel_code: return
    svc_def = registry[sel_code]

    if svc_def.get("description"):
        st.info(svc_def["description"])

    st.markdown("---")

    # Step 2: Requester info
    st.markdown("#### Étape 2 — Informations du demandeur")
    req_fields = get_requester_fields(sel_code)
    with st.form("ibk_requester_form"):
        requester_data = {}
        c1, c2 = st.columns(2)
        for i, f in enumerate(req_fields):
            with c1 if i % 2 == 0 else c2:
                val = st.text_input(f"{f['label']}{' *' if f.get('required') else ''}", key=f"ibk_r_{f['name']}")
                requester_data[f["name"]] = val.strip()

        st.markdown("---")
        st.markdown("#### Étape 3 — Paramètres du service")
        svc_params = render_service_params(svc_def, prefix="ibk_p")

        save_step2 = st.form_submit_button("Continuer →", use_container_width=True, type="primary")

    if save_step2:
        # Validate requester
        missing_req = [f["label"] for f in req_fields if f.get("required") and not requester_data.get(f["name"])]
        # Validate service params
        missing_svc = validate_required_fields(svc_params, svc_def)
        all_errors = [f"Champ demandeur: {m}" for m in missing_req] + missing_svc
        if all_errors:
            for e in all_errors: st.error(e)
        else:
            st.session_state["ibk_requester"] = requester_data
            st.session_state["ibk_svc_code"] = sel_code
            st.session_state["ibk_svc_params"] = svc_params
            st.success("Paramètres enregistrés. Ajoutez vos échantillons ci-dessous.")

    # Step 3: Sample table (only if step 2 is done)
    if st.session_state.get("ibk_svc_code") == sel_code and st.session_state.get("ibk_requester"):
        st.markdown("---")
        st.markdown("#### Étape 4 — Échantillons")
        samples = render_sample_table(svc_def)

        if samples:
            st.markdown("---")
            st.markdown("#### Étape 5 — Estimation budgétaire")
            try:
                pricing = calculate_price(svc_def, st.session_state.get("ibk_svc_params",{}), samples)
                c1,c2,c3 = st.columns(3)
                with c1: st.metric("Échantillons", pricing["number_of_units"])
                with c2: st.metric("Prix unitaire", format_price(pricing["unit_price"]))
                with c3: st.metric("Total estimé", format_price(pricing["total"]))

                # IBTIKAR balance declaration
                st.markdown("---")
                st.markdown("#### Déclaration de solde IBTIKAR")
                declared_balance = st.number_input(
                    "Solde IBTIKAR déclaré (DZD)", value=200000.0, min_value=0.0,
                    step=1000.0, key="ibk_balance"
                )
                st.info("ℹ️ Déclarez votre solde IBTIKAR actuel. Le système vérifiera que le coût ne dépasse pas votre solde.")
                if pricing["total"] > declared_balance:
                    st.warning(f"⚠️ Le coût estimé ({format_price(pricing['total'])}) dépasse votre solde déclaré ({format_price(declared_balance)}).")

                # Urgency selection
                st.markdown("---")
                st.markdown("#### Étape 6 — Urgence et soumission")
                ibk_urgency = st.selectbox("Niveau d'urgence", config.URGENCY_LEVELS, key="ibk_urgency")

                project_title = st.session_state.get("ibk_svc_params",{}).get("project_title","")
                if st.button("📤 Soumettre la demande IBTIKAR", use_container_width=True, type="primary", key="ibk_submit"):
                    try:
                        from core.services.ibtikar_service import submit_ibtikar_request
                        display_id = generate_request_id(config.CHANNEL_IBTIKAR)
                        req_data = {
                            "title": f"{sel_code} — {project_title or svc_def.get('service_name','')}",
                            "description": svc_def.get("description",""),
                            "service_code": sel_code,
                            "service_id": sel_code,
                            "display_id": display_id,
                            "urgency": ibk_urgency,
                            "declared_ibtikar_balance": declared_balance,
                            "requester": st.session_state["ibk_requester"],
                            "service_params": st.session_state["ibk_svc_params"],
                            "sample_table": [s for s in samples if s.get("_id")],
                            "pricing": pricing,
                            "budget_amount": pricing["total"],
                            "sample_count": pricing["number_of_units"],
                        }
                        saved = submit_ibtikar_request(req_data, user)

                        # Clear form state
                        for k in list(st.session_state.keys()):
                            if k.startswith("ibk_") or k.startswith("samples_"):
                                del st.session_state[k]
                        st.success(f"✅ Demande IBTIKAR soumise! Réf: {display_id}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ {e}")
            except Exception as e:
                st.error(f"Erreur de calcul: {e}")

def _my_requests(user, active):
    section_header(f"Demandes en cours ({len(active)})", "📋")
    if not active: render_empty_state("📭","Aucune demande en cours"); return
    for req in sorted(active, key=lambda x: x.get("created_at",""), reverse=True):
        render_request_card(req)
        with st.expander(f"📊 Suivi — {req.get('title','')[:50]}"):
            render_workflow_progress(req)
            c1,c2 = st.columns(2)
            with c1:
                st.markdown(f"**Statut:** {get_status_badge_html(req.get('status',''))}", unsafe_allow_html=True)
                if req.get("budget_amount"): st.write(f"**Budget:** {fmt_currency(req['budget_amount'])}")
                if req.get("service_code"): st.write(f"**Service:** {req['service_code']}")
            with c2:
                st.write(f"**Créée:** {fmt_date(req.get('created_at',''))}")
                if req.get("assigned_to"): st.write(f"**Analyste:** {resolve_username(req['assigned_to'])}")
            if req.get("rejection_reason"):
                st.error(f"Raison du rejet: {req['rejection_reason']}")
            # Receipt confirmation
            if req.get("status") in ("REPORT_VALIDATED", "COMPLETED") and not req.get("receipt_confirmed"):
                if st.button(f"✅ Confirmer la réception du rapport", key=f"confirm_receipt_{req['id']}"):
                    req["receipt_confirmed"] = True
                    req["receipt_confirmed_at"] = datetime.now(timezone.utc).isoformat()
                    req["receipt_confirmed_by"] = user.get("id", "")
                    save_request(req)
                    try:
                        from core.repository import save_audit_log
                        save_audit_log({
                            "action": "RECEIPT_CONFIRMED",
                            "request_id": req["id"],
                            "user_id": user.get("id"),
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        })
                    except Exception:
                        pass
                    st.success("✅ Réception confirmée. Merci !")
                    st.rerun()
            # Star rating (after receipt confirmed)
            if req.get("receipt_confirmed") and not req.get("service_rating"):
                st.markdown("##### ⭐ Évaluez le service")
                rating_cols = st.columns(5)
                for i in range(1, 6):
                    with rating_cols[i - 1]:
                        if st.button("⭐" * i, key=f"rate_{req['id']}_{i}"):
                            req["service_rating"] = i
                            req["rated_at"] = datetime.now(timezone.utc).isoformat()
                            save_request(req)
                            log_action("SERVICE_RATED", "REQUEST", req["id"], actor=user,
                                      details={"rating": i})
                            st.success(f"Merci ! Évaluation: {'⭐' * i}")
                            st.rerun()
                rating_comment = st.text_input("Commentaire (optionnel)", key=f"rc_{req['id']}")
                if rating_comment:
                    st.session_state[f"pending_comment_{req['id']}"] = rating_comment
            elif req.get("service_rating"):
                st.markdown(f"**Votre évaluation:** {render_star_rating_html(req['service_rating'])}", unsafe_allow_html=True)
                if req.get("rating_comment"):
                    st.markdown(f"*{req['rating_comment']}*")
            # Download IBTIKAR form if available
            form_path = req.get("ibtikar_form_path","")
            if form_path and os.path.exists(form_path):
                with open(form_path, "rb") as f:
                    st.download_button("📄 Télécharger le formulaire IBTIKAR (DOCX)", f.read(), file_name=os.path.basename(form_path), mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key=f"dl_{req['id']}")
            hist = req.get("history",[])
            if hist and st.checkbox(f"📜 Historique ({len(hist)})", key=f"rh_{req['id']}"):
                for h in reversed(hist):
                    st.markdown(f"<div style='font-size:12px;padding:2px 0'><strong>{h.get('from','—')}</strong> → <strong>{h.get('to','')}</strong> · {h.get('by','')} · {fmt_date(h.get('at',''))}</div>", unsafe_allow_html=True)
