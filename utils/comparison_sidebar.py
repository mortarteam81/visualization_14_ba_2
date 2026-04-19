from __future__ import annotations

from collections.abc import Mapping, Sequence

import streamlit as st


def _normalize_group_school_selection(value: object, schools: Sequence[str]) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        candidates = [value]
    else:
        try:
            candidates = list(value)
        except TypeError:
            candidates = []
    return [school for school in candidates if school in schools]


def _group_state_keys(key_prefix: str, slot: int) -> tuple[str, str, str, str]:
    return (
        f"{key_prefix}_group_preset_{slot}",
        f"{key_prefix}_group_name_{slot}",
        f"{key_prefix}_group_schools_{slot}",
        f"{key_prefix}_group_schools_widget_{slot}",
    )


def _filter_preset_schools(
    schools: Sequence[str],
    preset_name: str,
    group_presets: Mapping[str, Sequence[str]],
) -> list[str]:
    return [school for school in group_presets.get(preset_name, []) if school in schools]


def _apply_group_preset(
    slot: int,
    schools: Sequence[str],
    key_prefix: str,
    group_presets: Mapping[str, Sequence[str]],
    custom_preset_label: str,
    default_group_name_template: str,
) -> None:
    preset_key, name_key, schools_key, widget_key = _group_state_keys(key_prefix, slot)
    preset_name = st.session_state[preset_key]

    if preset_name == custom_preset_label:
        st.session_state[name_key] = st.session_state.get(name_key) or default_group_name_template.format(slot=slot)
        normalized = _normalize_group_school_selection(st.session_state.get(schools_key, []), schools)
        st.session_state[schools_key] = normalized
        st.session_state[widget_key] = normalized
        return

    preset_schools = _filter_preset_schools(schools, preset_name, group_presets)
    st.session_state[name_key] = preset_name
    st.session_state[schools_key] = preset_schools
    st.session_state[widget_key] = preset_schools


def _ensure_group_state(
    slot: int,
    schools: Sequence[str],
    key_prefix: str,
    default_slot_presets: Mapping[int, str],
    group_presets: Mapping[str, Sequence[str]],
    custom_preset_label: str,
    default_group_name_template: str,
) -> None:
    preset_key, name_key, schools_key, widget_key = _group_state_keys(key_prefix, slot)

    if preset_key in st.session_state:
        normalized = _normalize_group_school_selection(st.session_state.get(schools_key, []), schools)
        st.session_state[schools_key] = normalized
        st.session_state.setdefault(widget_key, normalized)
        return

    default_preset = default_slot_presets[slot]
    st.session_state[preset_key] = default_preset
    if default_preset == custom_preset_label:
        st.session_state[name_key] = default_group_name_template.format(slot=slot)
        st.session_state[schools_key] = []
        st.session_state[widget_key] = []
    else:
        preset_schools = _filter_preset_schools(schools, default_preset, group_presets)
        st.session_state[name_key] = default_preset
        st.session_state[schools_key] = preset_schools
        st.session_state[widget_key] = preset_schools


def build_group_definitions(
    schools: Sequence[str],
    *,
    key_prefix: str,
    title: str,
    caption: str,
    group_presets: Mapping[str, Sequence[str]],
    default_slot_presets: Mapping[int, str],
    custom_preset_label: str,
    slot_count: int = 3,
    preset_label: str = "프리셋",
    group_name_label: str = "그룹 이름",
    group_schools_label: str = "그룹 학교",
    preset_help: str = "프리셋을 선택하면 추천 그룹 구성이 자동으로 채워집니다.",
    group_name_help: str = "차트 평균선 이름으로 사용됩니다.",
    group_schools_help: str = "그룹에 포함할 학교를 직접 조정할 수 있습니다.",
    default_group_name_template: str = "그룹 {slot}",
) -> dict[str, list[str]]:
    preset_options = list(group_presets.keys())

    with st.sidebar:
        st.divider()
        st.subheader(title)
        st.caption(caption)

        for slot in range(1, slot_count + 1):
            _ensure_group_state(
                slot,
                schools,
                key_prefix,
                default_slot_presets,
                group_presets,
                custom_preset_label,
                default_group_name_template,
            )
            preset_key, name_key, schools_key, widget_key = _group_state_keys(key_prefix, slot)

            with st.expander(f"그룹 {slot}", expanded=slot == 1):
                st.selectbox(
                    preset_label,
                    options=preset_options,
                    key=preset_key,
                    help=preset_help,
                    on_change=_apply_group_preset,
                    args=(
                        slot,
                        schools,
                        key_prefix,
                        group_presets,
                        custom_preset_label,
                        default_group_name_template,
                    ),
                )
                st.text_input(
                    group_name_label,
                    key=name_key,
                    help=group_name_help,
                )
                selected_group_schools = st.multiselect(
                    group_schools_label,
                    list(schools),
                    default=st.session_state.get(widget_key, st.session_state.get(schools_key, [])),
                    key=widget_key,
                    help=group_schools_help,
                )
                st.session_state[schools_key] = _normalize_group_school_selection(selected_group_schools, schools)

    return {
        st.session_state[_group_state_keys(key_prefix, slot)[1]].strip(): st.session_state[
            _group_state_keys(key_prefix, slot)[2]
        ]
        for slot in range(1, slot_count + 1)
    }
