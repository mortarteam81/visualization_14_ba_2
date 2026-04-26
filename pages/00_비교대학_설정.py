from __future__ import annotations

import streamlit as st

from utils.comparison_profile import (
    ComparisonGroup,
    ComparisonProfile,
    DEFAULT_OWNER_ID,
    DEFAULT_OWNER_TYPE,
    DEFAULT_PROFILE_ID,
    DEFAULT_PROFILE_NAME,
    FileComparisonProfileStore,
    MAX_COMPARISON_GROUPS,
    MAX_COMPARISON_SCHOOLS,
    default_comparison_profile,
    normalize_comparison_profile,
)
from utils.config import APP_ICON, APP_SUBTITLE
from utils.management_insights import build_management_insight_dataset
from utils.theme import apply_app_theme


BASE_SCHOOL_KEY = "comparison_profile_base_school"
COMPARISON_SCHOOLS_KEY = "comparison_profile_comparison_schools"
NOTICE_KEY = "comparison_profile_notice"
RELOAD_WIDGETS_KEY = "comparison_profile_reload_widgets"


def _group_name_key(slot: int) -> str:
    return f"comparison_profile_group_name_{slot}"


def _group_schools_key(slot: int) -> str:
    return f"comparison_profile_group_schools_{slot}"


def _load_school_options() -> list[str]:
    dataset = build_management_insight_dataset()
    return sorted(dataset.long["school_name"].dropna().unique())


def _ensure_widget_state(profile: ComparisonProfile, school_options: list[str]) -> None:
    if st.session_state.pop(RELOAD_WIDGETS_KEY, False):
        st.session_state.pop(BASE_SCHOOL_KEY, None)
        st.session_state.pop(COMPARISON_SCHOOLS_KEY, None)
        for slot in range(1, MAX_COMPARISON_GROUPS + 1):
            st.session_state.pop(_group_name_key(slot), None)
            st.session_state.pop(_group_schools_key(slot), None)

    if COMPARISON_SCHOOLS_KEY not in st.session_state:
        st.session_state[COMPARISON_SCHOOLS_KEY] = list(profile.comparison_schools)

    if st.session_state.get(BASE_SCHOOL_KEY) not in school_options:
        st.session_state.pop(BASE_SCHOOL_KEY, None)

    for slot in range(1, MAX_COMPARISON_GROUPS + 1):
        group = profile.comparison_groups[slot - 1] if slot <= len(profile.comparison_groups) else None
        name_key = _group_name_key(slot)
        schools_key = _group_schools_key(slot)
        if name_key not in st.session_state:
            st.session_state[name_key] = group.name if group else f"비교 그룹 {slot}"
        if schools_key not in st.session_state:
            st.session_state[schools_key] = list(group.schools) if group else []
        _clean_group_state(slot, school_options)


def _clean_comparison_state(base_school: str, comparison_options: list[str]) -> None:
    current = st.session_state.get(COMPARISON_SCHOOLS_KEY, [])
    if isinstance(current, str):
        current = [current]
    allowed = set(comparison_options)
    cleaned: list[str] = []
    for school in current:
        if school == base_school or school not in allowed or school in cleaned:
            continue
        cleaned.append(school)
        if len(cleaned) >= MAX_COMPARISON_SCHOOLS:
            break
    st.session_state[COMPARISON_SCHOOLS_KEY] = cleaned


def _clean_group_state(slot: int, school_options: list[str]) -> None:
    key = _group_schools_key(slot)
    current = st.session_state.get(key, [])
    if isinstance(current, str):
        current = [current]
    allowed = set(school_options)
    cleaned: list[str] = []
    for school in current:
        if school not in allowed or school in cleaned:
            continue
        cleaned.append(school)
    st.session_state[key] = cleaned


def _profile_groups_from_selection() -> tuple[ComparisonGroup, ...]:
    groups: list[ComparisonGroup] = []
    for slot in range(1, MAX_COMPARISON_GROUPS + 1):
        name = str(st.session_state.get(_group_name_key(slot), "")).strip() or f"비교 그룹 {slot}"
        schools = tuple(st.session_state.get(_group_schools_key(slot), []))
        if not schools:
            continue
        groups.append(ComparisonGroup(name=name, schools=schools))
    return tuple(groups)


def _profile_from_selection(
    base_school: str,
    comparison_schools: list[str],
    comparison_groups: tuple[ComparisonGroup, ...],
) -> ComparisonProfile:
    return ComparisonProfile(
        profile_id=DEFAULT_PROFILE_ID,
        profile_name=DEFAULT_PROFILE_NAME,
        owner_type=DEFAULT_OWNER_TYPE,
        owner_id=DEFAULT_OWNER_ID,
        base_school=base_school,
        comparison_schools=tuple(comparison_schools),
        comparison_groups=comparison_groups,
        is_default=True,
        updated_at="",
    )


