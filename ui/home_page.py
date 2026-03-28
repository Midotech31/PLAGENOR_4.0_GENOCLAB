# ui/home_page.py — PLAGENOR 4.0 Home Page (Professional Public Portal)
# Spec Section 1-2: Logos with links, channel cards, services, login, guest, tracking
from __future__ import annotations
import os, uuid, streamlit as st
from datetime import datetime, timezone
import config
from core.repository import (
    get_all_users, save_user, save_request,
    get_request_by_guest_token, get_services_for_channel,
    generate_request_id, get_user_by_username,
    get_login_attempts, increment_login_attempts,
    clear_login_attempts, set_lockout,
)
from core.audit_engine import log_action
from ui.styles import get_global_css, get_login_css
from services.registry_loader import load_service_registry
from utils import sanitize_html as _escape_html
from utils.i18n import t, get_lang, set_lang

_ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

def _img(name):
    p = os.path.join(_ASSETS, name)
    return p if os.path.exists(p) else None

def _verify_pw(stored, plain):
    """Verify password — werkzeug is a hard dependency, no SHA-256 fallback."""
    if not stored or not plain:
        return False
    from werkzeug.security import check_password_hash
    return check_password_hash(stored, plain)

def _find_user(username, plain_password):
    """Use indexed SQL lookup instead of loading all users."""
    user = get_user_by_username(username)
    if user and _verify_pw(user.get("password_hash", ""), plain_password):
        return user
    return None

def _hash(pw):
    from utils import hash_password
    return hash_password(pw)


def render_home_page():
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("home_section", "home")
    st.markdown(get_global_css(), unsafe_allow_html=True)
    st.markdown(get_login_css(), unsafe_allow_html=True)

    # ── SIDEBAR ──
    with st.sidebar:
        # Language switcher
        current_lang = get_lang()
        switch_label = t("lang_switch")
        if st.button(f"🌐 {switch_label}", use_container_width=True, key="home_lang_toggle"):
            new_lang = "en" if current_lang == "fr" else "fr"
            set_lang(new_lang)
            st.rerun()

        logo_p = _img("logo_plagenor.png")
        if logo_p: st.image(logo_p, use_container_width=True)
        st.markdown("---")
        logo_e = _img("logo_essbo.png")
        if logo_e: st.image(logo_e, width=150)
        st.markdown('<div style="text-align:center;font-size:12px;color:#8899AA;line-height:1.7;margin-top:8px"><strong>ESSBO</strong> · Oran, Algérie<br/>École Supérieure en Sciences<br/>Biologiques d\'Oran<br/><br/><a href="http://www.essb-oran.edu.dz/index.php/fr/" target="_blank" style="color:#5DADE2">Site ESSBO</a> · <a href="https://genoclab.my.canva.site/genoclab-essbo" target="_blank" style="color:#1ABC9C">GENOCLAB</a> · <a href="https://ibtikar.dgrsdt.dz/" target="_blank" style="color:#F39C12">IBTIKAR</a><br/><br/>© 2026 Prof. Mohamed Merzoug</div>', unsafe_allow_html=True)

    # ── NAVIGATION ──
    nav = st.columns([1.5, 1, 1, 1, 1, 1])
    with nav[0]: st.markdown('<div style="font-size:20px;font-weight:800;color:#1A202C;padding-top:6px">🧬 PLAGENOR</div>', unsafe_allow_html=True)
    section = st.session_state.get("home_section", "home")
    with nav[1]:
        if st.button(f"🏠 {t('home')}", use_container_width=True, key="nav_home"): section = "home"
    with nav[2]:
        if st.button(f"🔬 {t('services')}", use_container_width=True, key="nav_svc"): section = "services"
    with nav[3]:
        if st.button(f"ℹ️ {t('about')}", use_container_width=True, key="nav_about"): section = "about"
    with nav[4]:
        if st.button(f"🔐 {t('login')}", use_container_width=True, key="nav_login"): section = "login"
    with nav[5]:
        if st.button(f"🔍 {t('track')}", use_container_width=True, key="nav_track"): section = "track"
    st.session_state["home_section"] = section
    st.markdown("<br/>", unsafe_allow_html=True)

    if section == "home": _section_home()
    elif section == "services": _section_services()
    elif section == "about": _section_about()
    elif section == "login": _section_login()
    elif section == "track": _section_track()
    else: _section_home()

    # ── FOOTER ──
    st.markdown('<div style="text-align:center;margin-top:40px;padding:20px;border-top:1px solid #E2E8F0"><div style="font-size:11px;color:#566573;line-height:1.8">© 2026 Prof. Mohamed Merzoug — ESSBO · IBTIKAR-DGRSDT · GENOCLAB<br/>Cité Emir Abdelkader, 31000 Oran · 041 24 63 59 · <a href="mailto:mohamed.merzoug.essbo@gmail.com" style="color:#5DADE2">mohamed.merzoug.essbo@gmail.com</a></div></div>', unsafe_allow_html=True)


