# services/form_renderer.py — PLAGENOR 4.0 Dynamic Form Renderer
# Renders Streamlit forms from YAML service registry definitions.

from __future__ import annotations
import uuid
import streamlit as st
from typing import Optional


def render_requester_form(fields: list, prefix: str = "req") -> dict:
    """Render requester information fields. Returns dict of values."""
    data = {}
    for field in fields:
        name = field["name"]
        label = field.get("label", name)
        required = field.get("required", False)
        key = f"{prefix}__{name}"

        value = st.text_input(f"{label}{' *' if required else ''}", key=key)
        data[name] = value.strip() if value else ""

    return data


def render_service_params(service_def: dict, prefix: str = "svc") -> dict:
    """Render service-specific parameters from YAML definition. Returns dict."""
    params = {}
    parameters = service_def.get("parameters", [])

    for field in parameters:
        name = field["name"]
        label = field.get("label", name)
        ftype = field["type"]
        required = field.get("required", False)
        help_text = field.get("help", "")
        key = f"{prefix}__{service_def.get('service_code', '')}_{name}"

        value = None

        if ftype == "enum":
            options = field.get("options", [])
            if options:
                display = (["— Sélectionner —"] + options) if required else [""] + options
                value = st.selectbox(f"{label}{' *' if required else ''}",
                                     display, help=help_text, key=key)
                if value in ("", "— Sélectionner —"):
                    value = None

        elif ftype == "boolean":
            value = st.radio(f"{label}{' *' if required else ''}",
                            ["Oui", "Non"], horizontal=True, help=help_text, key=key)
            value = True if value == "Oui" else False

        elif ftype == "integer":
            min_val = int(field.get("min", 0))
            value = st.number_input(f"{label}{' *' if required else ''}",
                                    min_value=min_val, step=1, help=help_text, key=key)

        elif ftype == "float":
            value = st.number_input(f"{label}{' *' if required else ''}",
                                    step=0.1, help=help_text, key=key)

        elif ftype in ("string", "text"):
            if ftype == "text":
                value = st.text_area(f"{label}{' *' if required else ''}",
                                     help=help_text, key=key)
            else:
                value = st.text_input(f"{label}{' *' if required else ''}",
                                      help=help_text, key=key)
            value = value.strip() if value else None

        params[name] = value

    return params


def render_sample_table(service_def: dict) -> list:
    """
    Render a dynamic sample table from YAML schema.
    Returns list of sample dicts.
    """
    schema = service_def.get("sample_table")
    if not schema or not schema.get("enabled", False):
        return []

    columns = schema.get("columns", [])
    if not columns:
        return []

    min_rows = int(schema.get("min_rows", 1))
    svc_code = service_def.get("service_code", "")

    # Session key for this service's samples
    session_key = f"samples_{svc_code}"
    if session_key not in st.session_state:
        st.session_state[session_key] = []

    samples = st.session_state[session_key]

    # Add/remove actions via session_state flags to avoid Streamlit rerun issues
    add_key = f"add_sample_flag_{svc_code}"
    remove_key = f"remove_sample_flag_{svc_code}"

    # Process pending add/remove actions from previous run
    if st.session_state.get(add_key):
        samples.append({"_id": str(uuid.uuid4())[:8]})
        st.session_state[session_key] = samples
        st.session_state[add_key] = False

    if st.session_state.get(remove_key):
        sid_to_remove = st.session_state[remove_key]
        st.session_state[session_key] = [s for s in samples if s.get("_id") != sid_to_remove]
        samples = st.session_state[session_key]
        st.session_state[remove_key] = ""

    # Add sample button
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(f"**Échantillons** (minimum {min_rows})")
    with c2:
        if st.button("➕ Ajouter", key=f"add_sample_{svc_code}"):
            st.session_state[add_key] = True
            st.rerun()

    if not samples:
        st.info(f"Cliquez sur ➕ pour ajouter au moins {min_rows} échantillon(s).")
        return []

    # Render each sample
    for idx, sample in enumerate(samples):
        sid = sample.get("_id", str(idx))
        with st.expander(f"Échantillon #{idx + 1}", expanded=True):
            cols_per_row = min(3, len(columns))
            col_groups = [columns[i:i+cols_per_row] for i in range(0, len(columns), cols_per_row)]

            for group in col_groups:
                ui_cols = st.columns(len(group))
                for ci, col_def in enumerate(group):
                    with ui_cols[ci]:
                        cname = col_def["name"]
                        clabel = col_def.get("label", cname)
                        ctype = col_def.get("type", "string")
                        creq = col_def.get("required", False)
                        ckey = f"s_{svc_code}_{sid}_{cname}"

                        if ctype == "enum":
                            opts = col_def.get("options", [])
                            val = st.selectbox(f"{clabel}{' *' if creq else ''}",
                                              [""] + opts, key=ckey)
                            sample[cname] = val if val else None
                        elif ctype == "boolean":
                            val = st.checkbox(f"{clabel}", key=ckey)
                            sample[cname] = val
                        elif ctype == "integer":
                            val = st.number_input(f"{clabel}{' *' if creq else ''}",
                                                  min_value=0, step=1, key=ckey)
                            sample[cname] = val
                        else:
                            val = st.text_input(f"{clabel}{' *' if creq else ''}",
                                               value=sample.get(cname, "") or "", key=ckey)
                            sample[cname] = val.strip() if val else None

            if st.button("🗑️ Supprimer", key=f"rm_{svc_code}_{sid}"):
                st.session_state[remove_key] = sid
                st.rerun()

    # Validation
    if len(samples) < min_rows:
        st.warning(f"Au moins {min_rows} échantillon(s) requis.")

    return samples


def validate_required_fields(params: dict, service_def: dict) -> list:
    """Check required fields. Returns list of error messages."""
    errors = []
    for field in service_def.get("parameters", []):
        if field.get("required") and not params.get(field["name"]):
            errors.append(f"« {field.get('label', field['name'])} » est obligatoire.")
    return errors
