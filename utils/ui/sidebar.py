"""Sidebar rendering helpers for Streamlit metric pages."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import streamlit as st

from utils.comparison_profile import default_selected_schools

from .models import SidebarConfig


def render_school_sidebar(
    *,
    schools: Sequence[str],
    default_schools: Sequence[str] | None = None,
    config: SidebarConfig | None = None,
) -> dict[str, Any]:
    """Render the common sidebar controls and return selected values."""

    sidebar_config = config or SidebarConfig()
    fallback_selection = list(default_schools or schools[:1])
    default_selection = default_selected_schools(schools, fallback=fallback_selection)
    school_help = sidebar_config.school_help or f"Choose from {len(schools)} schools."
    values: dict[str, Any] = {}

    with st.sidebar:
        st.header(sidebar_config.header)

        for toggle in sidebar_config.toggles:
            values[toggle.key] = st.toggle(
                toggle.label,
                value=toggle.value,
                help=toggle.help,
            )

        for radio in sidebar_config.radios:
            values[radio.key] = st.radio(
                radio.label,
                options=list(radio.options),
                index=radio.index,
                help=radio.help,
                horizontal=radio.horizontal,
            )

        values["selected_schools"] = st.multiselect(
            sidebar_config.school_label,
            list(schools),
            default=default_selection,
            help=school_help,
        )

        if sidebar_config.divider_after_controls and sidebar_config.meta_lines:
            st.divider()

        for meta in sidebar_config.meta_lines:
            st.caption(meta.text)

    return values