def _section_home():
    # Hero header with LARGE logos
    c1, c2, c3 = st.columns([1.2, 2.5, 1.2])
    with c1:
        lp = _img("logo_ibtikar.png") or _img("IBTIKAR Logo.png")
        if lp: st.image(lp, width=220)
    with c2:
        st.markdown('<div style="text-align:center;padding:10px 0"><div style="font-size:44px;font-weight:800;color:#1A202C;letter-spacing:2px;line-height:1.2">PLAGENOR 4.0</div><div style="font-size:17px;color:#64748B;margin-top:8px;font-weight:500">Plateforme Technologique de Génomique — ESSBO · ORAN</div></div>', unsafe_allow_html=True)
    with c3:
        lg = _img("logo_genoclab.png") or _img("GENOCLAB Logo.png")
        if lg: st.image(lg, width=220)
    st.markdown("<br/>", unsafe_allow_html=True)

    # Two channel cards — BIGGER text and padding
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:20px;padding:36px;box-shadow:0 4px 20px rgba(0,0,0,0.06)"><div style="text-align:center;font-size:26px;font-weight:800;color:#D97706;margin-bottom:16px">🏛 IBTIKAR — DGRSDT</div><div style="font-size:15px;color:#4A5568;line-height:2">Programme national de soutien à la recherche scientifique et à l\'innovation via un accès financé aux services de laboratoire.<br/><br/><strong style="color:#1A202C;font-size:16px">Éligibilité :</strong> Étudiants Master (fin de cycle), Ingéniorat et Doctorants de <strong style="color:#D97706">toutes les universités algériennes</strong>.<br/><br/><strong style="color:#1A202C;font-size:16px">Budget :</strong> <span style="color:#D97706;font-weight:800;font-size:18px">200 000 DA</span> virtuel annuel par étudiant, géré via la DGRSDT.<br/><br/>✦ Validation pédagogique + financière<br/>✦ Formulaire IBTIKAR officiel auto-généré<br/>✦ Suivi en temps réel</div><div style="text-align:center;margin-top:20px"><a href="https://ibtikar.dgrsdt.dz/" target="_blank" style="color:#D97706;font-size:15px;font-weight:600;text-decoration:none">🌐 ibtikar.dgrsdt.dz →</a></div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:20px;padding:36px;box-shadow:0 4px 20px rgba(0,0,0,0.06)"><div style="text-align:center;font-size:26px;font-weight:800;color:#0E8C7F;margin-bottom:16px">🧬 GENOCLAB</div><div style="font-size:15px;color:#4A5568;line-height:2">Laboratoire de services génomiques : séquençage, bio-informatique et analyses de génomique microbienne.<br/><br/><strong style="color:#1A202C;font-size:16px">Public :</strong> Entreprises, hôpitaux, laboratoires, chercheurs externes, particuliers.<br/><br/><strong style="color:#1A202C;font-size:16px">Tarification :</strong> Devis personnalisé · Facturation TVA 19% · Paiement avant analyse.<br/><br/>✦ Devis automatique basé sur le catalogue<br/>✦ Soumission possible sans compte (invité)<br/>✦ Suivi par code de tracking unique</div><div style="text-align:center;margin-top:20px"><a href="https://genoclab.my.canva.site/genoclab-essbo" target="_blank" style="color:#0E8C7F;font-size:15px;font-weight:600;text-decoration:none">🌐 genoclab-essbo →</a></div></div>', unsafe_allow_html=True)
    st.markdown("<br/>", unsafe_allow_html=True)

    # CTAs
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button(f"📋 {t('submit')}", use_container_width=True, type="primary", key="cta1"):
            st.session_state["home_section"] = "login"; st.rerun()
    with c2:
        if st.button(f"🔬 {t('services')}", use_container_width=True, key="cta2"):
            st.session_state["home_section"] = "services"; st.rerun()
    with c3:
        if st.button(f"🔍 {t('track')}", use_container_width=True, key="cta3"):
            st.session_state["home_section"] = "track"; st.rerun()
    st.markdown("<br/>", unsafe_allow_html=True)

    # Service highlights — BIGGER cards
    registry = load_service_registry()
    if registry:
        st.markdown('<div style="text-align:center;font-size:24px;font-weight:800;color:#1A202C;margin-bottom:20px">🔬 Nos Services</div>', unsafe_allow_html=True)
        cols = st.columns(min(4, len(registry)))
        for i, (code, svc) in enumerate(sorted(registry.items())):
            with cols[i % len(cols)]:
                name = svc.get("service_name", code)[:45]
                cat = svc.get("category", "")
                st.markdown(f'<div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:14px;padding:20px;margin-bottom:10px;min-height:110px;box-shadow:0 2px 8px rgba(0,0,0,0.04);transition:box-shadow 0.2s"><div style="font-size:12px;color:#0E8C7F;font-weight:700;letter-spacing:0.5px">{code}</div><div style="font-size:15px;color:#1A202C;font-weight:700;margin:6px 0">{name}</div><div style="font-size:13px;color:#64748B">{cat}</div></div>', unsafe_allow_html=True)


