from __future__ import annotations

import streamlit as st

from registry import get_metric, get_series
from ui import (
    MetricSpec,
    ThresholdSpec,
    build_dual_metric_kpis,
    build_pivot_table,
    build_yearly_stats,
    render_definition_table,
    render_kpis,
    render_pivot_table,
    render_stats_table,
)
from utils.chart_utils import (
    add_threshold_hline,
    create_trend_line_chart,
    emphasize_selected_traces,
    style_traces_by_name_contains,
)
from utils.config import APP_SUBTITLE, DATA_UPDATED
from utils.query import get_dataset
from utils.theme import apply_app_theme


PAGE = get_metric("research")
YEAR_COL = "기준년도"
SCHOOL_COL = "학교명"
CAMPUS_COL = "본분교명"
MAIN_CAMPUS = "본교"


def build_metric(series_id: str) -> MetricSpec:
    series = get_series(series_id)
    return MetricSpec(
        key=series.id,
        label=series.label,
        value_col=series.column,
        y_axis_label=f"{series.label} ({series.unit})",
        precision=series.decimals,
        threshold=ThresholdSpec(
            value=series.threshold or 0.0,
            label=series.threshold_label or "Threshold",
        ),
        chart_title=f"{series.label} 비교 추이",
    )


def render_dual_metric_selected_page(
    *,
    source_df,
    filtered_df,
    metrics: list[MetricSpec],
    year_col: str,
    school_col: str,
    latest_year: int | str,
    selected_schools: list[str],
    definition_rows: dict[str, str],
) -> None:
    render_kpis(
        build_dual_metric_kpis(
            filtered_df,
            metrics=metrics,
            latest_year=latest_year,
            school_col=school_col,
            year_col=year_col,
        ),
        columns=min(6, max(1, len(metrics) * 3)),
    )
    st.divider()

    tabs = st.tabs([metric.label for metric in metrics])
    for tab, metric in zip(tabs, metrics):
        with tab:
            st.subheader(metric.chart_title or metric.label)
            fig = create_trend_line_chart(
                source_df,
                x=year_col,
                y=metric.value_col,
                color=school_col,
                title=metric.chart_title or metric.label,
                x_label=year_col,
                y_label=metric.y_axis_label,
            )
            if metric.threshold is not None:
                add_threshold_hline(
                    fig,
                    threshold=metric.threshold.value,
                    label=metric.threshold.label,
                    color=metric.threshold.color or "red",
                    dash=metric.threshold.dash,
                )
            style_traces_by_name_contains(fig, "평균")
            emphasize_selected_traces(fig, selected_schools)
            st.plotly_chart(fig, width="stretch")

            with st.expander("Yearly stats", expanded=False):
                render_stats_table(
                    build_yearly_stats(filtered_df, year_col=year_col, metric=metric),
                    title="",
                )

            render_pivot_table(
                build_pivot_table(
                    filtered_df,
                    year_col=year_col,
                    school_col=school_col,
                    value_col=metric.value_col,
                    precision=metric.precision,
                ),
                label=f"Year by school: {metric.label}",
            )

    render_definition_table(definition_rows)


def main() -> None:
    st.set_page_config(page_title=f"{PAGE.title} | 서울 소재 사립대학교 시각화", page_icon=PAGE.icon, layout="wide")
    apply_app_theme()
    st.title(f"{PAGE.icon} {PAGE.title}")
    st.caption(APP_SUBTITLE)

    with st.sidebar:
        st.header("필터")
        include_branch = st.toggle(
            "분교 포함",
            value=False,
            help="분교 데이터를 포함해 비교할지 선택합니다.",
        )

    raw_df = get_dataset(PAGE.dataset_key, include_branch=True)
    df = raw_df if include_branch else raw_df[raw_df[CAMPUS_COL] == MAIN_CAMPUS].copy()
    schools = sorted(df[SCHOOL_COL].dropna().unique())
    years = sorted(df[YEAR_COL].dropna().unique())
    latest_year = max(years)

    with st.sidebar:
        default_selection = [PAGE.default_school] if PAGE.default_school in schools else schools[:1]
        selected_schools = st.multiselect("학교 선택", schools, default=default_selection)
        st.caption(f"데이터 기준: {DATA_UPDATED}")
        st.caption(f"비교 학교 수: {len(schools)}개")
        st.caption(f"분석 연도: {min(years)} ~ {latest_year}")
        st.caption("단위: 천원")

    if not selected_schools:
        st.info("사이드바에서 하나 이상의 학교를 선택해 주세요.")
        st.stop()

    filtered_df = df[df[SCHOOL_COL].isin(selected_schools)].copy()
    if filtered_df.empty:
        st.error("선택한 학교에 해당하는 데이터가 없습니다.")
        st.stop()

    render_dual_metric_selected_page(
        source_df=df,
        filtered_df=filtered_df,
        metrics=[build_metric("research_in"), build_metric("research_out")],
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        latest_year=latest_year,
        selected_schools=selected_schools,
        definition_rows={
            "지표": "전임교원 1인당 연구비를 교내와 교외로 나누어 비교합니다.",
            "교내 연구비": "전임교원 1인당 교내 연구비 수혜 실적입니다.",
            "교외 연구비": "전임교원 1인당 교외 연구비 수혜 실적입니다.",
            "4주기 인증 기준": PAGE.threshold_note,
            "분교 포함": "사이드바에서 본교만 보거나 분교를 함께 포함할 수 있습니다.",
            "데이터 기준": DATA_UPDATED,
        },
    )

    st.markdown("---")
    st.caption(f"데이터 출처: 대학알리미 | 기준일: {DATA_UPDATED}")


main()
