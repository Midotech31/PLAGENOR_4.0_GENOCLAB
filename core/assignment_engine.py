# core/assignment_engine.py — PLAGENOR 4.0 Assignment Engine
# score = (skill × w) − (load × w) − availability_penalty + productivity_score

from __future__ import annotations
from typing import Optional
import config
from core.repository import get_all_members, get_member, get_requests_by_member, get_service


def compute_member_score(member: dict, service_id: str = "") -> float:
    weights = config.ASSIGNMENT_WEIGHTS
    max_load = member.get("max_load", config.DEFAULT_MAX_LOAD)
    current_load = member.get("current_load", 0)

    # Skill score (0-100) — cross-reference member skills with service requirements
    skills = member.get("skills", [])
    skill_score = 0.0
    if service_id:
        if service_id in skills:
            skill_score = 100.0
        else:
            # Check if member has skills related to the service's required_skills
            svc = get_service(service_id)
            if svc:
                required_skills = svc.get("required_skills", [])
                if required_skills and skills:
                    matched = len(set(skills) & set(required_skills))
                    skill_score = (matched / len(required_skills)) * 80.0 if required_skills else 0.0
                elif not required_skills and service_id in skills:
                    skill_score = 100.0
            # No match at all
    elif not skills:
        skill_score = 50.0

    # Load score (0-100, inverted: lower load = higher score)
    if max_load > 0:
        load_ratio = current_load / max_load
        load_score = max(0, (1 - load_ratio)) * 100
    else:
        load_score = 0.0

    # Availability penalty
    available = member.get("available", True)
    availability_penalty = 0 if available else 50

    # Productivity score
    prod_score = member.get("productivity_score", 50.0)

    # Weighted calculation — skill match weighted most heavily
    score = (
        skill_score * (weights["skill"] / 100)
        + load_score * (weights["load"] / 100)
        + prod_score * (weights["productivity"] / 100)
        - availability_penalty * (weights["availability"] / 100)
    )

    return round(max(0, min(100, score)), 1)


def get_recommended_members(service_id: str = "", limit: int = 5) -> list:
    members = get_all_members()
    scored = []
    for m in members:
        if not m.get("available", True):
            continue
        if m.get("current_load", 0) >= m.get("max_load", config.DEFAULT_MAX_LOAD):
            continue
        score = compute_member_score(m, service_id)
        scored.append({**m, "_score": score})

    scored.sort(key=lambda x: x["_score"], reverse=True)
    return scored[:limit]


def get_member_workload(member_id: str) -> dict:
    member = get_member(member_id)
    if not member:
        return {}
    active = get_requests_by_member(member_id)
    return {
        "member_id": member_id,
        "name": member.get("full_name", member.get("name", "")),
        "current_load": member.get("current_load", 0),
        "max_load": member.get("max_load", config.DEFAULT_MAX_LOAD),
        "active_requests": len(active),
        "available": member.get("available", True),
        "utilization": round(
            member.get("current_load", 0) / max(1, member.get("max_load", config.DEFAULT_MAX_LOAD)) * 100, 1
        ),
    }