def _section_services():
    st.markdown('<div style="text-align:center;font-size:24px;font-weight:700;color:#1A202C;margin-bottom:20px">🔬 Catalogue des Services</div>', unsafe_allow_html=True)
    registry = load_service_registry()
    if not registry: st.info("Catalogue en cours de chargement..."); return

    # Service info doc mapping
    svc_info_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates", "genoclab")
    svc_info_map = {
        "EGTP-IMT": "Service_info_-_Microbial_identification_via_MALDI.docx",
        "EGTP-PCR": "Service_info_-_PCR.docx",
        "EGTP-SeqS": "Service_info_-_DNA_Sequencing_via_Sanger_Method.docx",
        "EGTP-Seq02": "Service_info_-_PCR_Amplification_and_Sequencing.docx",
        "EGTP-CAN": "Service_info_-_Nucleic_Acid_Quality_Control.docx",
        "EGTP-PS": "Service_info_-_Primer_Synthesis.docx",
        "EGTP-Lyoph": "Service_info_-_Lyophilization.docx",
        "EGTP-Illumina-Microbial-WGS": "Service_info_-_Microbial_Whole_Genome_Sequencing.docx",
    }

    for code in sorted(registry.keys()):
        svc = registry[code]
        name = svc.get("service_name", code)
        desc = svc.get("description", "").strip()[:250]
        pricing = svc.get("pricing", {})
        turnaround = svc.get("turnaround_time", "").strip()[:120]
        if pricing.get("model") == "per_sample_fixed":
            price_str = f"{pricing.get('unit_price', 0):,} DZD / échantillon"
        elif pricing.get("base_price"):
            bp = pricing["base_price"]
            price_str = f"{bp.get('non_pathogenic',0):,} — {bp.get('pathogenic',0):,} DZD"
        else: price_str = "Sur devis"
        with st.expander(f"**{code}** — {name}"):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(desc)
                if turnaround: st.markdown(f"**Délai :** {turnaround}")
                params = svc.get("parameters", [])
                st.caption(f"📋 {len(params)} paramètres · 📊 {len(svc.get('sample_table',{}).get('columns',[])) if svc.get('sample_table',{}).get('enabled') else 0} colonnes d'échantillons")
                # Service info download
                info_file = svc_info_map.get(code, "")
                info_path = os.path.join(svc_info_dir, info_file)
                if info_file and os.path.exists(info_path):
                    with open(info_path, "rb") as f:
                        st.download_button(f"📄 Fiche technique {code}", f.read(),
                                         file_name=info_file,
                                         mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                         key=f"dl_info_{code}")
            with c2:
                st.markdown(f'<div style="background:rgba(14,140,127,0.08);border:1px solid #0E8C7F;border-radius:12px;padding:16px;text-align:center"><div style="font-size:11px;color:#0E8C7F;font-weight:600">TARIF</div><div style="font-size:16px;font-weight:700;color:#1A202C;margin:8px 0">{price_str}</div><div style="font-size:10px;color:#718096">IBTIKAR & GENOCLAB</div></div>', unsafe_allow_html=True)


