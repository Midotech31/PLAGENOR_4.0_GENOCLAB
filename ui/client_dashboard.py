# ui/client_dashboard.py — PLAGENOR 4.0 Client Dashboard (GENOCLAB)
from __future__ import annotations
import streamlit as st, uuid
from datetime import datetime, timezone
import config
from ui.styles import get_global_css
from ui.shared_components import (
    render_sidebar_user, render_kpi_card, render_request_card,
    render_empty_state, render_workflow_progress, fmt_date, fmt_currency,
    section_header, get_status_badge_html, render_star_rating_html,
)
from core.repository import (
    get_all_active_requests, get_all_archived_requests,
    save_request, get_services_for_channel, get_requests_by_user, get_all_invoices,
    generate_request_id,
)
from core.workflow_engine import transition, get_allowed_transitions
from core.audit_engine import log_action
from services.registry_loader import load_service_registry, get_service_def, get_requester_fields
from services.form_renderer import render_service_params, render_sample_table
from services.pricing_engine import calculate_price, format_price
from services.notification_service import get_user_notifications, get_unread_count
from core.logger import get_logger
from utils.i18n import t

_log = get_logger("client_dashboard")

def render_client_dashboard(user):
    try:
        _render_client_dashboard_inner(user)
    except Exception as e:
        _log.exception("Erreur dans le tableau Client")
        st.error(f"❌ Une erreur inattendue s'est produite dans le tableau Client. Veuillez réessayer ou contacter l'administrateur.\n\nDétail: {e}")

