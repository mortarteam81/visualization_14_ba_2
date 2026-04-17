from __future__ import annotations

import pandas as pd
import streamlit as st

from registry import get_metric, get_series
from ui import MetricSpec, SidebarConfig, SidebarMeta, ThresholdSpec, render_school_sidebar, render_single_metric_page
from utils.config import APP_SUBTITLE, DATA_UPDATED
from utils.grouping import build_group_average_frame
from utils.query import get_dataset


PAGE = get_metric("budam")
SERIES = get_series("budam_rate")
YEAR_COL = "기준년도"
SCHOOL_COL = "학교명"
VALUE_COL = SERIES.column
CUSTOM_PRESET = "사용자 정의"
GROUP_SLOT_COUNT = 3
DEFAULT_SLOT_PRESETS = {
    1: "서울 소재 여대",
    2: "경쟁대학",
    3: CUSTOM_PRESET,
}
GROUP_PRESETS = {
    "서울 소재 여대": [
        "덕성여자대학교",
        "동덕여자대학교",
        "서울여자대학교",
        "성신여자대학교",
        "숙명여자대학교",
        "이화여자대학교",
    ],
    "경쟁대학": [
        "건국대학교",
        "경희대학교",
        "고려대학교",
        "국민대학교",
        "동국대학교",
        "서강대학교",
        "성균관대학교",
        "중앙대학교",
        "한양대학교",
    ],
    CUSTOM_PRESET: [],
}


def build_metric() -> MetricSpec:
    return MetricSpec(
        key=SERIES.id,
        label=SERIES.label,
        value_col=SERIES.column,
        y_axis_label=f"{SERIES.label} ({SERIES.unit})",
        precision=SERIES.decimals,
        threshold=ThresholdSpec(value=SERIES.threshold or 0.0, label=SERIES.threshold_label or "Threshold"),
        chart_title=f"{PAGE.title} 연도별 추이",
    )


def _filter_preset_schools(schools: list[str], preset_name: str) -> list[str]:
    return [school for school in GROUP_PRESETS.get(preset_name, []) if school in schools]


def _apply_group_preset(slot: int, schools: list[str]) -> None:
    preset_key = f"budam_group_preset_{slot}"
    name_key = f"budam_group_name_{slot}"
    schools_key = f"budam_group_schools_{slot}"
    preset_name = st.session_state[preset_key]

    if preset_name == CUSTOM_PRESET:
        st.session_state[name_key] = st.session_state.get(name_key) or f"그룹 {slot}"
        st.session_state[schools_key] = st.session_state.get(schools_key, [])
        return

    st.session_state[name_key] = preset_name
    st.session_state[schools_key] = _filter_preset_schools(schools, preset_name)


def _ensure_group_state(slot: int, schools: list[str]) -> None:
    preset_key = f"budam_group_preset_{slot}"
    name_key = f"budam_group_name_{slot}"
    schools_key = f"budam_group_schools_{slot}"

    if preset_key in st.session_state:
        return

    default_preset = DEFAULT_SLOT_PRESETS[slot]
    st.session_state[preset_key] = default_preset
    if default_preset == CUSTOM_PRESET:
        st.session_state[name_key] = f"그룹 {slot}"
        st.session_state[schools_key] = []
    else:
        st.session_state[name_key] = default_preset
        st.session_state[schools_key] = _filter_preset_schools(schools, default_preset)


def build_group_definitions(schools: list[str]) -> dict[str, list[str]]:
    preset_options = list(GROUP_PRESETS.keys())

    with st.sidebar:
        st.divider()
        st.subheader("조회 대상 학교 그룹")
        st.caption("프리셋으로 시작한 뒤 이름과 학교 목록을 자유롭게 수정할 수 있습니다.")

        for slot in range(1, GROUP_SLOT_COUNT + 1):
            _ensure_group_state(slot, schools)

            with st.expander(f"그룹 {slot}", expanded=slot == 1):
                st.selectbox(
                    "프리셋",
                    options=preset_options,
                    key=f"budam_group_preset_{slot}",
                    help="프리셋을 선택하면 추천 그룹 이름과 학교 목록이 채워집니다.",
                    on_change=_apply_group_preset,
                    args=(slot, schools),
                )
                st.text_input(
                    "그룹 이름",
                    key=f"budam_group_name_{slot}",
                    help="그래프 평균선 이름으로 사용됩니다.",
                )
                st.multiselect(
                    "그룹 학교",
                    schools,
                    key=f"budam_group_schools_{slot}",
                    help="이 그룹에 포함할 학교를 직접 추가하거나 제외할 수 있습니다.",
                )

    return {
        st.session_state[f"budam_group_name_{slot}"].strip(): st.session_state[f"budam_group_schools_{slot}"]
        for slot in range(1, GROUP_SLOT_COUNT + 1)
    }