def _section_about():
    lang = get_lang()
    if lang == "en":
        about_html = """<div style="max-width:700px;margin:0 auto">
<div style="text-align:center;font-size:24px;font-weight:700;color:#1A202C;margin-bottom:20px">About PLAGENOR</div>
<div style="font-size:14px;color:#4A5568;line-height:1.9">
<strong style="color:#0E8C7F">ESSBO</strong> (École Supérieure en Sciences Biologiques d'Oran) hosts <strong style="color:#1A202C;font-size:16px">PLAGENOR</strong>, a <em>service commun de recherche</em> (shared research facility) funded by the <strong>DGRSDT</strong> (Direction Générale de la Recherche Scientifique et du Développement Technologique).<br/><br/>

PLAGENOR hosts <strong style="color:#0E8C7F">GENOCLAB</strong>, the commercial subsidiary (<em>filiale commerciale SPA</em>) of ESSBO, governed by Algerian commercial code (SPA).<br/><br/>

<strong style="color:#1A202C;font-size:16px">PLAGENOR 4.0</strong> is the digital management platform for all PLAGENOR activities — acting as an internal ERP to organize workflows, manage IBTIKAR requests, and manage GENOCLAB clients.<br/><br/>

<strong style="color:#1A202C">Two missions:</strong><br/>
&nbsp;&nbsp;1. <strong style="color:#F39C12">IBTIKAR-DGRSDT</strong> — Genomic analyses for Algerian students (Master, Engineering, Doctorate). Students register on <a href="https://ibtikar.dgrsdt.dz/" target="_blank" style="color:#F39C12">ibtikar.dgrsdt.dz</a> and submit requests there; PLAGENOR receives these requests via its IBTIKAR account. Budget: 200,000 DA/year per student.<br/>
&nbsp;&nbsp;2. <strong style="color:#0E8C7F">GENOCLAB</strong> — Commercial genomic analyses for enterprises, hospitals, laboratories, external researchers, and individuals. Custom quotes, 19% VAT, payment before analysis.<br/><br/>

<strong style="color:#1A202C">Services:</strong> Microbial identification (MALDI-TOF), Sanger &amp; Illumina sequencing, PCR, nucleic acid quality control, lyophilization, primer synthesis.<br/><br/>

<strong style="color:#1A202C">Contact:</strong> Prof. Mohamed Merzoug · <a href="mailto:mohamed.merzoug.essbo@gmail.com" style="color:#2E86C1">mohamed.merzoug.essbo@gmail.com</a> · 041 24 63 59<br/>📍 Cité Emir Abdelkader, 31000 Oran
</div></div>"""
    else:
        about_html = """<div style="max-width:700px;margin:0 auto">
<div style="text-align:center;font-size:24px;font-weight:700;color:#1A202C;margin-bottom:20px">À propos de PLAGENOR</div>
<div style="font-size:14px;color:#4A5568;line-height:1.9">
L'<strong style="color:#0E8C7F">ESSBO</strong> (École Supérieure en Sciences Biologiques d'Oran) héberge <strong style="color:#1A202C;font-size:16px">PLAGENOR</strong>, un <em>service commun de recherche</em> financé par la <strong>DGRSDT</strong> (Direction Générale de la Recherche Scientifique et du Développement Technologique).<br/><br/>

PLAGENOR héberge <strong style="color:#0E8C7F">GENOCLAB</strong>, la filiale commerciale (SPA) de l'ESSBO, régie par le code de commerce algérien.<br/><br/>

<strong style="color:#1A202C;font-size:16px">PLAGENOR 4.0</strong> est la plateforme numérique de gestion de toutes les activités de PLAGENOR — agissant comme un ERP interne pour organiser les flux de travail, gérer les demandes IBTIKAR et les clients GENOCLAB.<br/><br/>

<strong style="color:#1A202C">Deux missions :</strong><br/>
&nbsp;&nbsp;1. <strong style="color:#F39C12">IBTIKAR-DGRSDT</strong> — Analyses génomiques pour les étudiants algériens (Master, Ingéniorat, Doctorat). Les étudiants s'inscrivent sur <a href="https://ibtikar.dgrsdt.dz/" target="_blank" style="color:#F39C12">ibtikar.dgrsdt.dz</a> et y soumettent leurs demandes ; PLAGENOR reçoit ces demandes via son compte IBTIKAR. Budget : 200 000 DA/an par étudiant.<br/>
&nbsp;&nbsp;2. <strong style="color:#0E8C7F">GENOCLAB</strong> — Analyses génomiques commerciales pour entreprises, hôpitaux, laboratoires, chercheurs externes et particuliers. Devis personnalisé, TVA 19%, paiement avant analyse.<br/><br/>

<strong style="color:#1A202C">Services :</strong> Identification microbienne (MALDI-TOF), séquençage Sanger &amp; Illumina, PCR, contrôle qualité des acides nucléiques, lyophilisation, synthèse d'amorces.<br/><br/>

<strong style="color:#1A202C">Contact :</strong> Prof. Mohamed Merzoug · <a href="mailto:mohamed.merzoug.essbo@gmail.com" style="color:#2E86C1">mohamed.merzoug.essbo@gmail.com</a> · 041 24 63 59<br/>📍 Cité Emir Abdelkader, 31000 Oran
</div></div>"""
    st.markdown(about_html, unsafe_allow_html=True)


