from __future__ import annotations

import streamlit as st

from registry import get_metric, get_series
from ui import MetricSpec, SidebarConfig, SidebarMeta, ThresholdSpec, render_school_sidebar, render_single_metric_page
from utils.ai_panel import render_metric_ai_analysis_panel
from utils.comparison_charts import (
    build_chart_frame,
    build_chart_styler,
    render_bump_chart,
    render_comparison_heatmap,
    render_focus_range_chart,
)
from utils.comparison_sidebar import build_group_definitions
from utils.config import APP_SUBTITLE, DATA_UPDATED
from utils.query import get_dataset
from utils.theme import apply_app_theme


PAGE = get_metric("jirosung")
SERIES = get_series("jirosung_outcome")

YEAR_COL = "기준년도"
SCHOOL_COL = "학교명"
BRANCH_COL = "본분교명"
MAIN_BRANCH = "본교"

CUSTOM_PRESET = "직접 구성"
DEFAULT_SLOT_PRESETS = {
    1: "서울 소재 여대",
    2: "주요 경쟁 대학",
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
    "주요 경쟁 대학": [
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
        threshold=ThresholdSpec(
            value=SERIES.threshold or 0.0,
            label=SERIES.threshold_label or "Threshold",
            color="#F59E0B",
            dash="dot",
        ),
        chart_title=f"{PAGE.title} 비교 추이",
    )


def main() -> None:
    st.set_page_config(
        page_title=f"{PAGE.title} | 대학알리미 시각화 대시보드",
        page_icon=PAGE.icon,
        layout="wide",
    )
    apply_app_theme()
    st.title(f"{PAGE.icon} {PAGE.title}")
    st.caption(APP_SUBTITLE)

    raw_df = get_dataset(PAGE.dataset_key, include_branch=True)

    with st.sidebar:
        st.header("옵션")
        include_branch = st.toggle(
            "분교 포함",
            value=False,
            help="분교 데이터를 함께 포함해 비교할 수 있습니다.",
        )

    df = raw_df if include_branch else raw_df[raw_df[BRANCH_COL] == MAIN_BRANCH].copy()
    schools = sorted(df[SCHOOL_COL].dropna().unique())
    years = sorted(df[YEAR_COL].dropna().unique())
    latest_year = max(years)

    sidebar_values = render_school_sidebar(
        schools=schools,
        default_schools=[PAGE.default_school] if PAGE.default_school in schools else schools[:1],
        config=SidebarConfig(
            header="학교 선택",
            school_label="비교 학교",
            school_help=f"총 {len(schools)}개 학교 가운데 비교할 학교를 선택합니다.",
            meta_lines=(
                SidebarMeta(text=f"업데이트: {DATA_UPDATED}"),
                SidebarMeta(text=f"대상 학교 수: {len(schools)}개"),
                SidebarMeta(text=f"기준년도 범위: {min(years)} ~ {latest_year}"),
                SidebarMeta(text="단위: %"),
            ),
        ),
    )
    selected_schools = sidebar_values["selected_schools"]
    group_definitions = build_group_definitions(
        schools,
        key_prefix=PAGE.id,
        title="비교 대상 그룹",
        caption="선택 학교의 흐름을 함께 보기 위해 비교 그룹을 지정합니다.",
        group_presets=GROUP_PRESETS,
        default_slot_presets=DEFAULT_SLOT_PRESETS,
        custom_preset_label=CUSTOM_PRESET,
        group_name_help="차트에 표시할 그룹 이름입니다.",
        group_schools_help="이 그룹에 포함할 학교를 선택합니다.",
        default_group_name_template="비교 그룹 {slot}",
    )

    if not selected_schools:
        st.info("비교할 학교를 하나 이상 선택해 주세요.")
        st.stop()

    filtered_df = df[df[SCHOOL_COL].isin(selected_schools)].copy()
    if filtered_df.empty:
        st.error("선택한 학교에 해당하는 데이터가 없습니다.")
        st.stop()

    metric = build_metric()
    chart_df = build_chart_frame(
        df,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        value_col=metric.value_col,
        selected_schools=selected_schools,
        group_definitions=group_definitions,
    )
    chart_styler = build_chart_styler(selected_schools, group_definitions)
    active_groups = [name for name, school_list in group_definitions.items() if name and school_list]

    if active_groups:
        st.info("현재 차트에는 선택 학교와 함께 다음 비교 그룹 평균선이 표시됩니다: " + ", ".join(active_groups))
    else:
        st.caption("활성화된 비교 그룹이 없어 현재는 선택 학교 추이만 표시됩니다.")

    render_single_metric_page(
        df=filtered_df,
        chart_df=chart_df,
        metric=metric,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        latest_year=latest_year,
        chart_title=f"{PAGE.title} 비교 추이",
        selected_schools=selected_schools,
        definition_rows={
            "지표명": "졸업생의 취업·진학 성과를 종합해 연도별 추이를 보여주는 지표입니다.",
            "산식 개요": "취업자와 진학자 비중을 바탕으로 졸업생 진로 성과를 산출합니다.",
            "4주기 인증 기준": PAGE.threshold_note,
            "비교 대상 그룹": "선택 학교와 비교 그룹 평균을 함께 표시해 상대적인 흐름을 볼 수 있습니다.",
            "분교 포함": "기본값은 본교 기준이며, 옵션에서 분교 포함 여부를 바꿀 수 있습니다.",
            "업데이트": DATA_UPDATED,
        },
        kpi_threshold_suffix=f"{SERIES.threshold:.1f}% 기준",
        chart_styler=chart_styler,
    )

    render_focus_range_chart(
        chart_df,
        metric=metric,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        chart_title=f"{metric.label} 기준선 인근 확대 비교",
        chart_styler=chart_styler,
        title="기준선 인근 확대 보기",
        caption="기준선 주변 구간을 확대해 낮은 진로 성과 학교들의 연도별 차이를 더 쉽게 비교할 수 있습니다.",
    )

    render_comparison_heatmap(
        chart_df,
        metric=metric,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        selected_schools=selected_schools,
        group_definitions=group_definitions,
        title="학교별 진로 성과 히트맵",
        caption="연도별 진로 성과 수준을 색의 강도로 보여주어 선택 학교와 비교 그룹의 흐름을 한눈에 볼 수 있습니다.",
        hover_value_label="진로 성과(%)",
    )

    render_bump_chart(
        chart_df,
        metric=metric,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        selected_schools=selected_schools,
        group_definitions=group_definitions,
        title="학교별 순위 변화 범프 차트",
        caption="연도별 진로 성과 순위 변화를 통해 선택 학교와 비교 그룹 평균의 위치 변화를 확인할 수 있습니다.",
        toggle_key=f"{PAGE.id}_bump_selected_only",
    )

    st.divider()
    render_metric_ai_analysis_panel(
        page_key=PAGE.id,
        df=df,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        latest_year=latest_year,
        metrics=[metric],
        selected_schools=selected_schools,
        group_definitions=group_definitions,
    )

    st.markdown("---")
    st.caption(f"데이터 출처: 대학알리미 | 업데이트: {DATA_UPDATED}")


main()
