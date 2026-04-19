from __future__ import annotations

import streamlit as st

from registry import get_metric, get_series
from ui import MetricSpec, ThresholdSpec, render_optional_page
from utils.config import APP_SUBTITLE, DATA_SOURCE, DATA_UPDATED
from utils.query import get_dataset
from utils.theme import apply_app_theme


PAGE = get_metric("gyowon")
JEONGWON = get_series("gyowon_jeongwon")
JAEHAK = get_series("gyowon_jaehak")


def build_metric(label: str, value_col: str, *, threshold: float | None = None) -> MetricSpec:
    threshold_spec = None
    if threshold is not None:
        threshold_spec = ThresholdSpec(value=threshold, label=JEONGWON.threshold_label or "Threshold")
    return MetricSpec(
        key=value_col,
        label=label,
        value_col=value_col,
        y_axis_label=f"{label} (%)",
        precision=1,
        threshold=threshold_spec,
        chart_title=f"{PAGE.title} 연도별 추이",
    )


def main() -> None:
    st.set_page_config(page_title=f"{PAGE.title} | 교육여건 지표", page_icon=PAGE.icon, layout="wide")
    apply_app_theme()
    st.title(f"{PAGE.icon} {PAGE.title}")
    st.caption(APP_SUBTITLE)

    with st.sidebar:
        st.header("필터")
        include_branch = st.toggle("분교 포함", value=False, help="분교 데이터를 포함합니다.")
        criterion = st.radio(
            "확보율 기준",
            options=["학생정원 기준", "재학생 기준"],
            index=0,
            help="4주기 인증의 주요 기준은 학생정원 기준입니다.",
        )

    raw_df = get_dataset(PAGE.dataset_key, include_branch=True, data_source=DATA_SOURCE)
    df = raw_df if include_branch else raw_df[raw_df["본분교명"] == "본교"].copy()

    schools = sorted(df["학교명"].unique())
    years = sorted(df["기준년도"].unique())
    latest_year = max(years)

    with st.sidebar:
        default_selection = [PAGE.default_school] if PAGE.default_school in schools else schools[:1]
        selected_schools = st.multiselect(
            "학교 선택",
            schools,
            default=default_selection,
            help=f"전체 {len(schools)}개 학교 중 선택",
        )
        source_label = "data.go.kr API" if DATA_SOURCE == "api" else "로컬 CSV"
        st.caption(f"데이터 소스: {source_label}")
        st.caption(f"기준일: {DATA_UPDATED}")
        st.caption(f"전체 학교 수: {len(schools)}개")
        st.caption(f"수록 기간: {min(years)} ~ {latest_year}년")

    if not selected_schools:
        st.info("사이드바에서 학교를 선택하세요.")
        st.stop()

    filtered_df = df[df["학교명"].isin(selected_schools)].copy()
    if filtered_df.empty:
        st.error("선택된 학교에 데이터가 없습니다.")
        st.stop()

    selected_metric = (
        build_metric(JEONGWON.label, JEONGWON.column, threshold=JEONGWON.threshold)
        if criterion == "학생정원 기준"
        else build_metric(JAEHAK.label, JAEHAK.column)
    )
    comparison_metrics = None
    if len(selected_schools) == 1:
        comparison_metrics = [
            build_metric(JEONGWON.label, JEONGWON.column, threshold=JEONGWON.threshold),
            build_metric(JAEHAK.label, JAEHAK.column),
        ]

    render_optional_page(
        df=filtered_df,
        base_metric=selected_metric,
        comparison_metrics=comparison_metrics,
        year_col="기준년도",
        school_col="학교명",
        latest_year=latest_year,
        chart_title=f"선택 학교 ({len(selected_schools)}개) {PAGE.title} 추이 ({criterion})",
        selected_schools=selected_schools,
        definition_rows={
            "출처": "대학알리미 공시자료 (서울 소재 사립대학교)",
            "학생정원 기준 산식": "전임교원 수 ÷ 교원법정정원(학생정원 기준) × 100 (%)",
            "재학생 기준 산식": "전임교원 수 ÷ 교원법정정원(재학생 기준) × 100 (%)",
            "4주기 인증 기준": PAGE.threshold_note,
            "분교 처리": "기본값은 본교만 표시, 사이드바에서 분교 포함 선택 가능",
            "데이터 기준일": f"{DATA_UPDATED} / {DATA_SOURCE.upper()}",
        },
    )
    st.markdown("---")
    st.caption(f"데이터 출처: 대학알리미 | 기준일: {DATA_UPDATED}")


main()