def build_chart_frame(df: pd.DataFrame, selected_schools: list[str], group_definitions: dict[str, list[str]]) -> pd.DataFrame:
    grouped_schools = sorted(
        {
            school
            for schools_in_group in group_definitions.values()
            for school in schools_in_group
        }
    )
    visible_schools = sorted(set(selected_schools) | set(grouped_schools))
    selected_df = df[df[SCHOOL_COL].isin(visible_schools)].copy()
    group_average_df = build_group_average_frame(
        df,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        value_col=VALUE_COL,
        groups=group_definitions,
    )
    if group_average_df.empty:
        return selected_df
    return pd.concat([selected_df, group_average_df], ignore_index=True)


def main() -> None:
    st.set_page_config(page_title=f"{PAGE.title} | 교육여건 지표", page_icon=PAGE.icon, layout="wide")
    st.title(f"{PAGE.icon} {PAGE.title}")
    st.caption(APP_SUBTITLE)

    df = get_dataset(PAGE.dataset_key)
    schools = sorted(df[SCHOOL_COL].unique())
    years = sorted(df[YEAR_COL].unique())
    latest_year = max(years)

    sidebar_values = render_school_sidebar(
        schools=schools,
        default_schools=[PAGE.default_school] if PAGE.default_school in schools else schools[:1],
        config=SidebarConfig(
            header="필터",
            school_label="개별 학교 선택",
            school_help=f"전체 {len(schools)}개 학교 중 비교할 학교를 선택하세요.",
            meta_lines=(
                SidebarMeta(text=f"기준일: {DATA_UPDATED}"),
                SidebarMeta(text=f"전체 학교 수: {len(schools)}개"),
                SidebarMeta(text=f"수록 기간: {min(years)} ~ {latest_year}년"),
            ),
        ),
    )
    group_definitions = build_group_definitions(schools)

    selected_schools = sidebar_values["selected_schools"]
    if not selected_schools:
        st.info("사이드바에서 학교를 선택해 주세요.")
        st.stop()

    filtered_df = df[df[SCHOOL_COL].isin(selected_schools)].copy()
    if filtered_df.empty:
        st.error("선택한 학교에 해당하는 데이터가 없습니다.")
        st.stop()

    chart_df = build_chart_frame(df, selected_schools, group_definitions)
    active_groups = [name for name, school_list in group_definitions.items() if name and school_list]

    if active_groups:
        st.info(f"그래프에 그룹 평균선이 함께 표시됩니다: {', '.join(active_groups)}")
    else:
        st.caption("활성화된 그룹이 없어서 현재는 개별 학교 추이만 표시됩니다.")

    render_single_metric_page(
        df=filtered_df,
        chart_df=chart_df,
        metric=build_metric(),
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        latest_year=latest_year,
        chart_title=f"선택 학교, 그룹 구성 학교, 그룹 평균 {PAGE.title} 추이",
        definition_rows={
            "출처": "대학알리미 공시자료 (서울 소재 사립대학)",
            "산식": "법정부담금 부담액 ÷ 법정부담금 기준액 × 100 (%)",
            "4주기 인증 기준": PAGE.threshold_note,
            "그룹 비교": "개별 선택 학교와 그룹 구성 학교의 추이, 그룹 평균값을 함께 표시",
            "데이터 기준일": DATA_UPDATED,
        },
        kpi_threshold_suffix=f"{SERIES.threshold:.1f}% 이상",
    )
    st.markdown("---")
    st.caption(f"데이터 출처: 대학알리미 | 기준일: {DATA_UPDATED}")


main()
