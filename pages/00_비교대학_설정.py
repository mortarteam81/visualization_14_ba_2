from __future__ import annotations

from collections.abc import Callable

import streamlit as st

from utils.analysis_scope import load_default_analysis_scope
from utils.app_db import (
    AppDatabaseError,
    AppUserStore,
    ROLE_ADMIN,
    ROLE_VIEWER,
    normalize_email,
    streamlit_session_scope,
)
from utils.auth import initial_admin_emails_from_secrets, require_authenticated_user
from utils.comparison_profile import (
    ComparisonGroup,
    ComparisonProfile,
    MAX_COMPARISON_GROUPS,
    MAX_COMPARISON_SCHOOLS,
    default_comparison_profile,
    normalize_comparison_profile,
)
from utils.config import APP_ICON, APP_SUBTITLE
from utils.management_insights import build_management_insight_dataset
from utils.profile_db import DatabaseComparisonProfileStore
from utils.theme import apply_app_theme


NOTICE_SUFFIX = "notice"
RELOAD_WIDGETS_SUFFIX = "reload_widgets"


def _base_school_key(prefix: str) -> str:
    return f"{prefix}_base_school"


def _comparison_schools_key(prefix: str) -> str:
    return f"{prefix}_comparison_schools"


def _notice_key(prefix: str) -> str:
    return f"{prefix}_{NOTICE_SUFFIX}"


def _reload_widgets_key(prefix: str) -> str:
    return f"{prefix}_{RELOAD_WIDGETS_SUFFIX}"


def _group_name_key(prefix: str, slot: int) -> str:
    return f"{prefix}_group_name_{slot}"


def _group_schools_key(prefix: str, slot: int) -> str:
    return f"{prefix}_group_schools_{slot}"


def _load_school_options() -> list[str]:
    dataset = build_management_insight_dataset()
    return _filter_default_scope_school_options(dataset.long["school_name"].dropna().unique())


def _filter_default_scope_school_options(available_schools: list[str]) -> list[str]:
    available = {str(school).strip() for school in available_schools if str(school).strip()}
    scoped_schools = [
        str(school.get("school_name", "")).strip()
        for school in load_default_analysis_scope().get("schools", [])
        if isinstance(school, dict)
    ]
    scoped_options = [school for school in scoped_schools if school and school in available]
    return sorted(scoped_options or available)


def _clean_group_state(prefix: str, slot: int, school_options: list[str]) -> None:
    key = _group_schools_key(prefix, slot)
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


def _ensure_widget_state(profile: ComparisonProfile, school_options: list[str], prefix: str) -> None:
    if st.session_state.pop(_reload_widgets_key(prefix), False):
        st.session_state.pop(_base_school_key(prefix), None)
        st.session_state.pop(_comparison_schools_key(prefix), None)
        for slot in range(1, MAX_COMPARISON_GROUPS + 1):
            st.session_state.pop(_group_name_key(prefix, slot), None)
            st.session_state.pop(_group_schools_key(prefix, slot), None)

    if _comparison_schools_key(prefix) not in st.session_state:
        st.session_state[_comparison_schools_key(prefix)] = list(profile.comparison_schools)

    if st.session_state.get(_base_school_key(prefix)) not in school_options:
        st.session_state.pop(_base_school_key(prefix), None)

    for slot in range(1, MAX_COMPARISON_GROUPS + 1):
        group = profile.comparison_groups[slot - 1] if slot <= len(profile.comparison_groups) else None
        name_key = _group_name_key(prefix, slot)
        schools_key = _group_schools_key(prefix, slot)
        if name_key not in st.session_state:
            st.session_state[name_key] = group.name if group else f"비교 그룹 {slot}"
        if schools_key not in st.session_state:
            st.session_state[schools_key] = list(group.schools) if group else []
        _clean_group_state(prefix, slot, school_options)


def _clean_comparison_state(prefix: str, base_school: str, comparison_options: list[str]) -> None:
    key = _comparison_schools_key(prefix)
    current = st.session_state.get(key, [])
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
    st.session_state[key] = cleaned