def _render_client_dashboard_inner(user):
    st.session_state["user"] = user
    st.session_state["authenticated"] = True
    st.markdown(get_global_css(), unsafe_allow_html=True)
    render_sidebar_user(user)
    unread = get_unread_count(user.get("id",""))
    badge = f" · 🔔 {unread}" if unread else ""
    st.markdown(f'<div style="margin-bottom:24px"><h2 style="color:#1B2838;margin:0">🏢 {t("welcome_client")}</h2><p style="color:#7F8C9B;margin:4px 0 0">{t("requests")}{badge}</p></div>', unsafe_allow_html=True)

    my = get_requests_by_user(user.get("id",""))
    geno = [r for r in my if r.get("channel")==config.CHANNEL_GENOCLAB]
    active = [r for r in geno if r.get("status") not in ("REJECTED","COMPLETED","ARCHIVED","QUOTE_REJECTED_BY_CLIENT")]
    completed = [r for r in geno if r.get("status") in ("COMPLETED","ARCHIVED")]
    invoices = [i for i in get_all_invoices() if i.get("client_id")==user.get("id")]
    pending_quotes = [r for r in active if r.get("status")=="QUOTE_SENT"]

    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: render_kpi_card("📋", len(geno), t("requests"), "teal")
    with c2: render_kpi_card("🔄", len(active), t("in_progress"), "orange")
    with c3: render_kpi_card("✅", len(completed), t("completed"), "green")
    with c4: render_kpi_card("🧾", len(invoices), t("invoices"), "purple")
    with c5: render_kpi_card("📧", len(pending_quotes), t("pending"), "red" if pending_quotes else "blue")
    st.markdown("<br/>", unsafe_allow_html=True)

    if pending_quotes:
        st.markdown(f'<div style="background:#FEF9E7;border:1px solid #F9E79F;border-radius:12px;padding:16px;margin-bottom:16px"><strong>⚠️ {len(pending_quotes)} devis en attente</strong> — Validez ou refusez dans l\'onglet "Mes demandes".</div>', unsafe_allow_html=True)

    tabs = st.tabs([f"➕ {t('new_request')}",f"📋 {t('my_requests')}",f"🧾 {t('invoices')}",f"📦 {t('archives')}",f"🔔 {t('notifications')}"])

    with tabs[0]:
        section_header("Soumettre une demande d'analyse", "➕")
        registry = load_service_registry()
        if not registry: st.warning("Aucun service."); return
        codes = sorted(registry.keys())
        labels = {c: f"{c} — {registry[c].get('service_name','')}" for c in codes}
        sel = st.selectbox("Service *", ["— Sélectionner —"]+[labels[c] for c in codes], key="cl_svc")
        if sel == "— Sélectionner —": st.info("Sélectionnez un service."); return
        sel_code = next((c for c in codes if labels[c]==sel), None)
        if not sel_code: return
        svc_def = registry[sel_code]
        if svc_def.get("description"): st.info(svc_def["description"])
        with st.form("cl_req_form"):
            st.markdown("#### Informations")
            c1,c2 = st.columns(2)
            with c1:
                cl_org = st.text_input("Organisation *", help="Nom de votre entreprise, laboratoire ou institution")
                cl_contact = st.text_input("Contact (email/tél) *", help="Entrez une adresse email valide (ex: nom@universite.dz) ou un numéro de téléphone")
            with c2:
                cl_urgency = st.selectbox("Urgence", ["Normal","Urgent","Très urgent"])
                cl_desc = st.text_area("Description *", height=80, help="Décrivez brièvement l'objectif de votre demande d'analyse")
            st.markdown("#### Paramètres du service")
            svc_params = render_service_params(svc_def, prefix="cl_p")
            if st.form_submit_button("Continuer →", use_container_width=True, type="primary"):
                _valid = True
                if not cl_org.strip() or not cl_contact.strip() or not cl_desc.strip():
                    st.warning("Champs * obligatoires.")
                    _valid = False
                elif "@" in cl_contact.strip():
                    from utils.validation import is_valid_email
                    if not is_valid_email(cl_contact.strip()):
                        st.error("Adresse email invalide. Vérifiez le format.")
                        _valid = False
                if _valid:
                    st.session_state["cl_ready"] = True
                    st.session_state["cl_svc_code"] = sel_code
                    st.session_state["cl_params"] = svc_params
                    st.session_state["cl_meta"] = {"org": cl_org, "contact": cl_contact, "urgency": cl_urgency, "desc": cl_desc}
                    st.success("Paramètres enregistrés. Ajoutez vos échantillons.")

        if st.session_state.get("cl_svc_code")==sel_code and st.session_state.get("cl_ready"):
            st.markdown("#### Échantillons")
            samples = render_sample_table(svc_def)
            if samples:
                try:
                    pricing = calculate_price(svc_def, st.session_state.get("cl_params",{}), samples)
                    c1,c2,c3 = st.columns(3)
                    with c1: st.metric("Échantillons", pricing["number_of_units"])
                    with c2: st.metric("Prix unitaire", format_price(pricing["unit_price"]))
                    with c3: st.metric("Total estimé", format_price(pricing["total"]))
                    if st.button("📤 Soumettre", use_container_width=True, type="primary", key="cl_submit"):
                        try:
                            from core.services.genoclab_service import submit_genoclab_request
                            meta = st.session_state.get("cl_meta",{})
                            display_id = generate_request_id(config.CHANNEL_GENOCLAB)
                            req_data = {
                                "title": f"{sel_code} — {meta.get('org','')}",
                                "description": meta.get("desc",""),
                                "service_code": sel_code,
                                "service_id": sel_code,
                                "display_id": display_id,
                                "organization": meta.get("org",""),
                                "contact": meta.get("contact",""),
                                "urgency": meta.get("urgency","Normal"),
                                "service_params": st.session_state.get("cl_params",{}),
                                "sample_table": samples,
                                "pricing": pricing,
                            }
                            saved = submit_genoclab_request(req_data, user)
                            for k in list(st.session_state.keys()):
                                if k.startswith("cl_") or k.startswith("samples_"): del st.session_state[k]
                            st.success(f"✅ Demande soumise! Réf: {display_id}"); st.rerun()
                        except Exception as e: st.error(f"❌ {e}")
                except Exception as e: st.error(str(e))

    with tabs[1]:
        if not active: render_empty_state("📭","Aucune demande en cours")
        else:
            for req in sorted(active, key=lambda x: x.get("created_at",""), reverse=True):
                render_request_card(req)
                with st.expander(f"📊 {req.get('title','')[:50]}"):
                    render_workflow_progress(req)
                    if req.get("status")=="QUOTE_SENT":
                        amt = req.get("quote_amount",0)
                        if amt: st.markdown(f'<div style="text-align:center;font-size:24px;font-weight:700;color:#1B4F72;margin:12px 0">{fmt_currency(amt)}</div>', unsafe_allow_html=True)
                        c1,c2 = st.columns(2)
                        with c1:
                            if st.button("✅ Accepter", key=f"ca_{req['id']}", type="primary", use_container_width=True):
                                try: transition(req["id"],"QUOTE_VALIDATED_BY_CLIENT",user); st.success("Accepté!"); st.rerun()
                                except Exception as e: st.error(str(e))
                        with c2:
                            if st.button("❌ Refuser", key=f"cr_{req['id']}", use_container_width=True):
                                try: transition(req["id"],"QUOTE_REJECTED_BY_CLIENT",user,rejection_reason="Refusé par le client"); st.rerun()
                                except Exception as e: st.error(str(e))
                    # Receipt confirmation
                    if req.get("status") in ("REPORT_VALIDATED", "COMPLETED") and not req.get("receipt_confirmed"):
                        if st.button(f"✅ Confirmer la réception du rapport", key=f"confirm_receipt_{req['id']}"):
                            req["receipt_confirmed"] = True
                            req["receipt_confirmed_at"] = datetime.now(timezone.utc).isoformat()
                            req["receipt_confirmed_by"] = user.get("id", "")
                            from core.repository import save_audit_log
                            save_request(req)
                            try:
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
                                if st.button("⭐" * i, key=f"cl_rate_{req['id']}_{i}"):
                                    req["service_rating"] = i
                                    req["rated_at"] = datetime.now(timezone.utc).isoformat()
                                    save_request(req)
                                    log_action("SERVICE_RATED", "REQUEST", req["id"], actor=user,
                                              details={"rating": i})
                                    st.success(f"Merci ! Évaluation: {'⭐' * i}")
                                    st.rerun()
                        rating_comment = st.text_input("Commentaire (optionnel)", key=f"cl_rc_{req['id']}")
                        if rating_comment:
                            st.session_state[f"cl_pending_comment_{req['id']}"] = rating_comment
                    elif req.get("service_rating"):
                        st.markdown(f"**Votre évaluation:** {render_star_rating_html(req['service_rating'])}", unsafe_allow_html=True)

    with tabs[2]:
        if not invoices: render_empty_state("🧾","Aucune facture")
        else:
            for inv in sorted(invoices, key=lambda x: x.get("created_at",""), reverse=True):
                st.markdown(f"**{inv.get('invoice_number','')}** · {fmt_date(inv.get('created_at',''))} · **{fmt_currency(inv.get('total_ttc',0))}** {'🔒' if inv.get('locked') else ''}")
                st.markdown("---")

    with tabs[3]:
        arch = completed + [r for r in get_all_archived_requests() if r.get("client_id")==user.get("id")]
        if not arch: render_empty_state("📦","Aucune archive")
        else:
            for r in arch[:20]: render_request_card(r)

    with tabs[4]:
        notifs = get_user_notifications(user.get("id",""))
        if not notifs: render_empty_state("🔔","Aucune notification")
        else:
            for n in notifs[:30]:
                st.markdown(f'<div style="padding:8px 12px;border-left:3px solid #117A65;margin-bottom:6px;font-size:13px">{n.get("message","")} · {fmt_date(n.get("created_at",""))}</div>', unsafe_allow_html=True)
