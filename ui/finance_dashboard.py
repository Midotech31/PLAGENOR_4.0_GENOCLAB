# ui/finance_dashboard.py — PLAGENOR 4.0 Finance Dashboard
# Budget enforcement via ibtikar_service.validate_finance()
from __future__ import annotations
import streamlit as st
from datetime import datetime
import config
from ui.styles import get_global_css
from ui.shared_components import (
    render_sidebar_user, render_kpi_card, render_empty_state,
    render_progress_bar, fmt_date, fmt_datetime, fmt_currency,
    section_header, get_channel_badge_html, get_status_badge_html,
    render_request_card, render_workflow_progress,
    render_export_button,
)
from core.repository import get_all_active_requests, get_all_invoices, get_all_archived_requests, get_revenue_archives
from core.financial_engine import get_budget_dashboard
from core.budget_engine import get_budget_status
from core.workflow_engine import transition, get_allowed_transitions
from core.audit_engine import safe_get_all_audit_logs
from services.pricing_engine import format_price
from core.logger import get_logger
from utils.i18n import t

_log = get_logger("finance_dashboard")

def render_finance_dashboard(user):
    try:
        _render_finance_dashboard_inner(user)
    except Exception as e:
        _log.exception("Erreur dans le tableau Financier")
        st.error(f"❌ Une erreur inattendue s'est produite dans le tableau Financier. Veuillez réessayer ou contacter l'administrateur.\n\nDétail: {e}")

def _render_finance_dashboard_inner(user):
    st.session_state["user"] = user
    st.session_state["authenticated"] = True
    st.markdown(get_global_css(), unsafe_allow_html=True)
    render_sidebar_user(user)
    st.markdown(f'<div style="margin-bottom:24px"><h2 style="color:#1B2838;margin:0">💰 {t("welcome_finance")}</h2><p style="color:#7F8C9B;margin:4px 0 0">{t("validation")} IBTIKAR · {t("invoices")} GENOCLAB</p></div>', unsafe_allow_html=True)

    budget = get_budget_dashboard()
    invoices = get_all_invoices()
    ibk = budget.get("ibtikar", {})
    gcl = budget.get("genoclab", {})
    c1,c2,c3,c4 = st.columns(4)
    with c1: render_kpi_card("flask", fmt_currency(ibk.get('total',0)), f"IBTIKAR {t('revenue_virtual')}", "orange")
    with c2: render_kpi_card("dna", fmt_currency(gcl.get('total',0)), f"GENOCLAB {t('revenue_real')}", "green")
    with c3: render_kpi_card("invoice", str(gcl.get('count',0)), t("invoices"), "teal")
    with c4: render_kpi_card("award", str(ibk.get('students',0)), t("students"), "purple")
    st.markdown("<br/>", unsafe_allow_html=True)

    tabs = st.tabs([f"🏦 {t('validation')} IBTIKAR", f"📊 {t('budget')}", f"🧾 {t('invoices')} GENOCLAB", f"📈 {t('archives')}", f"📜 {t('audit')}"])

    # ── TAB 1: IBTIKAR BUDGET VALIDATION ──────────────────────────────────
    with tabs[0]:
        _ibtikar_validation(user)

    # ── TAB 2: BUDGET OVERVIEW ────────────────────────────────────────────
    with tabs[1]:
        _budget_overview()

    # ── TAB 3: GENOCLAB INVOICES ──────────────────────────────────────────
    with tabs[2]:
        _genoclab_invoices(user)

    # ── TAB 4: REVENUE ARCHIVES ───────────────────────────────────────────
    with tabs[3]:
        _revenue_archives()

    # ── TAB 5: FINANCIAL HISTORY ──────────────────────────────────────────
    with tabs[4]:
        _financial_history()