def _profile_groups_from_selection(prefix: str) -> tuple[ComparisonGroup, ...]:
    groups: list[ComparisonGroup] = []
    for slot in range(1, MAX_COMPARISON_GROUPS + 1):
        name = str(st.session_state.get(_group_name_key(prefix, slot), "")).strip() or f"비교 그룹 {slot}"
        schools = tuple(st.session_state.get(_group_schools_key(prefix, slot), []))
        if schools:
            groups.append(ComparisonGroup(name=name, schools=schools))
    return tuple(groups)


def _profile_from_selection(
    *,
    base_school: str,
    comparison_schools: list[str],
    comparison_groups: tuple[ComparisonGroup, ...],
    profile_name: str,
) -> ComparisonProfile:
    return ComparisonProfile(
        profile_id="draft",
        profile_name=profile_name,
        owner_type="draft",
        owner_id="draft",
        base_school=base_school,
        comparison_schools=tuple(comparison_schools),
        comparison_groups=comparison_groups,
        is_default=True,
        updated_at="",
    )


def _render_profile_editor(
    *,
    prefix: str,
    title: str,
    caption: str,
    profile_name: str,
    store: DatabaseComparisonProfileStore,
    school_options: list[str],
    save_notice: str,
    restore_notice: str,
    restore_profile: Callable[[], ComparisonProfile] | None = None,
    restore_action: Callable[[], None] | None = None,
) -> None:
    st.subheader(title)
    st.caption(caption)
    st.info(
        "선택 후보는 기본 분석 범위인 서울 소재 사립 일반대학(4년제) 본교/기존 학교로 제한됩니다."
    )

    try:
        profile = store.load(school_options)
    except AppDatabaseError:
        st.error("비교군 설정을 불러오지 못했습니다. Neon DB 연결을 확인해 주세요.")
        return

    _ensure_widget_state(profile, school_options, prefix)

    notice = st.session_state.pop(_notice_key(prefix), None)
    if notice:
        st.success(notice)

    base_key = _base_school_key(prefix)
    comparison_key = _comparison_schools_key(prefix)

    if st.session_state.get(base_key) in school_options:
        base_school = st.selectbox("기준대학", school_options, key=base_key)
    else:
        base_index = school_options.index(profile.base_school)
        base_school = st.selectbox("기준대학", school_options, index=base_index, key=base_key)

    comparison_options = [school for school in school_options if school != base_school]
    _clean_comparison_state(prefix, base_school, comparison_options)
    comparison_schools = st.multiselect(
        "기본 비교대학",
        comparison_options,
        key=comparison_key,
        max_selections=MAX_COMPARISON_SCHOOLS,
    )

    if len(comparison_schools) < 3:
        st.warning("비교대학은 3개 이상을 권장합니다. 저장은 가능하지만 비교 평균의 대표성이 약해질 수 있습니다.")

    st.markdown("### 기본 비교그룹")
    st.caption("각 지표 화면은 이 설정을 시작값으로 불러오며, 지표 화면에서 바꾼 값은 현재 화면에만 적용됩니다.")
    for slot in range(1, MAX_COMPARISON_GROUPS + 1):
        with st.expander(f"그룹 {slot}", expanded=slot == 1):
            st.text_input(
                "그룹 이름",
                key=_group_name_key(prefix, slot),
                help="각 지표 페이지의 기본 그룹 평균선 이름으로 사용됩니다.",
            )
            _clean_group_state(prefix, slot, school_options)
            st.multiselect(
                "그룹 학교",
                school_options,
                key=_group_schools_key(prefix, slot),
                help="기본 그룹을 사용하지 않으려면 학교를 선택하지 않은 상태로 두면 됩니다.",
            )

    comparison_groups = _profile_groups_from_selection(prefix)
    preview_profile = normalize_comparison_profile(
        _profile_from_selection(
            base_school=base_school,
            comparison_schools=comparison_schools,
            comparison_groups=comparison_groups,
            profile_name=profile_name,
        ),
        school_options,
    )

    summary_col1, summary_col2, summary_col3 = st.columns(3)
    summary_col1.metric("기준대학", preview_profile.base_school)
    summary_col2.metric("기본 비교대학", f"{len(preview_profile.comparison_schools)}개")
    summary_col3.metric("기본 비교그룹", f"{len(preview_profile.comparison_groups)}개")

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
        if st.button("저장", type="primary", use_container_width=True, key=f"{prefix}_save"):
            try:
                store.save(preview_profile, school_options)
            except AppDatabaseError:
                st.error("비교군 설정을 저장하지 못했습니다. Neon DB 연결을 확인해 주세요.")
                return
            st.session_state[_notice_key(prefix)] = save_notice
            st.session_state[_reload_widgets_key(prefix)] = True
            st.rerun()

    with button_col2:
        if st.button("기본값 적용", use_container_width=True, key=f"{prefix}_restore"):
            try:
                if restore_action is not None:
                    restore_action()
                elif restore_profile is not None:
                    store.save(restore_profile(), school_options)
            except AppDatabaseError:
                st.error("기본 비교군을 적용하지 못했습니다. Neon DB 연결을 확인해 주세요.")
                return
            st.session_state[_notice_key(prefix)] = restore_notice
            st.session_state[_reload_widgets_key(prefix)] = True
            st.rerun()

    if profile.updated_at:
        st.caption(f"마지막 저장: {profile.updated_at}")
    else:
        st.caption("저장된 설정이 없어 기본 비교군을 사용 중입니다.")


