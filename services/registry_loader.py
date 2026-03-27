# services/registry_loader.py — PLAGENOR 4.0 Service Registry Loader
# Loads and validates all YAML service definitions.

from __future__ import annotations
import os
from pathlib import Path
from typing import Optional
import yaml
import streamlit as st


def _get_registry_dir() -> Path:
    base = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return base / "services" / "registry"

SUPPORTED_PARAM_TYPES = {"string", "text", "integer", "float", "enum", "boolean"}
SUPPORTED_PRICING_MODELS = {"per_sample_table_row_with_multiplier", "per_sample_fixed"}


@st.cache_data(ttl=300)
def _load_registry_from_disk() -> dict:
    """Internal cached loader for YAML service definitions."""
    registry_dir = _get_registry_dir()
    services = {}
    if not registry_dir.exists():
        return services
    for yaml_file in sorted(registry_dir.glob("*.yaml")):
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict):
                continue
            code = data.get("service_code", "")
            if code and code not in services:
                services[code] = data
        except Exception as e:
            print(f"Registry load error ({yaml_file.name}): {e}")
    return services


def load_service_registry(force_reload: bool = False) -> dict:
    """Load all YAML service definitions. Returns {service_code: definition}."""
    if force_reload:
        _load_registry_from_disk.clear()
    return _load_registry_from_disk()


def get_service_def(service_code: str) -> Optional[dict]:
    """Get a single service definition by code."""
    return load_service_registry().get(service_code)


def get_all_service_codes() -> list[str]:
    """Get sorted list of all service codes."""
    return sorted(load_service_registry().keys())


def get_service_parameters(service_code: str) -> list[dict]:
    """Get the parameters list for a service."""
    svc = get_service_def(service_code)
    return svc.get("parameters", []) if svc else []


def get_sample_table_schema(service_code: str) -> Optional[dict]:
    """Get sample table schema for a service."""
    svc = get_service_def(service_code)
    if not svc:
        return None
    table = svc.get("sample_table")
    if table and table.get("enabled", False):
        return table
    return None


def get_requester_fields(service_code: str) -> list[dict]:
    """Get requester fields for a service (common across all services)."""
    svc = get_service_def(service_code)
    if not svc:
        return _default_requester_fields()
    return svc.get("requester_fields", _default_requester_fields())


def save_service_yaml(service_code: str, data: dict) -> bool:
    """Save a service definition back to its YAML file."""
    registry_dir = _get_registry_dir()
    if not registry_dir.exists():
        registry_dir.mkdir(parents=True, exist_ok=True)
    filepath = registry_dir / f"{service_code}.yaml"
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        _load_registry_from_disk.clear()
        return True
    except Exception:
        return False


def get_all_yaml_files() -> list[dict]:
    """List all YAML files in the registry directory with metadata."""
    registry_dir = _get_registry_dir()
    results = []
    if not registry_dir.exists():
        return results
    for yaml_file in sorted(registry_dir.glob("*.yaml")):
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if isinstance(data, dict):
                results.append({
                    "filename": yaml_file.name,
                    "filepath": str(yaml_file),
                    "service_code": data.get("service_code", ""),
                    "service_name": data.get("service_name", data.get("name", "")),
                    "data": data,
                })
        except Exception:
            continue
    return results


def _default_requester_fields() -> list[dict]:
    return [
        {"name": "full_name", "label": "Nom et prénom", "type": "string", "required": True},
        {"name": "institution", "label": "Université / École", "type": "string", "required": True},
        {"name": "laboratory", "label": "Laboratoire", "type": "string", "required": True},
        {"name": "status", "label": "Fonction / Poste", "type": "string", "required": True},
        {"name": "phone", "label": "Numéro de téléphone", "type": "string", "required": True},
        {"name": "email", "label": "Adresse e-mail", "type": "string", "required": True},
        {"name": "supervisor", "label": "Directeur de recherche", "type": "string", "required": True},
    ]
