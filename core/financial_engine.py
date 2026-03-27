# core/financial_engine.py — PLAGENOR 4.0 Financial Engine
# IBTIKAR: 200K DA per student/year (virtual revenue). GENOCLAB: Invoicing (real revenue).

from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
import config
from core.exceptions import BudgetExceededError, BudgetOverrideRequiredError, InvoiceLockError
from core.repository import (
    get_all_active_requests, get_all_archived_requests,
    get_all_invoices, save_invoice, get_next_invoice_number,
    get_request, get_revenue_archives, save_revenue_archive,
)
from core.audit_engine import log_financial_action, log_budget_override


# ═══════════════════════════════════════════════════════════════════════════
# IBTIKAR — Virtual Revenue (per-student budget tracking)
# ═══════════════════════════════════════════════════════════════════════════

def get_ibtikar_virtual_revenue(year: Optional[int] = None) -> dict:
    """Calculate IBTIKAR virtual revenue = total budget consumed across ALL students.
    Each student has 200K DA/year. IBTIKAR revenue = sum of all validated request budgets."""
    if year is None:
        year = datetime.now().year
    total = 0.0
    count = 0
    requester_ids = set()
    for req in get_all_active_requests() + get_all_archived_requests():
        if req.get("channel") != config.CHANNEL_IBTIKAR:
            continue
        if req.get("status") in config.REJECTION_STATES:
            continue
        created = req.get("created_at", "")
        try:
            req_year = datetime.fromisoformat(created.replace("Z", "+00:00")).year
        except Exception:
            req_year = year
        if req_year == year:
            amt = float(req.get("budget_amount") or 0)
            total += amt
            count += 1
            rid = req.get("requester_id", "")
            if rid:
                requester_ids.add(rid)
    return {
        "total": total,
        "count": count,
        "students": len(requester_ids),
    }


def get_ibtikar_budget_used_by_requester(requester_id: str, year: Optional[int] = None) -> float:
    """Budget used by ONE specific student/requester."""
    if year is None:
        year = datetime.now().year
    total = 0.0
    for req in get_all_active_requests() + get_all_archived_requests():
        if req.get("channel") != config.CHANNEL_IBTIKAR:
            continue
        if req.get("requester_id") != requester_id:
            continue
        if req.get("status") in config.REJECTION_STATES:
            continue
        created = req.get("created_at", "")
        try:
            req_year = datetime.fromisoformat(created.replace("Z", "+00:00")).year
        except Exception:
            req_year = year
        if req_year == year:
            total += float(req.get("budget_amount") or 0)
    return total


def get_ibtikar_budget_used(year: Optional[int] = None) -> float:
    """TOTAL IBTIKAR virtual revenue (all students combined). Used for dashboard display."""
    return get_ibtikar_virtual_revenue(year).get("total", 0.0)


def check_ibtikar_budget(amount: float, actor: dict, request_id: str = "",
                          requester_id: str = "") -> dict:
    """Check if THIS STUDENT's budget allows the amount. Cap = 200K per student."""
    used = get_ibtikar_budget_used_by_requester(requester_id) if requester_id else 0.0
    cap = config.IBTIKAR_BUDGET_CAP  # 200,000 DA per student
    projected = used + amount

    result = {
        "used": used,
        "cap": cap,
        "amount": amount,
        "projected": projected,
        "exceeded": projected > cap,
        "remaining": max(0, cap - used),
        "pct_used": round(used / cap * 100, 1) if cap > 0 else 0,
    }

    if result["exceeded"]:
        if actor.get("role") == config.ROLE_SUPER_ADMIN:
            result["override_allowed"] = True
        else:
            result["override_allowed"] = False
            raise BudgetExceededError(
                f"Budget IBTIKAR de cet étudiant dépassé: {projected:,.0f} DZD / {cap:,.0f} DZD. "
                f"Seul le SUPER_ADMIN peut autoriser un dépassement."
            )
    return result


def approve_with_budget_override(request_id: str, actor: dict,
                                  amount: float, justification: str) -> dict:
    if actor.get("role") != config.ROLE_SUPER_ADMIN:
        raise BudgetExceededError("Seul le SUPER_ADMIN peut autoriser un override budgétaire")
    if not justification or len(justification.strip()) < 10:
        raise BudgetExceededError("La justification doit comporter au moins 10 caractères")

    log_budget_override(request_id, actor, amount, justification)
    return {"approved": True, "override": True, "justification": justification}


# ═══════════════════════════════════════════════════════════════════════════
# GENOCLAB — Real Revenue (invoicing)
# ═══════════════════════════════════════════════════════════════════════════