def _ibtikar_validation(user):
    section_header("Demandes IBTIKAR en attente de validation financière", "dollar")

    requests = get_all_active_requests()
    pending_finance = [r for r in requests
                       if r.get("channel") == config.CHANNEL_IBTIKAR
                       and r.get("status") == "VALIDATION_PEDAGOGIQUE"]

    if not pending_finance:
        render_empty_state("check_circle", "Aucune demande en attente de validation financière")
        return

    for req in pending_finance:
        render_request_card(req)
        with st.expander(f"🏦 Valider — {req.get('title','')[:50]}"):
            render_workflow_progress(req)

            # Show request details
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"**Demandeur:** {req.get('requester_name', '')}")
                st.write(f"**Service:** {req.get('service_code', '')}")
                st.write(f"**Échantillons:** {req.get('sample_count', '—')}")
            with c2:
                pricing = req.get("pricing", {})
                budget_amt = req.get("budget_amount", 0)
                st.write(f"**Montant demandé:** {fmt_currency(budget_amt)}")
                if pricing:
                    st.write(f"**Modèle tarif:** {pricing.get('pricing_model','—')}")
                    st.write(f"**Prix unitaire:** {format_price(pricing.get('unit_price',0))}")

            # Show requester's current budget usage
            requester_id = req.get("requester_id", "")
            if requester_id:
                req_budget = get_budget_status(requester_id=requester_id)
                st.markdown("---")
                st.markdown(f"**Budget du demandeur ({req.get('requester_name','')}):**")
                render_progress_bar(req_budget["used"], req_budget["cap"], "blue",
                                   f"Consommé: {fmt_currency(req_budget['used'])} / {fmt_currency(req_budget['cap'])}")
                projected = req_budget["used"] + budget_amt
                if projected > req_budget["cap"]:
                    st.warning(f"⚠️ Ce montant dépasserait le plafond du demandeur: "
                              f"{fmt_currency(projected)} > {fmt_currency(req_budget['cap'])}")

            st.markdown("---")

            # Approval / Rejection
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Approuver le budget", key=f"fin_approve_{req['id']}", type="primary",
                            use_container_width=True):
                    try:
                        from core.services.ibtikar_service import validate_finance
                        result = validate_finance(req["id"], user, approved=True)
                        st.success(f"✅ Budget validé — Note de plateforme générée")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ {e}")
                        # Check if it's a budget override situation
                        if "dépassé" in str(e).lower() and user.get("role") == config.ROLE_SUPER_ADMIN:
                            justification = st.text_area("Justification de l'override",
                                                         key=f"fin_just_{req['id']}")
                            if justification and st.button("⚡ Override SA",
                                                           key=f"fin_override_{req['id']}"):
                                try:
                                    result = validate_finance(req["id"], user, approved=True,
                                                            override_justification=justification)
                                    st.success("✅ Override approuvé")
                                    st.rerun()
                                except Exception as e2:
                                    st.error(str(e2))

            with c2:
                reject_reason = st.text_input("Raison du rejet", key=f"fin_reject_r_{req['id']}")
                if st.button("❌ Rejeter", key=f"fin_reject_{req['id']}",
                            use_container_width=True):
                    if not reject_reason:
                        st.warning("Raison de rejet obligatoire")
                    else:
                        try:
                            from core.services.ibtikar_service import validate_finance
                            validate_finance(req["id"], user, approved=False, reason=reject_reason)
                            st.success("Demande rejetée")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

    # Also show GENOCLAB payment confirmations
    st.markdown("---")
    section_header("Paiements GENOCLAB en attente", "credit_card")
    pending_payment = [r for r in requests
                       if r.get("channel") == config.CHANNEL_GENOCLAB
                       and r.get("status") == "INVOICE_GENERATED"]
    if not pending_payment:
        render_empty_state("check_circle", "Aucun paiement en attente")
    else:
        for req in pending_payment:
            render_request_card(req)
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(f"**Facture:** {fmt_currency(req.get('quote_amount', 0))}")
            with c2:
                if st.button("💳 Confirmer paiement", key=f"fin_pay_{req['id']}",
                            type="primary"):
                    try:
                        transition(req["id"], "PAYMENT_CONFIRMED", user)
                        st.success("✅ Paiement confirmé")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))