st.set_page_config(
    page_title="비교대학 설정 | 교육 여건 지표",
    page_icon=APP_ICON,
    layout="wide",
)
apply_app_theme()

st.title("비교대학 설정")
st.caption(APP_SUBTITLE)

school_options = _load_school_options()
if not school_options:
    st.error("비교대학 설정에 사용할 학교 목록을 찾지 못했습니다.")
    st.stop()

store = FileComparisonProfileStore()
profile = store.load(school_options)
_ensure_widget_state(profile, school_options)

notice = st.session_state.pop(NOTICE_KEY, None)
if notice:
    st.success(notice)

st.info("이 화면에서 저장한 값은 앱 전체의 기본 비교군으로 사용됩니다. 각 사용자가 다른 화면에서 바꾼 선택은 해당 세션에만 적용됩니다.")

if st.session_state.get(BASE_SCHOOL_KEY) in school_options:
    base_school = st.selectbox("기준대학", school_options, key=BASE_SCHOOL_KEY)
else:
    base_index = school_options.index(profile.base_school)
    base_school = st.selectbox(
        "기준대학",
        school_options,
        index=base_index,
        key=BASE_SCHOOL_KEY,
    )

comparison_options = [school for school in school_options if school != base_school]
_clean_comparison_state(base_school, comparison_options)
comparison_schools = st.multiselect(
    "비교대학",
    comparison_options,
    key=COMPARISON_SCHOOLS_KEY,
    max_selections=MAX_COMPARISON_SCHOOLS,
)

if len(comparison_schools) < 3:
    st.warning("비교대학은 3개 이상을 권장합니다. 저장은 가능하지만 비교 평균의 대표성이 약해질 수 있습니다.")

st.markdown("### 비교 대상 그룹")
st.caption("선택 사항입니다. 저장한 그룹은 각 지표 페이지의 비교 대상 그룹 기본값으로 적용됩니다.")

for slot in range(1, MAX_COMPARISON_GROUPS + 1):
    with st.expander(f"그룹 {slot}", expanded=slot == 1):
        st.text_input(
            "그룹 이름",
            key=_group_name_key(slot),
            help="각 지표 페이지의 그룹 평균선 이름으로 사용됩니다.",
        )
        _clean_group_state(slot, school_options)
        st.multiselect(
            "그룹 학교",
            school_options,
            key=_group_schools_key(slot),
            help="그룹을 사용하지 않으려면 학교를 선택하지 않은 상태로 두면 됩니다.",
        )

comparison_groups = _profile_groups_from_selection()
preview_profile = normalize_comparison_profile(
    _profile_from_selection(base_school, comparison_schools, comparison_groups),
    school_options,
)

summary_col1, summary_col2, summary_col3 = st.columns(3)
summary_col1.metric("기준대학", preview_profile.base_school)
summary_col2.metric("비교대학", f"{len(preview_profile.comparison_schools)}개")
summary_col3.metric("비교 그룹", f"{len(preview_profile.comparison_groups)}개")

st.dataframe(
    [
        {"구분": "기준대학", "학교명": preview_profile.base_school},
        *[
            {"구분": f"비교대학 {index}", "학교명": school}
            for index, school in enumerate(preview_profile.comparison_schools, start=1)
        ],
        *[
            {"구분": group.name, "학교명": ", ".join(group.schools)}
            for group in preview_profile.comparison_groups
        ],
    ],
    use_container_width=True,
    hide_index=True,
)

button_col1, button_col2 = st.columns([1, 1])
with button_col1:
    if st.button("저장", type="primary", use_container_width=True):
        store.save(preview_profile, school_options)
        st.session_state[NOTICE_KEY] = "운영자 기본 비교군을 저장했습니다."
        st.session_state[RELOAD_WIDGETS_KEY] = True
        st.rerun()

with button_col2:
    if st.button("기본값 복원", use_container_width=True):
        store.save(default_comparison_profile(school_options), school_options)
        st.session_state[NOTICE_KEY] = "기본 비교군으로 복원했습니다."
        st.session_state[RELOAD_WIDGETS_KEY] = True
        st.rerun()

if profile.updated_at:
    st.caption(f"마지막 저장: {profile.updated_at}")
else:
    st.caption("저장된 로컬 설정이 없어 기본 비교군을 사용 중입니다.")
