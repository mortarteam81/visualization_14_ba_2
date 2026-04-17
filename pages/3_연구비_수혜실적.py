from __future__ import annotations

import streamlit as st

from registry import get_metric, get_series
from ui import MetricSpec, ThresholdSpec, render_dual_metric_page
from utils.config import APP_SUBTITLE, DATA_UPDATED
from utils.query import get_dataset


PAGE = get_metric("research")
RESEARCH_IN = get_series("research_in")
RESEARCH_OUT = get_series("research_out")


def build_metric(series_id: str) -> MetricSpec:
    series = get_series(series_id)
    return MetricSpec(
        key=series.id,
        label=series.label,
        value_col=series.column,
        y_axis_label=f"{series.label} ({series.unit})",
        precision=series.decimals,
        threshold=ThresholdSpec(value=series.threshold or 0.0, label=series.threshold_label or "Threshold"),
        chart_title=f"{series.label} 연도별 추이",
    )


def main() -> None:
    st.set_page_config(page_title=f"{PAGE.title} | 교육여건 지표", page_icon=PAGE.icon, layout="wide")
    st.title(f"{PAGE.icon} {PAGE.title}")
    st.caption(APP_SUBTITLE)

    with st.sidebar:
        st.header("필터")
        include_branch = st.toggle("분교 포함", value=False, help="분교 데이터를 포함합니다.")

    raw_df = get_dataset(PAGE.dataset_key, include_branch=True)
    df = raw_df if include_branch else raw_df[raw_df["본분교명"] == "본교"].copy()
    schools = sorted(df["학교명"].unique())
    years = sorted(df["기준년도"].unique())
    latest_year = max(years)

    with st.sidebar:
        default_selection = [PAGE.default_school] if PAGE.default_school in schools else schools[:1]
        selected_schools = st.multiselect("학교 선택", schools, default=default_selection)
        st.caption(f"기준일: {DATA_UPDATED}")
        st.caption(f"전체 학교 수: {len(schools)}개")
        st.caption(f"수록 기간: {min(years)} ~ {latest_year}년")
        st.caption("단위: 천원")

    if not selected_schools:
        st.info("사이드바에서 학교를 선택하세요.")
        st.stop()

    filtered_df = df[df["학교명"].isin(selected_schools)].copy()
    if filtered_df.empty:
        st.error("선택된 학교에 데이터가 없습니다.")
        st.stop()

    render_dual_metric_page(
        df=filtered_df,
        metrics=[build_metric("research_in"), build_metric("research_out")],
        year_col="기준년도",
        school_col="학교명",
        latest_year=latest_year,
        definition_rows={
            "출처": "대학알리미 공시자료 (서울 소재 사립대학교)",
            "교내 산식": "교내 연구비 합계 ÷ 전임교원 수",
            "교외 산식": "교외 연구비 합계 ÷ 전임교원 수",
            "4주기 인증 기준": PAGE.threshold_note,
            "분교 처리": "기본값은 본교만 표시, 사이드바에서 분교 포함 선택 가능",
            "데이터 기준일": DATA_UPDATED,
        },
    )
    st.markdown("---")
    st.caption(f"데이터 출처: 대학알리미 | 기준일: {DATA_UPDATED}")


main()
