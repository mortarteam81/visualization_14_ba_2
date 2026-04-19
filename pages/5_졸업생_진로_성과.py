from __future__ import annotations

import streamlit as st

from registry import get_metric, get_series
from ui import (
    MetricSpec,
    SidebarConfig,
    SidebarMeta,
    ThresholdSpec,
    render_school_sidebar,
    render_single_metric_page,
)
from utils.ai_panel import render_metric_ai_analysis_panel
from utils.config import APP_SUBTITLE, DATA_UPDATED
from utils.query import get_dataset
from utils.theme import apply_app_theme


PAGE = get_metric("jirosung")
SERIES = get_series("jirosung_outcome")

YEAR_COL = "기준년도"
SCHOOL_COL = "학교명"
BRANCH_COL = "본분교명"
MAIN_BRANCH = "본교"


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
        ),
        chart_title=f"{PAGE.title} 비교 추이",
    )


def main() -> None:
    st.set_page_config(
        page_title=f"{PAGE.title} | 대학 시각화 대시보드",
        page_icon=PAGE.icon,
        layout="wide",
    )
    apply_app_theme()
    st.title(f"{PAGE.icon} {PAGE.title}")
    st.caption(APP_SUBTITLE)

    raw_df = get_dataset(PAGE.dataset_key, include_branch=True)
    include_branch = st.sidebar.toggle(
        "분교 포함",
        value=False,
        help="분교 데이터를 포함해 비교합니다.",
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
            school_help=f"총 {len(schools)}개 학교 중에서 선택합니다.",
            meta_lines=(
                SidebarMeta(text=f"업데이트: {DATA_UPDATED}"),
                SidebarMeta(text=f"대상 학교 수: {len(schools)}개"),
                SidebarMeta(text=f"기준년도 범위: {min(years)} ~ {latest_year}"),
            ),
        ),
    )

    selected_schools = sidebar_values["selected_schools"]
    if not selected_schools:
        st.info("비교할 학교를 하나 이상 선택해 주세요.")
        st.stop()

    filtered_df = df[df[SCHOOL_COL].isin(selected_schools)].copy()
    if filtered_df.empty:
        st.error("선택한 학교에 해당하는 데이터가 없습니다.")
        st.stop()

    render_single_metric_page(
        df=filtered_df,
        chart_df=df,
        metric=build_metric(),
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        latest_year=latest_year,
        chart_title=f"선택 학교 ({len(selected_schools)}개) {PAGE.title} 비교 추이",
        selected_schools=selected_schools,
        definition_rows={
            "지표": "대학알리미 공시자료 기준 비교 지표입니다.",
            "계산식": "(취업률 + 진학률) 기반의 졸업생 진로 성과 지표입니다.",
            "4주기 인증 기준": PAGE.threshold_note,
            "분교 포함": "기본은 본교만 표시되며, 필요 시 분교 포함을 켤 수 있습니다.",
            "업데이트": DATA_UPDATED,
        },
        kpi_threshold_suffix=f"{SERIES.threshold:.1f}% 이상",
    )

    st.divider()
    render_metric_ai_analysis_panel(
        page_key=PAGE.id,
        df=df,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        latest_year=latest_year,
        metrics=[build_metric()],
        selected_schools=selected_schools,
        group_definitions={},
    )

    st.markdown("---")
    st.caption(f"데이터 출처: 대학알리미 | 업데이트: {DATA_UPDATED}")


main()
