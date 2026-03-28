# core/productivity_engine.py — PLAGENOR 4.0 Productivity Engine

from __future__ import annotations
from datetime import datetime, timezone
import config
from core.repository import (
    get_all_members, get_member, save_member,
    get_all_active_requests, get_all_archived_requests,
)


PERFORMANCE_LEVELS = [
    {"key": "fire", "emoji": "\U0001f525", "label_fr": "Le plus rapide", "label_en": "Fastest", "min_score": 90},
    {"key": "very_good", "emoji": "\u2b50", "label_fr": "Très bien", "label_en": "Very Good", "min_score": 75},
    {"key": "good", "emoji": "\U0001f44d", "label_fr": "Bien", "label_en": "Good", "min_score": 60},
    {"key": "not_bad", "emoji": "\U0001f642", "label_fr": "Pas mal", "label_en": "Not Bad", "min_score": 0},
]


def get_performance_level(score: float) -> dict:
    for level in PERFORMANCE_LEVELS:
        if score >= level["min_score"]:
            return level
    return PERFORMANCE_LEVELS[-1]


def get_productivity_status(score: float) -> str:
    if score >= config.SCORE_EXCELLENT:
        return "EXCELLENT"
    elif score >= config.SCORE_GOOD:
        return "GOOD"
    elif score >= config.SCORE_NORMAL:
        return "NORMAL"
    return "LOW"


def compute_member_productivity(member_id: str) -> dict:
    # PERF-05: Use targeted SQL query instead of loading all requests
    from core.repository import _get_all, _JSON_FIELDS_REQUESTS
    assigned = _get_all("requests", _JSON_FIELDS_REQUESTS,
                        "assigned_to=?", (member_id,))

    total = len(assigned)
    completed = [r for r in assigned if r.get("status") == "COMPLETED"]
    in_progress = [r for r in assigned if r.get("status") in (
        "ANALYSIS_STARTED", "ANALYSIS_FINISHED", "SAMPLE_RECEIVED")]

    completion_rate = (len(completed) / total * 100) if total > 0 else 50.0

    # On-time rate
    on_time = 0
    for r in completed:
        sla = config.SLA_DAYS_IBTIKAR if r.get("channel") == "IBTIKAR" else config.SLA_DAYS_GENOCLAB
        try:
            created = datetime.fromisoformat(r.get("created_at", "").replace("Z", "+00:00"))
            updated = datetime.fromisoformat(r.get("updated_at", "").replace("Z", "+00:00"))
            days = (updated - created).days
            if days <= sla:
                on_time += 1
        except Exception:
            on_time += 1

    on_time_rate = (on_time / len(completed) * 100) if completed else 50.0

    score = round(completion_rate * 0.6 + on_time_rate * 0.4, 1)
    score = max(0, min(100, score))

    status = get_productivity_status(score)

    return {
        "member_id": member_id,
        "total_assigned": total,
        "completed": len(completed),
        "in_progress": len(in_progress),
        "completion_rate": round(completion_rate, 1),
        "on_time_rate": round(on_time_rate, 1),
        "score": score,
        "status": status,
        "emoji": config.PRODUCTIVITY_EMOJI.get(status, "⚪"),
    }


def recalculate_member(member_id: str) -> dict:
    metrics = compute_member_productivity(member_id)
    member = get_member(member_id)
    if member:
        member["productivity_score"] = metrics["score"]
        member["productivity_status"] = metrics["status"]
        save_member(member)
    return metrics


def recalculate_all() -> list:
    results = []
    for m in get_all_members():
        r = recalculate_member(m.get("id"))
        results.append(r)
    return results


def get_all_productivity_stats() -> list:
    results = []
    for m in get_all_members():
        metrics = compute_member_productivity(m.get("id"))
        metrics["name"] = m.get("full_name", m.get("name", ""))
        results.append(metrics)
    return results
