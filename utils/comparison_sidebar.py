from __future__ import annotations

from collections.abc import Mapping, Sequence

from ui import SidebarMeta

import streamlit as st

from utils.comparison_profile import comparison_profile_signature, current_comparison_profile_store
from utils.source_display import format_source_caption


DEFAULT_CUSTOM_PRESET_LABEL = "직접 구성"
DEFAULT_GROUP_SLOT_PRESETS = {
    1: "서울 소재 여대",
    2: "주요 경쟁 대학",
    3: DEFAULT_CUSTOM_PRESET_LABEL,
}
DEFAULT_GROUP_PRESETS = {
    "서울 소재 여대": [
        "덕성여자대학교",
        "동덕여자대학교",
        "서울여자대학교",
        "성신여자대학교",
        "숙명여자대학교",
        "이화여자대학교",
    ],
    "주요 경쟁 대학": [
        "건국대학교",
        "경희대학교",
        "고려대학교",
        "국민대학교",
        "광운대학교",
        "서강대학교",
        "성균관대학교",
        "중앙대학교",
        "한양대학교",
    ],
    DEFAULT_CUSTOM_PRESET_LABEL: [],
}


def build_default_group_preset_config(
    custom_preset_label: str = DEFAULT_CUSTOM_PRESET_LABEL,
) -> tuple[dict[int, str], dict[str, list[str]], str]:
    slot_presets = {
        1: "서울 소재 여대",
        2: "주요 경쟁 대학",
        3: custom_preset_label,
    }
    group_presets = {
        "서울 소재 여대": list(DEFAULT_GROUP_PRESETS["서울 소재 여대"]),
        "주요 경쟁 대학": list(DEFAULT_GROUP_PRESETS["주요 경쟁 대학"]),
        custom_preset_label: [],
    }
    return slot_presets, group_presets, custom_preset_label


def build_standard_sidebar_meta(
    *,
    data_updated: str,
    school_count: int,
    year_min: int | str,
    year_max: int | str,
    unit: str,
    data_source: str | None = None,
    source: object | None = None,
    manifest: object | None = None,
) -> tuple[SidebarMeta, ...]:
    meta_lines: list[SidebarMeta] = []
    source_manifest = manifest or source
    if source_manifest is not None:
        source_text = format_source_caption(source_manifest).split(" | ", maxsplit=1)[0]
        meta_lines.append(SidebarMeta(text=source_text.replace("데이터 출처", "데이터 소스", 1)))
    elif data_source:
        source_label = _format_data_source_label(data_source)
        meta_lines.append(SidebarMeta(text=f"데이터 소스: {source_label}"))
    meta_lines.extend(
        [
            SidebarMeta(text=f"업데이트: {data_updated}"),
            SidebarMeta(text=f"대상 학교 수: {school_count}개"),
            SidebarMeta(text=f"기준년도 범위: {year_min} ~ {year_max}"),
            SidebarMeta(text=f"단위: {unit}"),
        ]
    )
    return tuple(meta_lines)


def _format_data_source_label(data_source: str) -> str:
    normalized = data_source.strip().lower()
    if normalized == "api":
        return "data.go.kr API"
    if normalized in {"csv", "local", "local_csv"}:
        return "로컬 CSV"
    return data_source


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
    default_profile_groups: Sequence[tuple[str, Sequence[str]]],
) -> None:
    preset_key, name_key, schools_key, widget_key = _group_state_keys(key_prefix, slot)

    if preset_key in st.session_state:
        normalized = _normalize_group_school_selection(st.session_state.get(schools_key, []), schools)
        st.session_state[schools_key] = normalized
        st.session_state.setdefault(widget_key, normalized)
        return

    if slot <= len(default_profile_groups):
        group_name, group_schools = default_profile_groups[slot - 1]
        normalized = _normalize_group_school_selection(group_schools, schools)
        st.session_state[preset_key] = custom_preset_label
        st.session_state[name_key] = group_name or default_group_name_template.format(slot=slot)
        st.session_state[schools_key] = normalized
        st.session_state[widget_key] = normalized
        return

    st.session_state[preset_key] = custom_preset_label
    st.session_state[name_key] = default_group_name_template.format(slot=slot)
    st.session_state[schools_key] = []
    st.session_state[widget_key] = []


def _reset_group_state_if_profile_changed(
    *,
    key_prefix: str,
    slot_count: int,
    profile_signature: str,
) -> None:
    stamp_key = f"{key_prefix}_comparison_group_profile_signature"
    if st.session_state.get(stamp_key) == profile_signature:
        return

    for slot in range(1, slot_count + 1):
        for state_key in _group_state_keys(key_prefix, slot):
            st.session_state.pop(state_key, None)
    st.session_state[stamp_key] = profile_signature


def _clear_group_state(key_prefix: str, slot_count: int) -> None:
    for slot in range(1, slot_count + 1):
        for state_key in _group_state_keys(key_prefix, slot):
            st.session_state.pop(state_key, None)


def _display_group_title(title: str) -> str:
    return "현재 화면용 비교그룹" if title.strip() == "비교 대상 그룹" else title


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
    try:
        profile = current_comparison_profile_store().load(schools)
        default_profile_groups = tuple((group.name, list(group.schools)) for group in profile.comparison_groups)
        profile_signature = comparison_profile_signature(profile)
    except Exception:
        default_profile_groups = ()
        profile_signature = "comparison-profile-unavailable"
    _reset_group_state_if_profile_changed(
        key_prefix=key_prefix,
        slot_count=slot_count,
        profile_signature=profile_signature,
    )

    with st.sidebar:
        st.divider()
        st.subheader(_display_group_title(title))
        st.caption(caption)
        st.caption("저장된 기본 비교그룹을 기준으로 시작하며, 여기서 바꾼 내용은 현재 화면에만 적용됩니다.")
        if st.button("기본 비교그룹 다시 적용", key=f"{key_prefix}_reset_comparison_groups"):
            _clear_group_state(key_prefix, slot_count)
            st.rerun()

        for slot in range(1, slot_count + 1):
            _ensure_group_state(
                slot,
                schools,
                key_prefix,
                default_slot_presets,
                group_presets,
                custom_preset_label,
                default_group_name_template,
                default_profile_groups,
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