def _role_label(role: str) -> str:
    return "운영자" if role == ROLE_ADMIN else "조회 사용자"


def _render_user_management(auth_email: str, initial_admin_emails: tuple[str, ...]) -> None:
    st.subheader("사용자 관리")
    st.caption("접근 허용 이메일을 등록하고, 기존 사용자의 표시 이름, 권한, 활성 상태를 관리합니다.")
    user_store = AppUserStore(streamlit_session_scope)

    try:
        users = user_store.list_users()
    except AppDatabaseError:
        st.error("사용자 목록을 불러오지 못했습니다. Neon DB 연결을 확인해 주세요.")
        return

    st.dataframe(
        [
            {
                "이메일": user.email,
                "표시 이름": user.display_name,
                "권한": _role_label(user.role),
                "활성": "예" if user.is_active else "아니오",
                "마지막 로그인": user.last_login_at,
            }
            for user in users
        ],
        use_container_width=True,
        hide_index=True,
    )

    with st.form("add_or_update_user_form"):
        st.markdown("### 사용자 추가")
        st.caption("Google 로그인에 사용할 이메일 주소를 등록합니다.")
        new_email = st.text_input("이메일", key="new_user_email")
        new_display_name = st.text_input("표시 이름", key="new_user_display_name")
        new_role = st.selectbox("권한", [ROLE_VIEWER, ROLE_ADMIN], format_func=_role_label, key="new_user_role")
        new_is_active = st.checkbox("활성", value=True, key="new_user_is_active")
        submitted = st.form_submit_button("사용자 저장", type="primary")
        if submitted:
            try:
                user_store.upsert_user(
                    email=new_email,
                    display_name=new_display_name,
                    role=new_role,
                    is_active=new_is_active,
                )
            except ValueError:
                st.error("이메일을 입력해 주세요.")
            except AppDatabaseError:
                st.error("사용자를 저장하지 못했습니다. Neon DB 연결을 확인해 주세요.")
            else:
                st.success("사용자를 저장했습니다.")
                st.rerun()

    if not users:
        return

    selected_email = st.selectbox("수정할 사용자", [user.email for user in users], key="edit_user_email")
    selected_user = next(user for user in users if user.email == selected_email)
    is_initial_admin = selected_user.email in initial_admin_emails
    is_self = selected_user.email == normalize_email(auth_email)

    with st.form("edit_existing_user_form"):
        st.markdown("### 기존 사용자 수정")
        st.caption("초기 운영자와 현재 로그인한 본인의 권한 및 활성 상태는 보호됩니다.")
        display_name = st.text_input("표시 이름", value=selected_user.display_name, key="edit_user_display_name")
        role = st.selectbox(
            "권한",
            [ROLE_VIEWER, ROLE_ADMIN],
            index=[ROLE_VIEWER, ROLE_ADMIN].index(selected_user.role),
            format_func=_role_label,
            key="edit_user_role",
            disabled=is_initial_admin or is_self,
        )
        is_active = st.checkbox(
            "활성",
            value=selected_user.is_active,
            key="edit_user_is_active",
            disabled=is_initial_admin or is_self,
        )
        submitted = st.form_submit_button("변경 저장")
        if submitted:
            next_role = ROLE_ADMIN if is_initial_admin else selected_user.role if is_self else role
            next_is_active = True if is_initial_admin or is_self else is_active
            try:
                user_store.upsert_user(
                    email=selected_user.email,
                    display_name=display_name,
                    role=next_role,
                    is_active=next_is_active,
                )
            except AppDatabaseError:
                st.error("사용자 변경사항을 저장하지 못했습니다. Neon DB 연결을 확인해 주세요.")
            else:
                st.success("사용자 변경사항을 저장했습니다.")
                st.rerun()


