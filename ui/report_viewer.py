# ui/report_viewer.py — Dedicated report viewing page for requesters
from __future__ import annotations
import streamlit as st
import os
from datetime import datetime, timezone
from core.repository import get_request_by_report_token, save_request
from ui.styles import get_global_css
from ui.shared_components import render_star_rating_html, fmt_date


def render_report_viewer(token: str):
    st.markdown(get_global_css(), unsafe_allow_html=True)
    req = get_request_by_report_token(token)
    if not req:
        st.error("Lien invalide ou expiré.")
        return

    # Mark as delivered on first view
    if not req.get("report_delivered"):
        req["report_delivered"] = True
        req["report_delivered_at"] = datetime.now(timezone.utc).isoformat()
        save_request(req)

    # Header
    st.markdown("""
    <div style="text-align:center;padding:40px 20px">
        <div style="font-size:40px;margin-bottom:16px">🧬</div>
        <h1 style="color:#0F172A;font-size:28px;margin:0">PLAGENOR 4.0</h1>
        <p style="color:#64748B;font-size:15px;margin-top:8px">Votre rapport d'analyse est prêt</p>
    </div>
    """, unsafe_allow_html=True)

    # Request info
    st.markdown(f"""
    <div style="background:white;border-radius:16px;padding:32px;border:1px solid #F1F5F9;max-width:600px;margin:0 auto;box-shadow:0 4px 16px rgba(0,0,0,0.04)">
        <h3 style="margin:0 0 16px;color:#0F172A">{req.get('title','Rapport')}</h3>
        <p style="color:#64748B">Référence: <strong>{req.get('display_id','')}</strong></p>
        <p style="color:#64748B">Service: <strong>{req.get('service_code','')}</strong></p>
        <p style="color:#64748B">Date: <strong>{fmt_date(req.get('created_at',''))}</strong></p>
    </div>
    """, unsafe_allow_html=True)

    # Report download
    report_file = req.get("report_file", "")
    if report_file and os.path.exists(report_file):
        st.markdown("<br>", unsafe_allow_html=True)
        with open(report_file, "rb") as f:
            st.download_button(
                "📄 Télécharger le rapport",
                f.read(),
                file_name=os.path.basename(report_file),
                use_container_width=True,
                type="primary"
            )

    # Thank you + rating
    st.markdown("""
    <div style="text-align:center;padding:32px;margin-top:24px">
        <div style="font-size:32px;margin-bottom:12px">🙏</div>
        <h3 style="color:#0F172A;margin:0">Merci pour votre confiance!</h3>
        <p style="color:#64748B;margin-top:8px">Nous espérons que vous êtes satisfait de notre service.</p>
    </div>
    """, unsafe_allow_html=True)

    # Star rating
    if not req.get("service_rating"):
        st.markdown("##### ⭐ Évaluez notre service")
        cols = st.columns(5)
        for i in range(1, 6):
            with cols[i - 1]:
                if st.button("⭐" * i, key=f"report_rate_{i}"):
                    req["service_rating"] = i
                    req["rated_at"] = datetime.now(timezone.utc).isoformat()
                    save_request(req)
                    st.success(f"Merci pour votre évaluation! {'⭐' * i}")
                    st.rerun()
    else:
        rating = req.get("service_rating", 0)
        st.markdown(
            f"<div style='text-align:center'><p>Votre évaluation: {render_star_rating_html(rating)}</p></div>",
            unsafe_allow_html=True,
        )
