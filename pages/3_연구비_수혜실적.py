from __future__ import annotations

import pandas as pd
import streamlit as st

from registry import get_metric, get_series
from ui import (
    MetricSpec,
    SidebarConfig,
    ThresholdSpec,
    build_pivot_table,
    build_yearly_stats,
    render_definition_table,
    render_pivot_table,
    render_school_sidebar,
    render_stats_table,
)
from utils.ai_panel import render_metric_ai_analysis_panel
from utils.auth import require_authenticated_user
from utils.chart_utils import (
    add_threshold_hline,
    create_trend_line_chart,
)
from utils.comparison_charts import (
    build_chart_frame,
    build_chart_styler,
    render_bump_chart,
    render_comparison_heatmap,
    render_focus_range_chart,
    resolve_threshold_focus_range,
)
from utils.comparison_page import render_dual_metric_sections, render_single_school_metric_comparison
from utils.comparison_sidebar import build_default_group_preset_config, build_group_definitions, build_standard_sidebar_meta
from utils.config import APP_SUBTITLE, DATA_UPDATED
from utils.query import get_dataset
from utils.theme import apply_app_theme


PAGE = get_metric("research")
RESEARCH_IN = get_series("research_in")
RESEARCH_OUT = get_series("research_out")

YEAR_COL = "기준년도"
SCHOOL_COL = "학교명"
CAMPUS_COL = "본분교명"
MAIN_CAMPUS = "본교"

DEFAULT_SLOT_PRESETS, GROUP_PRESETS, CUSTOM_PRESET = build_default_group_preset_config()


def build_metric(series) -> MetricSpec:
    metric_label = series.label
    threshold_label = series.threshold_label or "기준값"
    threshold_color = "#F59E0B"

    if series.id == "research_in":
        metric_label = "교내 연구비"
        threshold_label = "4주기 인증 기준(교내연구비)"
        threshold_color = "#38BDF8"
    elif series.id == "research_out":
        metric_label = "교외 연구비"
        threshold_label = "4주기 인증 기준(교외연구비)"
        threshold_color = "#F97316"

    return MetricSpec(
        key=series.id,
        label=metric_label,
        value_col=series.column,
        y_axis_label=f"{metric_label} ({series.unit})",
        precision=series.decimals,
        threshold=ThresholdSpec(
            value=series.threshold or 0.0,
            label=threshold_label,
            color=threshold_color,
            dash="dot",
        ),
        chart_title=f"{metric_label} 비교 추이",
    )


def _focus_range(series: pd.Series, metric: MetricSpec) -> tuple[float, float] | None:
    if series.empty:
        return None
    threshold = metric.threshold.value if metric.threshold else 0.0
    return resolve_threshold_focus_range(
        series,
        metric,
        lower_offset=threshold,
        upper_offset=max(threshold * 5.0, 5_000.0),
    )


def render_metric_section(
    *,
    base_df: pd.DataFrame,
    filtered_df: pd.DataFrame,
    metric: MetricSpec,
    selected_schools: list[str],
    group_definitions: dict[str, list[str]],
) -> None:
    chart_df = build_chart_frame(
        base_df,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        value_col=metric.value_col,
        selected_schools=selected_schools,
        group_definitions=group_definitions,
    )
    chart_styler = build_chart_styler(selected_schools, group_definitions)

    fig = create_trend_line_chart(
        chart_df,
        x=YEAR_COL,
        y=metric.value_col,
        color=SCHOOL_COL,
        title=metric.chart_title or metric.label,
        x_label=YEAR_COL,
        y_label=metric.y_axis_label,
        hovermode="closest",
    )
    if metric.threshold is not None:
        add_threshold_hline(
            fig,
            threshold=metric.threshold.value,
            label=metric.threshold.label,
            color=metric.threshold.color or "#F59E0B",
            dash=metric.threshold.dash,
        )
    chart_styler(fig)
    st.plotly_chart(fig, use_container_width=True)

    render_focus_range_chart(
        chart_df,
        metric=metric,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        chart_title=f"{metric.label} 기준선 인근 확대 비교",
        chart_styler=chart_styler,
        title="기준선 인근 확대 보기",
        caption="인증 기준 주변 구간을 확대해 학교별 차이를 더 쉽게 읽을 수 있습니다.",
        range_resolver=_focus_range,
    )

    render_comparison_heatmap(
        chart_df,
        metric=metric,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        selected_schools=selected_schools,
        group_definitions=group_definitions,
        title=f"{metric.label} 히트맵",
        caption="연도별 연구비 규모를 색으로 보여주어 선택 학교와 비교 그룹의 상대적 위치를 빠르게 파악할 수 있습니다.",
        hover_value_label=metric.label,
    )

    render_bump_chart(
        chart_df,
        metric=metric,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        selected_schools=selected_schools,
        group_definitions=group_definitions,
        title=f"{metric.label} 순위 변화",
        caption="연도별 연구비 순위 흐름을 통해 선택 학교와 그룹 평균의 상대적 위치 변화를 확인할 수 있습니다.",
        toggle_key=f"{metric.key}_bump_selected_only",
    )

    with st.expander("연도별 통계", expanded=False):
        render_stats_table(
            build_yearly_stats(filtered_df, year_col=YEAR_COL, metric=metric),
            title="",
        )

    render_pivot_table(
        build_pivot_table(
            filtered_df,
            year_col=YEAR_COL,
            school_col=SCHOOL_COL,
            value_col=metric.value_col,
            precision=metric.precision,
        ),
        label=f"연도별 학교 비교: {metric.label}",
    )