st.set_page_config(
    page_title="기본 비교군 설정 | 교육 여건 지표",
    page_icon=APP_ICON,
    layout="wide",
)
auth_user = require_authenticated_user()
apply_app_theme()

st.title("기본 비교군 설정")
st.caption(APP_SUBTITLE)

school_options = _load_school_options()
if not school_options:
    st.error("기본 비교군 설정에 사용할 학교 목록을 찾지 못했습니다.")
    st.stop()

user_profile_store = DatabaseComparisonProfileStore.for_user(auth_user.email)
system_profile_store = DatabaseComparisonProfileStore.for_system()
initial_admin_emails = initial_admin_emails_from_secrets()

if auth_user.is_admin:
    my_tab, system_tab, users_tab = st.tabs(["내 기본 비교군", "운영자 기본 비교군", "사용자 관리"])
    with my_tab:
        _render_profile_editor(
            prefix="my_comparison_profile",
            title="내 기본 비교군",
            caption="모든 지표 화면의 시작값으로 사용되는 내 기본 비교군입니다.",
            profile_name="내 기본 비교군",
            store=user_profile_store,
            school_options=school_options,
            save_notice="내 기본 비교군을 저장했습니다.",
            restore_notice="내 기본 비교군을 초기화하고 운영자 기본 비교군을 적용했습니다.",
            restore_action=user_profile_store.delete,
        )
    with system_tab:
        _render_profile_editor(
            prefix="system_comparison_profile",
            title="운영자 기본 비교군",
            caption="사용자별 설정이 없는 계정과 새 사용자에게 적용되는 기본 비교군입니다.",
            profile_name="운영자 기본 비교군",
            store=system_profile_store,
            school_options=school_options,
            save_notice="운영자 기본 비교군을 저장했습니다.",
            restore_notice="코드 기본 비교군으로 복원했습니다.",
            restore_profile=lambda: default_comparison_profile(school_options),
        )
    with users_tab:
        _render_user_management(auth_user.email, initial_admin_emails)
else:
    _render_profile_editor(
        prefix="my_comparison_profile",
        title="내 기본 비교군",
        caption="모든 지표 화면의 시작값으로 사용되는 내 기본 비교군입니다.",
        profile_name="내 기본 비교군",
        store=user_profile_store,
        school_options=school_options,
        save_notice="내 기본 비교군을 저장했습니다.",
        restore_notice="내 기본 비교군을 초기화하고 운영자 기본 비교군을 적용했습니다.",
        restore_action=user_profile_store.delete,
    )