def _section_login():
    tabs = st.tabs([f"🔐 {t('login')}", f"📝 {t('register')}", f"📬 {t('guest_submit')}"])
    with tabs[0]: _login()
    with tabs[1]: _register()
    with tabs[2]: _guest_submit()


def _login():
    _c, cc, _r = st.columns([1, 2, 1])
    with cc:
        st.markdown('<div style="text-align:center;color:#1A202C;font-size:20px;font-weight:700;margin-bottom:16px">🔐 Connexion</div>', unsafe_allow_html=True)
        with st.form("login_form"):
            u = st.text_input("Identifiant", placeholder="Votre identifiant")
            p = st.text_input("Mot de passe", type="password", placeholder="Votre mot de passe")
            if st.form_submit_button("Se connecter", use_container_width=True, type="primary"):
                if not u.strip() or not p.strip(): st.warning("Identifiant et mot de passe requis."); return
                username = u.strip()
                # Rate limiting — DB-persisted (SEC-02)
                attempts_info = get_login_attempts(username)
                if attempts_info.get("locked_until"):
                    try:
                        lockout_time = datetime.fromisoformat(attempts_info["locked_until"])
                        elapsed = (datetime.now(timezone.utc) - lockout_time).total_seconds()
                        if elapsed < 900:  # 15 minutes
                            remaining = int((900 - elapsed) / 60) + 1
                            st.error(f"🔒 Compte temporairement verrouillé. Réessayez dans {remaining} minutes.")
                            return
                        else:
                            clear_login_attempts(username)
                    except Exception:
                        clear_login_attempts(username)
                user = _find_user(username, p.strip())
                if not user:
                    increment_login_attempts(username)
                    updated = get_login_attempts(username)
                    if updated["count"] >= config.MAX_LOGIN_ATTEMPTS:
                        set_lockout(username, datetime.now(timezone.utc).isoformat())
                        st.error("🔒 Trop de tentatives. Compte verrouillé pour 15 minutes.")
                    else:
                        st.error("Identifiant ou mot de passe incorrect.")
                    log_action("LOGIN_FAILED", "AUTH", "", actor={"id": "", "username": username, "role": ""},
                               details={"attempts": updated["count"]})
                    return
                if not user.get("active", True): st.error("Compte désactivé."); return
                # Reset attempts on successful login
                clear_login_attempts(username)
                # SEC-03: Generate per-session CSRF token
                import secrets
                st.session_state["csrf_token"] = secrets.token_urlsafe(32)
                st.session_state["authenticated"] = True
                st.session_state["user"] = user
                log_action("LOGIN_SUCCESS", "AUTH", user.get("id",""), actor=user)
                st.rerun()


