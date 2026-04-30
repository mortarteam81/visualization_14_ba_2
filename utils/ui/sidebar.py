"""Sidebar rendering helpers for Streamlit metric pages."""

from __future__ import annotations

from typing import Any, Sequence

import streamlit as st

from utils.comparison_profile import (
    comparison_profile_signature,
    current_comparison_profile_store,
    default_selected_schools,
    selected_schools_from_profile,
)
from utils.theme import is_mobile_compact_mode

from .models import SidebarConfig


def _normalize_school_selection(value: object, schools: Sequence[str]) -> list[str]:
    if isinstance(value, str):
        candidates = [value]
    else:
        try:
            candidates = list(value or [])
        except TypeError:
            candidates = []
    allowed = set(schools)
    return [school for school in candidates if school in allowed]


def _profile_defaults(
    schools: Sequence[str],
    fallback_selection: Sequence[str],
) -> tuple[list[str], str]:
    try:
        profile = current_comparison_profile_store().load(schools)
        selected = selected_schools_from_profile(profile, schools)
        signature = comparison_profile_signature(profile)
    except Exception:
        selected = []
        signature = "comparison-profile-unavailable"

    if selected:
        return selected, signature
    return default_selected_schools(schools, fallback=fallback_selection), signature


def _comparison_school_label(label: str) -> str:
    if label.strip() in {"학교 선택", "비교 학교", "비교 학교 선택"}:
        return "현재 화면에 표시할 학교"
    return label


def _format_school_summary(schools: Sequence[str], *, limit: int = 4) -> str:
    selected = list(schools)
    if not selected:
        return "저장된 비교대학이 없어 기본 학교만 표시됩니다."
    visible = ", ".join(selected[:limit])
    if len(selected) <= limit:
        return visible
    return f"{visible} 외 {len(selected) - limit}개교"


def render_school_sidebar(
    *,
    schools: Sequence[str],
    key_prefix: str | None = None,
    default_schools: Sequence[str] | None = None,
    config: SidebarConfig | None = None,
) -> dict[str, Any]:
    """Render the common sidebar controls and return selected values."""

    sidebar_config = config or SidebarConfig()
    fallback_selection = list(default_schools or schools[:1])
    default_selection, profile_signature = _profile_defaults(schools, fallback_selection)
    school_help = sidebar_config.school_help or f"Choose from {len(schools)} schools."
    school_label = _comparison_school_label(sidebar_config.school_label)
    selection_key = f"{key_prefix}_selected_schools" if key_prefix else None
    profile_stamp_key = f"{key_prefix}_comparison_profile_signature" if key_prefix else None
    reset_key = f"{key_prefix}_reset_comparison_profile" if key_prefix else None
    values: dict[str, Any] = {}
    mobile_compact = is_mobile_compact_mode()

    if mobile_compact and sidebar_config.show_profile_controls:
        st.info(f"기본 비교군 적용 중: {_format_school_summary(default_selection)}")
        st.link_button("비교대학 설정에서 변경", "/비교대학_설정")

    if selection_key and profile_stamp_key:
        if st.session_state.get(profile_stamp_key) != profile_signature:
            st.session_state.pop(selection_key, None)
            st.session_state[profile_stamp_key] = profile_signature
        if selection_key not in st.session_state:
            st.session_state[selection_key] = list(default_selection)
        else:
            st.session_state[selection_key] = _normalize_school_selection(
                st.session_state[selection_key],
                schools,
            )

    with st.sidebar:
        if not mobile_compact:
            st.header(sidebar_config.header)
        if sidebar_config.show_profile_controls and not mobile_compact:
            st.caption(sidebar_config.profile_notice)
            if selection_key and reset_key and st.button(sidebar_config.profile_reset_label, key=reset_key):
                st.session_state[selection_key] = list(default_selection)

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

        if mobile_compact:
            values["selected_schools"] = list(default_selection)
        elif selection_key:
            values["selected_schools"] = st.multiselect(
                school_label,
                list(schools),
                key=selection_key,
                help=school_help,
            )
        else:
            values["selected_schools"] = st.multiselect(
                school_label,
                list(schools),
                default=default_selection,
                help=school_help,
            )

        if sidebar_config.divider_after_controls and sidebar_config.meta_lines:
            st.divider()

        for meta in sidebar_config.meta_lines:
            st.caption(meta.text)

    return values