def generate_invoice(request: dict, actor: dict, line_items: Optional[list] = None) -> dict:
    if request.get("channel") != config.CHANNEL_GENOCLAB:
        raise ValueError("Les factures ne sont générées que pour GENOCLAB")

    inv_number = get_next_invoice_number()
    now = datetime.now(timezone.utc).isoformat()

    items = line_items or []
    if not items and request.get("quote_amount"):
        items = [{"description": request.get("title", "Service GENOCLAB"),
                  "quantity": 1, "unit_price": float(request.get("quote_amount", 0))}]

    subtotal = sum(item.get("quantity", 1) * item.get("unit_price", 0) for item in items)
    vat = round(subtotal * config.VAT_RATE, 2)
    total = round(subtotal + vat, 2)

    invoice = {
        "invoice_number": inv_number,
        "request_id": request.get("id"),
        "client_id": request.get("client_id", request.get("requester_id", "")),
        "channel": config.CHANNEL_GENOCLAB,
        "line_items": items,
        "subtotal_ht": subtotal,
        "vat_rate": config.VAT_RATE,
        "vat_amount": vat,
        "total_ttc": total,
        "status": "GENERATED",
        "locked": True,
        "created_at": now,
        "created_by": actor.get("id", ""),
    }

    saved = save_invoice(invoice)
    log_financial_action("INVOICE_GENERATED", saved.get("id", ""), actor, total, {
        "invoice_number": inv_number, "request_id": request.get("id"),
    })
    return saved


def get_revenue_summary() -> dict:
    """GENOCLAB real revenue from invoices."""
    invoices = get_all_invoices()
    total = sum(inv.get("total_ttc", 0) for inv in invoices)
    by_year = {}
    for inv in invoices:
        try:
            year = datetime.fromisoformat(
                inv.get("created_at", "").replace("Z", "+00:00")).year
        except Exception:
            year = datetime.now().year
        by_year[year] = by_year.get(year, 0) + inv.get("total_ttc", 0)
    return {"total": total, "count": len(invoices), "by_year": by_year}


# ═══════════════════════════════════════════════════════════════════════════
# COMBINED DASHBOARD DATA
# ═══════════════════════════════════════════════════════════════════════════

def get_budget_dashboard() -> dict:
    """Return symmetric data for both IBTIKAR and GENOCLAB revenue display."""
    ibtikar = get_ibtikar_virtual_revenue()
    genoclab = get_revenue_summary()

    return {
        # IBTIKAR — virtual revenue
        "ibtikar": {
            "total": ibtikar["total"],
            "count": ibtikar["count"],
            "students": ibtikar["students"],
            "budget_per_student": config.IBTIKAR_BUDGET_CAP,
            "label": "Revenus virtuels IBTIKAR",
        },
        # GENOCLAB — real revenue
        "genoclab": {
            "total": genoclab["total"],
            "count": genoclab["count"],
            "label": "Revenus GENOCLAB",
        },
        # Legacy fields for backward compatibility
        "used": ibtikar["total"],
        "cap": config.IBTIKAR_BUDGET_CAP,
        "remaining": 0,  # Not meaningful for global view
        "pct": 0,
        "revenue": genoclab,
    }


def archive_monthly_revenue(actor: dict) -> dict:
    """Snapshot current month's revenue for BOTH channels."""
    now = datetime.now(timezone.utc)
    month_key = now.strftime("%Y-%m")

    # GENOCLAB invoices
    invoices = get_all_invoices()
    month_invoices = []
    for inv in invoices:
        try:
            created = datetime.fromisoformat(inv.get("created_at", "").replace("Z", "+00:00"))
            if created.strftime("%Y-%m") == month_key:
                month_invoices.append(inv)
        except Exception:
            continue
    total_ht = sum(inv.get("subtotal_ht", 0) for inv in month_invoices)
    total_vat = sum(inv.get("vat_amount", 0) for inv in month_invoices)
    total_ttc = sum(inv.get("total_ttc", 0) for inv in month_invoices)

    # IBTIKAR virtual revenue
    ibtikar = get_ibtikar_virtual_revenue(now.year)

    archive = {
        "id": f"arch_{month_key}",
        "period": month_key,
        "month": month_key,
        "archived_at": now.isoformat(),
        "archived_by": actor.get("id", ""),
        # GENOCLAB
        "genoclab_invoices_count": len(month_invoices),
        "genoclab_total_ht": total_ht,
        "genoclab_total_vat": total_vat,
        "genoclab_total_ttc": total_ttc,
        # IBTIKAR
        "ibtikar_virtual_revenue": ibtikar["total"],
        "ibtikar_requests_count": ibtikar["count"],
        "ibtikar_students_count": ibtikar["students"],
        "ibtikar_budget_per_student": config.IBTIKAR_BUDGET_CAP,
    }
    save_revenue_archive(archive)
    log_financial_action("REVENUE_ARCHIVED", month_key, actor, total_ttc + ibtikar["total"], {
        "month": month_key, "genoclab_invoices": len(month_invoices),
        "ibtikar_requests": ibtikar["count"],
    })
    return archive


def reset_revenue_counters() -> None:
    """Placeholder called after archiving."""
    pass