def _register():
    _c, cc, _r = st.columns([1, 2, 1])
    with cc:
        st.markdown('<div style="text-align:center;color:#1A202C;font-size:20px;font-weight:700;margin-bottom:4px">📝 Créer un compte</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;color:#718096;font-size:13px;margin-bottom:16px">Étudiants IBTIKAR et clients GENOCLAB</div>', unsafe_allow_html=True)
        with st.form("reg_form", clear_on_submit=True):
            rn = st.text_input("Nom complet *")
            re_ = st.text_input("Email *")
            role = st.selectbox("Type de compte *", ["Demandeur IBTIKAR (étudiant/chercheur)", "Client GENOCLAB (externe)"])
            is_ibtikar = "IBTIKAR" in role
            if is_ibtikar:
                st.markdown('<div style="font-size:12px;color:#F39C12;margin:4px 0 8px">Master, Ingéniorat (fin de cycle) ou Doctorat — toutes universités algériennes</div>', unsafe_allow_html=True)
                r_univ = st.text_input("Université / École *")
                r_level = st.selectbox("Niveau *", ["Master (fin de cycle)", "Ingéniorat (fin de cycle)", "Doctorat"])
                r_lab = st.text_input("Laboratoire")
                r_sup = st.text_input("Directeur de recherche *")
            else:
                r_univ = st.text_input("Organisation *")
                r_level = r_lab = r_sup = ""
            rp = st.text_input("Téléphone")
            ru = st.text_input("Identifiant souhaité *")
            rpw = st.text_input("Mot de passe *", type="password")
            if st.form_submit_button("Créer mon compte", use_container_width=True, type="primary"):
                if not rn.strip() or not re_.strip() or not ru.strip() or not rpw or len(rpw) < config.MIN_PASSWORD_LENGTH:
                    st.warning(f"Champs * obligatoires. Mot de passe min {config.MIN_PASSWORD_LENGTH} car."); return
                if not r_univ.strip(): st.warning("Université / Organisation obligatoire."); return
                if is_ibtikar and not r_sup.strip(): st.warning("Directeur de recherche obligatoire."); return
                if any(u.get("username")==ru.strip() for u in get_all_users()): st.error("Identifiant déjà pris."); return
                if any(u.get("email")==re_.strip() for u in get_all_users()): st.error("Email déjà utilisé."); return
                user_role = config.ROLE_REQUESTER if is_ibtikar else config.ROLE_CLIENT
                new_user = {"id": str(uuid.uuid4()), "username": ru.strip(), "full_name": rn.strip(), "password_hash": _hash(rpw), "role": user_role, "email": re_.strip(), "organization_id": r_univ.strip(), "phone": rp.strip(), "student_level": r_level if is_ibtikar else "", "supervisor": r_sup.strip() if is_ibtikar else "", "laboratory": r_lab.strip() if is_ibtikar else "", "active": True, "created_at": datetime.now(timezone.utc).isoformat(), "self_registered": True}
                save_user(new_user)
                from core.repository import link_guest_requests_to_client
                linked = link_guest_requests_to_client(re_.strip(), new_user["id"])
                log_action("USER_REGISTERED", "USER", new_user["id"], actor=new_user, details={"role": user_role, "guest_linked": linked})
                st.session_state["authenticated"] = True; st.session_state["user"] = new_user
                st.success(f"Compte créé!{f' {linked} demande(s) liée(s).' if linked else ''}"); st.rerun()


