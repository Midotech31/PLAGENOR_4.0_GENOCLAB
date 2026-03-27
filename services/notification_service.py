# services/notification_service.py — PLAGENOR 4.0 Notification Service

from __future__ import annotations
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from typing import Optional
import config
from core.repository import (
    create_notification, get_all_notifications,
    get_all_users, get_user, mark_notification_read,
)
from core.logger import get_logger

_log = get_logger("notification_service")


def send_email_notification(to_email: str, subject: str, body_text: str) -> bool:
    """Send an HTML email via SMTP. Returns True on success, False on failure."""
    if not config.SMTP_ENABLED or not to_email:
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{config.SMTP_FROM_NAME} <{config.SMTP_FROM_EMAIL}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        html_body = f"""<html><body style="font-family:Arial,sans-serif;color:#1B2838;max-width:600px;margin:auto">
<div style="background:#1B4F72;padding:16px 24px;border-radius:8px 8px 0 0">
  <h2 style="color:#fff;margin:0">{config.APP_TITLE}</h2>
  <p style="color:#AED6F1;margin:4px 0 0;font-size:13px">{config.APP_SUBTITLE}</p>
</div>
<div style="padding:24px;border:1px solid #E8ECF1;border-top:none;border-radius:0 0 8px 8px">
  <p style="font-size:14px;line-height:1.6">{body_text}</p>
  <hr style="border:none;border-top:1px solid #E8ECF1;margin:24px 0"/>
  <p style="font-size:11px;color:#7F8C9B">{config.PLATFORM_INSTITUTION}<br/>{config.PLATFORM_ADDRESS}</p>
</div></body></html>"""
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.send_message(msg)
        _log.info("Email envoyé à %s: %s", to_email, subject)
        return True
    except Exception as e:
        _log.error("Échec envoi email à %s: %s", to_email, e)
        return False


def notify_user(user_id: str, message: str, notif_type: str = "INFO",
                request_id: str = "", channel: str = ""):
    return create_notification({
        "user_id": user_id,
        "message": message,
        "type": notif_type,
        "request_id": request_id,
        "channel": channel,
    })


def notify_role(role: str, message: str, notif_type: str = "INFO",
                request_id: str = "", channel: str = ""):
    users = get_all_users()
    for u in users:
        if u.get("role") == role:
            notify_user(u.get("id", ""), message, notif_type, request_id, channel)


def notify_workflow_transition(request: dict, to_state: str, actor: dict):
    """Send notifications based on workflow transitions."""
    channel = request.get("channel", "")
    req_id = request.get("id", "")
    title = request.get("title", "Demande")

    notification_map = {
        # ── IBTIKAR workflow notifications ──
        "SUBMITTED": {
            "targets": [],  # admin notified via dashboard
            "msg": f"📋 Nouvelle demande soumise: '{title}'.",
            "roles": [config.ROLE_PLATFORM_ADMIN],
        },
        "VALIDATION_PEDAGOGIQUE": {
            "targets": [request.get("requester_id")],
            "msg": f"🎓 Votre demande '{title}' a passé la validation pédagogique.",
        },
        "VALIDATION_FINANCE": {
            "targets": [request.get("requester_id")],
            "msg": f"💰 Votre demande '{title}' a été approuvée financièrement.",
        },
        "PLATFORM_NOTE_GENERATED": {
            "targets": [request.get("requester_id")],
            "msg": f"📋 La note de plateforme pour '{title}' a été générée.",
        },
        "REJECTED": {
            "targets": [request.get("requester_id"), request.get("client_id")],
            "msg": f"❌ Votre demande '{title}' a été rejetée.",
        },
        "ASSIGNED": {
            "targets": [request.get("assigned_to")],
            "msg": f"🔬 Une nouvelle analyse vous a été assignée: '{title}'.",
            "roles": [config.ROLE_MEMBER],
        },
        "SAMPLE_RECEIVED": {
            "targets": [request.get("requester_id"), request.get("client_id")],
            "msg": f"📦 Vos échantillons pour '{title}' ont été réceptionnés.",
        },
        "ANALYSIS_STARTED": {
            "targets": [request.get("requester_id"), request.get("client_id")],
            "msg": f"🔬 L'analyse pour '{title}' a démarré.",
        },
        "ANALYSIS_FINISHED": {
            "targets": [],
            "msg": f"🧪 L'analyse pour '{title}' est terminée.",
            "roles": [config.ROLE_PLATFORM_ADMIN],
        },
        # ── GENOCLAB workflow notifications ──
        "REQUEST_CREATED": {
            "targets": [],
            "msg": f"📥 Nouvelle demande GENOCLAB: '{title}'.",
            "roles": [config.ROLE_PLATFORM_ADMIN],
        },
        "QUOTE_SENT": {
            "targets": [request.get("client_id")],
            "msg": f"💵 Un devis pour '{title}' vous a été envoyé.",
        },
        "QUOTE_VALIDATED_BY_CLIENT": {
            "targets": [],
            "msg": f"🤝 Le devis pour '{title}' a été accepté par le client.",
            "roles": [config.ROLE_PLATFORM_ADMIN, config.ROLE_FINANCE],
        },
        "INVOICE_GENERATED": {
            "targets": [request.get("client_id")],
            "msg": f"🧾 La facture pour '{title}' a été générée.",
            "roles": [config.ROLE_FINANCE],
        },
        "PAYMENT_CONFIRMED": {
            "targets": [request.get("client_id")],
            "msg": f"💳 Le paiement pour '{title}' a été confirmé.",
        },
        # ── Shared final states ──
        "REPORT_UPLOADED": {
            "targets": [],
            "msg": f"📄 Le rapport pour '{title}' a été uploadé.",
            "roles": [config.ROLE_PLATFORM_ADMIN],
        },
        "REPORT_VALIDATED": {
            "targets": [request.get("requester_id"), request.get("client_id")],
            "msg": f"📋 Le rapport pour '{title}' a été validé et est disponible.",
        },
        "COMPLETED": {
            "targets": [request.get("requester_id"), request.get("client_id")],
            "msg": f"🎉 La demande '{title}' est complétée.",
        },
    }

    config_entry = notification_map.get(to_state)
    if not config_entry:
        return

    targets = [t for t in config_entry.get("targets", []) if t]
    for target_id in targets:
        if target_id != actor.get("id"):
            notify_user(target_id, config_entry["msg"], "WORKFLOW", req_id, channel)
            # Send email if SMTP enabled
            if config.SMTP_ENABLED:
                target_user = get_user(target_id)
                if target_user and target_user.get("email"):
                    send_email_notification(
                        target_user["email"],
                        f"[{config.APP_TITLE}] {title} — {to_state}",
                        config_entry["msg"],
                    )

    for role in config_entry.get("roles", []):
        notify_role(role, config_entry["msg"], "WORKFLOW", req_id, channel)


def get_unread_count(user_id: str) -> int:
    notifs = get_all_notifications()
    return sum(1 for n in notifs
               if n.get("user_id") == user_id and not n.get("read", False))


def get_user_notifications(user_id: str, limit: int = 50) -> list:
    notifs = get_all_notifications()
    user_notifs = [n for n in notifs if n.get("user_id") == user_id]
    user_notifs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return user_notifs[:limit]