def _budget_overview():
    section_header("Vue d'ensemble budgétaire", "bar_chart")
    budget = get_budget_dashboard()
    ibk = budget.get("ibtikar", {})
    gcl = budget.get("genoclab", {})

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### 🏛 IBTIKAR — Revenus virtuels")
        st.markdown(f"""
        <div style="display:flex;gap:28px;margin:12px 0">
            <div><span style="font-size:13px;color:#64748B">Total virtuel</span><br/><strong style="font-size:22px;color:#D97706">{fmt_currency(ibk.get('total',0))}</strong></div>
            <div><span style="font-size:13px;color:#64748B">Demandes</span><br/><strong style="font-size:22px">{ibk.get('count',0)}</strong></div>
            <div><span style="font-size:13px;color:#64748B">Étudiants</span><br/><strong style="font-size:22px">{ibk.get('students',0)}</strong></div>
            <div><span style="font-size:13px;color:#64748B">Budget/étudiant</span><br/><strong style="font-size:22px">{fmt_currency(ibk.get('budget_per_student',200000))}</strong></div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("##### 🧬 GENOCLAB — Revenus réels")
        st.markdown(f"""
        <div style="display:flex;gap:28px;margin:12px 0">
            <div><span style="font-size:13px;color:#64748B">Chiffre d'affaires</span><br/><strong style="font-size:22px;color:#059669">{fmt_currency(gcl.get('total',0))}</strong></div>
            <div><span style="font-size:13px;color:#64748B">Factures</span><br/><strong style="font-size:22px">{gcl.get('count',0)}</strong></div>
        </div>""", unsafe_allow_html=True)

    # IBTIKAR requests with budget
    ibtikar = [r for r in get_all_active_requests()
               if r.get("channel") == config.CHANNEL_IBTIKAR and r.get("budget_amount", 0) > 0]
    if ibtikar:
        st.markdown(f"**{len(ibtikar)} demande(s) IBTIKAR avec budget alloué**")
        for req in ibtikar:
            c1,c2,c3 = st.columns([4,2,2])
            with c1: st.write(f"**{req.get('title','')[:50]}** — {req.get('requester_name','')}")
            with c2: st.markdown(get_status_badge_html(req.get("status","")), unsafe_allow_html=True)
            with c3: st.write(fmt_currency(req.get("budget_amount",0)))
            st.markdown("<div style='border-bottom:1px solid #f0f2f6'></div>", unsafe_allow_html=True)

    # Override history
    from core.budget_engine import get_override_logs
    overrides = get_override_logs()
    if overrides:
        st.markdown("---")
        section_header(f"Dépassements autorisés ({len(overrides)})", "alert")
        for o in overrides:
            st.markdown(f'<div style="padding:8px;border-left:3px solid #E74C3C;margin-bottom:6px;background:#FEF9E7;border-radius:4px;font-size:13px">⚠️ <strong>{fmt_currency(o.get("amount",0))}</strong> par {o.get("actor_username","")} — {fmt_datetime(o.get("timestamp",""))}<br/><span style="color:#7F8C9B">{o.get("justification","")}</span></div>', unsafe_allow_html=True)


def _genoclab_invoices(user):
    section_header("Factures GENOCLAB", "invoice")
    invoices = get_all_invoices()
    if not invoices:
        render_empty_state("invoice", "Aucune facture")
        return

    total_ht = sum(i.get("subtotal_ht",0) for i in invoices)
    total_tva = sum(i.get("vat_amount",0) for i in invoices)
    total_ttc = sum(i.get("total_ttc",0) for i in invoices)
    st.markdown(f'<div style="display:flex;gap:32px;margin-bottom:16px"><div><span style="font-size:12px;color:#7F8C9B">Total HT</span><br/><strong>{fmt_currency(total_ht)}</strong></div><div><span style="font-size:12px;color:#7F8C9B">TVA</span><br/><strong>{fmt_currency(total_tva)}</strong></div><div><span style="font-size:12px;color:#7F8C9B">Total TTC</span><br/><strong style="color:#117A65;font-size:20px">{fmt_currency(total_ttc)}</strong></div></div>', unsafe_allow_html=True)
    render_export_button(invoices, filename="factures_genoclab.csv", columns=["invoice_number","created_at","client_name","subtotal_ht","vat_amount","total_ttc","locked"])

    for inv in sorted(invoices, key=lambda x: x.get("created_at",""), reverse=True):
        c1,c2,c3,c4 = st.columns([3,2,2,1])
        with c1: st.markdown(f"**{inv.get('invoice_number','')}**")
        with c2: st.write(fmt_date(inv.get("created_at","")))
        with c3: st.write(f"**{fmt_currency(inv.get('total_ttc',0))}**")
        with c4: st.write("🔒" if inv.get("locked") else "🔓")
        st.markdown("<div style='border-bottom:1px solid #f0f2f6'></div>", unsafe_allow_html=True)


def _revenue_archives():
    section_header("Archives mensuelles des revenus", "trending_up")
    archives = get_revenue_archives()
    if not archives:
        render_empty_state("trending_up", "Aucune archive mensuelle. L'archivage est déclenché depuis l'espace Super Admin.")
        return
    for arch in sorted(archives, key=lambda x: x.get("month", ""), reverse=True):
        month = arch.get("month", "")
        st.markdown(f"""
        <div class="data-card" style="margin-bottom:12px">
            <div style="display:flex;justify-content:space-between;align-items:center">
                <h4 style="margin:0;color:#1B2838">📅 {month}</h4>
                <span style="color:#7F8C9B;font-size:12px">Archivé le {fmt_datetime(arch.get("archived_at",""))}</span>
            </div>
            <div style="display:flex;gap:32px;margin-top:12px">
                <div><span style="font-size:12px;color:#7F8C9B">GENOCLAB TTC</span><br/><strong style="color:#117A65">{fmt_currency(arch.get("genoclab_total_ttc",0))}</strong></div>
                <div><span style="font-size:12px;color:#7F8C9B">GENOCLAB HT</span><br/><strong>{fmt_currency(arch.get("genoclab_total_ht",0))}</strong></div>
                <div><span style="font-size:12px;color:#7F8C9B">TVA</span><br/><strong>{fmt_currency(arch.get("genoclab_total_vat",0))}</strong></div>
                <div><span style="font-size:12px;color:#7F8C9B">Factures</span><br/><strong>{arch.get("genoclab_invoices_count",0)}</strong></div>
                <div><span style="font-size:12px;color:#7F8C9B">Budget IBTIKAR</span><br/><strong>{fmt_currency(arch.get("ibtikar_budget_used",0))} / {fmt_currency(arch.get("ibtikar_budget_cap",0))}</strong></div>
            </div>
        </div>""", unsafe_allow_html=True)


def _financial_history():
    section_header("Historique Financier", "file")
    logs = [l for l in safe_get_all_audit_logs()
            if any(kw in l.get("action","") for kw in ("FINANCIAL","BUDGET","INVOICE","PRICE","OVERRIDE"))]
    if not logs:
        render_empty_state("file", "Aucun événement financier")
        return
    render_export_button(logs, filename="historique_financier.csv", columns=["action","actor_username","timestamp","entity_type"])
    for e in sorted(logs, key=lambda x: x.get("timestamp",""), reverse=True)[:50]:
        icon = "⚠️" if "OVERRIDE" in e.get("action","") else "🧾" if "INVOICE" in e.get("action","") else "💰"
        st.markdown(f'<div style="padding:6px 12px;border-left:3px solid #E8ECF1;margin-bottom:4px;font-size:13px">{icon} <strong>{e.get("action","")}</strong> <span style="color:#7F8C9B">par {e.get("actor_username","")}</span> <span style="color:#ABB2B9">{fmt_datetime(e.get("timestamp",""))}</span></div>', unsafe_allow_html=True)