def _guest_submit():
    _c, cc, _r = st.columns([1, 2, 1])
    with cc:
        st.markdown('<div style="text-align:center;color:#1A202C;font-size:20px;font-weight:700;margin-bottom:4px">📬 Demande sans compte</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;color:#718096;font-size:13px;margin-bottom:16px">IBTIKAR ou GENOCLAB — Recevez un code de suivi</div>', unsafe_allow_html=True)
        registry = load_service_registry()
        if not registry:
            st.info("Catalogue de services en cours de chargement..."); return
        svc_labels = {f"{c} — {s.get('service_name','')}": c for c, s in sorted(registry.items())}

        # Step 1: Guest info + service selection
        with st.form("guest_form_step1"):
            st.markdown("**Vos informations**")
            gc1, gc2 = st.columns(2)
            with gc1:
                gn = st.text_input("Nom complet *")
                ge = st.text_input("Email *")
            with gc2:
                gp = st.text_input("Téléphone")
                go = st.text_input("Organisation")
            g_channel = st.selectbox("Canal *", ["GENOCLAB (externe)", "IBTIKAR (étudiant/chercheur)"])
            gs = st.selectbox("Service demandé *", ["— Sélectionner —"] + list(svc_labels.keys()))
            if gs != "— Sélectionner —":
                svc_code = svc_labels.get(gs, "")
                svc_def = registry.get(svc_code, {})
                if svc_def.get("description"):
                    st.info(svc_def["description"][:200])

                # Service-specific parameters from YAML
                st.markdown("**Paramètres du service**")
                from services.form_renderer import render_service_params
                svc_params = render_service_params(svc_def, prefix="guest_p")
            else:
                svc_code = ""; svc_def = {}; svc_params = {}

            gd = st.text_area("Description complémentaire", height=100)

            if st.form_submit_button("📤 Soumettre la demande", use_container_width=True, type="primary"):
                if not gn.strip() or not ge.strip() or gs == "— Sélectionner —":
                    st.warning("Nom, email et service sont obligatoires."); return
                channel = config.CHANNEL_IBTIKAR if "IBTIKAR" in g_channel else config.CHANNEL_GENOCLAB
                token = str(uuid.uuid4())  # SEC-05: full UUID for entropy
                # ARCH-01/UX-01: Route through service layer for server-side validation
                guest_actor = {"id": "guest", "username": ge.strip(), "role": "GUEST",
                               "full_name": gn.strip()}
                try:
                    data = {
                        "title": f"{svc_code} — {gn.strip()}",
                        "description": gd.strip(),
                        "service_code": svc_code,
                        "service_id": svc_code,
                        "service_params": svc_params,
                        "client_name": gn.strip(),
                        "organization": go.strip(),
                        "contact": gp.strip(),
                        "sample_count": 1,
                    }
                    if channel == config.CHANNEL_IBTIKAR:
                        data["requester"] = {"full_name": gn.strip(), "institution": go.strip(), "email": ge.strip()}
                        data["requester_name"] = gn.strip()
                        from core.services.ibtikar_service import submit_ibtikar_request
                        saved = submit_ibtikar_request(data, guest_actor)
                    else:
                        from core.services.genoclab_service import submit_genoclab_request
                        saved = submit_genoclab_request(data, guest_actor)
                    # Mark as guest and add tracking token
                    saved["submitted_as_guest"] = True
                    saved["guest_token"] = token
                    saved["guest_name"] = gn.strip()
                    saved["guest_email"] = ge.strip()
                    saved["guest_phone"] = gp.strip()
                    from datetime import timedelta
                    saved["guest_token_expires_at"] = (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()
                    save_request(saved)
                except Exception as e:
                    st.error(f"❌ Erreur: {e}")
                    return
                log_action("GUEST_REQUEST", "REQUEST", saved["id"],
                          actor=guest_actor,
                          details={"token": token, "channel": channel, "service": svc_code},
                          channel=channel)
                st.success("✅ Demande soumise avec succès!")
                st.markdown(f'<div style="background:rgba(39,174,96,0.08);border:2px solid #27AE60;border-radius:16px;padding:24px;text-align:center;margin:16px 0"><div style="color:#4A5568;font-size:13px">Votre code de suivi :</div><div style="font-size:36px;font-weight:800;color:#27AE60;font-family:monospace;letter-spacing:4px;margin:8px 0">{_escape_html(token)}</div><div style="color:#718096;font-size:12px">Utilisez le menu "🔍 Suivi" pour suivre votre demande.</div></div>', unsafe_allow_html=True)


def _section_track():
    _c, cc, _r = st.columns([1, 2, 1])
    with cc:
        st.markdown('<div style="text-align:center;color:#1A202C;font-size:20px;font-weight:700;margin-bottom:16px">🔍 Suivre ma demande</div>', unsafe_allow_html=True)
        tk = st.text_input("Code de suivi", placeholder="Ex: A1B2C3D4")
        if st.button("🔍 Rechercher", use_container_width=True, type="primary", key="track_btn"):
            if not tk.strip(): st.warning("Entrez un code."); return
            req = get_request_by_guest_token(tk.strip().upper())
            if not req: st.error("Aucune demande trouvée."); return
            from ui.shared_components import get_status_badge_html, fmt_date
            title_safe = _escape_html(req.get("title", ""))
            svc_safe = _escape_html(req.get("service_id", "—"))
            st.markdown(f'<div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:16px;padding:24px;margin-top:12px;box-shadow:0 2px 8px rgba(0,0,0,0.04)"><div style="font-size:18px;font-weight:700;color:#1A202C;margin-bottom:8px">{title_safe}</div><div style="margin-bottom:10px">{get_status_badge_html(req.get("status",""))}</div><div style="font-size:13px;color:#718096;line-height:1.8">📅 {fmt_date(req.get("created_at",""))} · 🧬 {svc_safe} · 📊 {_escape_html(str(req.get("sample_count","—")))} échantillons</div></div>', unsafe_allow_html=True)
            for h in req.get("history", []):
                from_safe = _escape_html(h.get("from", "Début"))
                to_safe = _escape_html(h.get("to", ""))
                st.markdown(f'<div style="padding:6px 12px;border-left:3px solid rgba(14,140,127,0.4);margin:4px 0;font-size:12px;color:#718096"><strong style="color:#4A5568">{from_safe}</strong> → <strong style="color:#1A202C">{to_safe}</strong> · {fmt_date(h.get("at",""))}</div>', unsafe_allow_html=True)
