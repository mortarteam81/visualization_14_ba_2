from __future__ import annotations

import streamlit as st

from registry import get_metric, get_series
from ui import MetricSpec, SidebarConfig, SidebarMeta, ThresholdSpec, render_school_sidebar, render_single_metric_page
from utils.config import APP_SUBTITLE, DATA_UPDATED
from utils.query import get_dataset


PAGE = get_metric("tuition")
SERIES = get_series("tuition_ratio")


def build_metric() -> MetricSpec:
    return MetricSpec(
        key=SERIES.id,
        label=SERIES.label,
        value_col=SERIES.column,
        y_axis_label=f"{SERIES.label} ({SERIES.unit})",
        precision=SERIES.decimals,
        threshold=ThresholdSpec(value=SERIES.threshold or 0.0, label=SERIES.threshold_label or "Threshold"),
        higher_is_better=False,
        chart_title=f"{PAGE.title} 연도별 추이",
    )


def main() -> None:
    st.set_page_config(page_title=f"{PAGE.title} | 교육여건 지표", page_icon=PAGE.icon, layout="wide")
    st.title(f"{PAGE.icon} {PAGE.title}")
    st.caption(APP_SUBTITLE)

    df = get_dataset(PAGE.dataset_key)
    schools = sorted(df["학교명"].unique())
    years = sorted(df["기준년도"].unique())
    latest_year = max(years)

    sidebar_values = render_school_sidebar(
        schools=schools,
        default_schools=[PAGE.default_school] if PAGE.default_school in schools else schools[:1],
        config=SidebarConfig(
            header="필터",
            school_label="학교 선택",
            school_help=f"전체 {len(schools)}개 학교 중 선택",
            meta_lines=(
                SidebarMeta(text=f"기준일: {DATA_UPDATED}"),
                SidebarMeta(text=f"전체 학교 수: {len(schools)}개"),
                SidebarMeta(text=f"수록 기간: {min(years)} ~ {latest_year}년"),
            ),
        ),
    )

    selected_schools = sidebar_values["selected_schools"]
    if not selected_schools:
        st.info("사이드바에서 학교를 선택하세요.")
        st.stop()

    filtered_df = df[df["학교명"].isin(selected_schools)].copy()
    if filtered_df.empty:
        st.error("선택된 학교에 데이터가 없습니다.")
        st.stop()

    render_single_metric_page(
        df=filtered_df,
        metric=build_metric(),
        year_col="기준년도",
        school_col="학교명",
        latest_year=latest_year,
        chart_title=f"선택 학교 ({len(selected_schools)}개) {PAGE.title} 추이",
        definition_rows={
            "출처": "대학알리미 공시자료 결산 현황 (서울 소재 사립대학교)",
            "산식": "등록금수입 ÷ 운영수입 × 100 (%)",
            "4주기 인증 기준": PAGE.threshold_note,
            "데이터 기준일": DATA_UPDATED,
        },
        kpi_threshold_suffix=f"{SERIES.threshold:.1f}% 이하",
    )
    st.markdown("---")
    st.caption(f"데이터 출처: 대학알리미 | 기준일: {DATA_UPDATED}")


main()