def main() -> None:
    st.set_page_config(
        page_title=f"{PAGE.title} | 대학알리미 시각화 대시보드",
        page_icon=PAGE.icon,
        layout="wide",
    )
    require_authenticated_user()
    apply_app_theme()
    st.title(f"{PAGE.icon} {PAGE.title}")
    st.caption(APP_SUBTITLE)

    with st.sidebar:
        st.header("옵션")
        include_branch = st.toggle(
            "분교 포함",
            value=False,
            help="분교 데이터를 포함해 비교합니다.",
        )

    raw_df = get_dataset(PAGE.dataset_key, include_branch=True)
    df = raw_df if include_branch else raw_df[raw_df[CAMPUS_COL] == MAIN_CAMPUS].copy()
    schools = sorted(df[SCHOOL_COL].dropna().unique())
    years = sorted(df[YEAR_COL].dropna().unique())
    latest_year = max(years)

    sidebar_values = render_school_sidebar(
        schools=schools,
        default_schools=[PAGE.default_school] if PAGE.default_school in schools else schools[:1],
        config=SidebarConfig(
            header="학교 선택",
            school_label="비교 학교",
            school_help=f"총 {len(schools)}개 학교 중에서 비교할 학교를 선택합니다.",
            meta_lines=build_standard_sidebar_meta(
                data_updated=DATA_UPDATED,
                school_count=len(schools),
                year_min=min(years),
                year_max=latest_year,
                unit="천원",
            ),
        ),
    )
    selected_schools = sidebar_values["selected_schools"]
    group_definitions = build_group_definitions(
        schools,
        key_prefix=PAGE.id,
        title="비교 대상 그룹",
        caption="연구비 평균선을 함께 보기 위한 비교 그룹을 지정합니다.",
        group_presets=GROUP_PRESETS,
        default_slot_presets=DEFAULT_SLOT_PRESETS,
        custom_preset_label=CUSTOM_PRESET,
        group_name_help="차트에 표시될 그룹 이름입니다.",
        group_schools_help="이 그룹에 포함할 학교를 직접 조정할 수 있습니다.",
        default_group_name_template="비교 그룹 {slot}",
    )

    if not selected_schools:
        st.info("비교할 학교를 하나 이상 선택해 주세요.")
        st.stop()

    filtered_df = df[df[SCHOOL_COL].isin(selected_schools)].copy()
    if filtered_df.empty:
        st.error("선택한 학교에 해당하는 데이터가 없습니다.")
        st.stop()

    metrics = [build_metric(RESEARCH_IN), build_metric(RESEARCH_OUT)]

    render_dual_metric_sections(
        filtered_df=filtered_df,
        metrics=metrics,
        latest_year=latest_year,
        school_col=SCHOOL_COL,
        year_col=YEAR_COL,
        render_metric_section=lambda metric: render_metric_section(
            base_df=df,
            filtered_df=filtered_df,
            metric=metric,
            selected_schools=selected_schools,
            group_definitions=group_definitions,
        ),
    )

    active_groups = [name for name, school_list in group_definitions.items() if name and school_list]
    if active_groups:
        st.info(
            "메인 차트에는 선택 학교, 그룹 구성 학교, 그룹 평균선이 함께 표시됩니다. "
            + ", ".join(active_groups)
        )
    else:
        st.caption("활성화된 그룹이 없어 현재는 선택 학교 추이만 표시됩니다.")

    render_single_school_metric_comparison(
        filtered_df,
        metrics=metrics,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        section_title="교내 연구비 / 교외 연구비 비교",
        chart_title="교내 연구비 vs 교외 연구비",
        y_label="연구비(천원)",
        color_map={
            metrics[0].label: "#6EA8FF",
            metrics[1].label: "#FF9A4D",
        },
    )

    st.divider()
    render_metric_ai_analysis_panel(
        page_key=PAGE.id,
        df=df,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        latest_year=latest_year,
        metrics=metrics,
        selected_schools=selected_schools,
        group_definitions=group_definitions,
    )

    render_definition_table(
        {
            "지표": "전임교원 1인당 연구비 수혜 실적을 교내 연구비와 교외 연구비로 나누어 비교합니다.",
            "교내 연구비": "전임교원 1인당 교내 연구비 수혜 실적입니다.",
            "교외 연구비": "전임교원 1인당 교외 연구비 수혜 실적입니다.",
            "4주기 인증 기준": PAGE.threshold_note,
            "비교 대상 그룹": "선택 학교 외에 그룹 평균과 그룹 구성 학교를 함께 표시해 상대적 위치를 확인합니다.",
            "분교 포함": "기본값은 본교 기준이며, 필요할 때만 분교 포함 비교를 켤 수 있습니다.",
            "데이터 기준": DATA_UPDATED,
        }
    )

    st.markdown("---")
    st.caption(f"데이터 출처: 대학알리미 | 업데이트: {DATA_UPDATED}")


main()
