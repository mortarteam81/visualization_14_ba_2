from __future__ import annotations

import pandas as pd
import streamlit as st

from registry import get_metric, get_series
from ui import (
    MetricSpec,
    SidebarConfig,
    SidebarMeta,
    ThresholdSpec,
    build_pivot_table,
    build_yearly_stats,
    render_pivot_table,
    render_school_sidebar,
    render_single_metric_page,
    render_stats_table,
)
from utils.ai_panel import render_metric_ai_analysis_panel
from utils.chart_utils import add_threshold_hlines, create_multi_metric_line_chart
from utils.comparison_charts import (
    build_chart_frame,
    build_chart_styler,
    render_bump_chart,
    render_comparison_heatmap,
    render_focus_range_chart,
)
from utils.comparison_sidebar import build_group_definitions
from utils.config import APP_SUBTITLE, DATA_SOURCE, DATA_UPDATED
from utils.query import get_dataset
from utils.theme import apply_app_theme


PAGE = get_metric("gyowon")
JEONGWON = get_series("gyowon_jeongwon")
JAEHAK = get_series("gyowon_jaehak")

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
        "광운대학교",
        "서강대학교",
        "성균관대학교",
        "중앙대학교",
        "한양대학교",
    ],
    CUSTOM_PRESET: [],
}


def build_metric(series) -> MetricSpec:
    threshold_spec = None
    if series.threshold is not None:
        threshold_spec = ThresholdSpec(
            value=series.threshold,
            label=series.threshold_label or "Threshold",
            color="#F59E0B",
            dash="dot",
        )

    return MetricSpec(
        key=series.id,
        label=series.label,
        value_col=series.column,
        y_axis_label=f"{series.label} (%)",
        precision=series.decimals,
        threshold=threshold_spec,
        chart_title=f"{PAGE.title} 비교 추이",
    )


def _focus_range(series: pd.Series, metric: MetricSpec) -> tuple[float, float] | None:
    if series.empty:
        return None
    data_min = float(series.min())
    data_max = float(series.max())
    if metric.threshold is not None:
        lower = max(0.0, min(data_min, metric.threshold.value - 15))
        upper = max(metric.threshold.value + 20, min(data_max, metric.threshold.value + 35))
    else:
        lower = max(0.0, data_min - 10)
        upper = data_max + 10
    if upper <= lower:
        return None
    return lower, upper


def render_dual_metric_comparison(filtered_df: pd.DataFrame) -> None:
    if len(filtered_df[SCHOOL_COL].unique()) != 1:
        return

    comparison_metrics = [build_metric(JEONGWON), build_metric(JAEHAK)]
    st.subheader("기준별 비교")
    comparison_fig = create_multi_metric_line_chart(
        filtered_df,
        x=YEAR_COL,
        metrics=[(metric.label, metric.value_col) for metric in comparison_metrics],
        title="학생정원 기준 vs 재학생 기준",
        y_label="전임교원 확보율 (%)",
        color_map={
            JEONGWON.label: "#6EA8FF",
            JAEHAK.label: "#FF9A4D",
        },
    )
    thresholds = [metric.threshold for metric in comparison_metrics if metric.threshold is not None]
    if thresholds:
        add_threshold_hlines(comparison_fig, thresholds)
    st.plotly_chart(comparison_fig, width="stretch")

    with st.expander("기준별 연도 통계", expanded=False):
        for metric in comparison_metrics:
            render_stats_table(
                build_yearly_stats(filtered_df, year_col=YEAR_COL, metric=metric),
                title=metric.label,
            )

    for metric in comparison_metrics:
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
    apply_app_theme()
    st.title(f"{PAGE.icon} {PAGE.title}")
    st.caption(APP_SUBTITLE)

    raw_df = get_dataset(PAGE.dataset_key, include_branch=True, data_source=DATA_SOURCE)

    with st.sidebar:
        st.header("옵션")
        include_branch = st.toggle(
            "분교 포함",
            value=False,
            help="분교 데이터를 포함해 비교합니다.",
        )
        criterion = st.radio(
            "비교 기준",
            options=["학생정원 기준", "재학생 기준"],
            index=0,
            help="4주기 인증 기준은 학생정원 기준에 맞춰 제시됩니다.",
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
            school_help=f"총 {len(schools)}개 학교 중에서 비교할 학교를 선택합니다.",
            meta_lines=(
                SidebarMeta(text=f"데이터 소스: {'data.go.kr API' if DATA_SOURCE == 'api' else '로컬 CSV'}"),
                SidebarMeta(text=f"업데이트: {DATA_UPDATED}"),
                SidebarMeta(text=f"대상 학교 수: {len(schools)}개"),
                SidebarMeta(text=f"기준년도 범위: {min(years)} ~ {latest_year}"),
            ),
        ),
    )
    selected_schools = sidebar_values["selected_schools"]
    group_definitions = build_group_definitions(
        schools,
        key_prefix=PAGE.id,
        title="비교 대상 그룹",
        caption="선택 학교와 함께 볼 평균선을 만들 비교 그룹을 지정합니다.",
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

    selected_series = JEONGWON if criterion == "학생정원 기준" else JAEHAK
    selected_metric = build_metric(selected_series)
    chart_df = build_chart_frame(
        df,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        value_col=selected_metric.value_col,
        selected_schools=selected_schools,
        group_definitions=group_definitions,
    )
    chart_styler = build_chart_styler(selected_schools, group_definitions)
    active_groups = [name for name, school_list in group_definitions.items() if name and school_list]

    if active_groups:
        st.info(
            "메인 차트에는 선택 학교, 그룹 구성 학교, 그룹 평균선이 함께 표시됩니다. "
            + ", ".join(active_groups)
        )
    else:
        st.caption("활성화된 그룹이 없어 현재는 선택 학교 추이만 표시됩니다.")

    render_single_metric_page(
        df=filtered_df,
        chart_df=chart_df,
        metric=selected_metric,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        latest_year=latest_year,
        chart_title=f"{PAGE.title} 비교 추이 ({criterion})",
        selected_schools=selected_schools,
        definition_rows={
            "지표": "대학의 법정 기준 대비 실제 전임교원 확보 수준을 비교하는 지표입니다.",
            "학생정원 기준": "학생정원을 기준으로 계산한 전임교원 확보율입니다.",
            "재학생 기준": "재학생 수를 기준으로 계산한 전임교원 확보율입니다.",
            "4주기 인증 기준": PAGE.threshold_note,
            "비교 대상 그룹": "선택 학교 외에 그룹 평균과 그룹 구성 학교를 함께 표시해 상대적 위치를 확인합니다.",
            "분교 포함": "기본값은 본교 기준이며, 필요할 때만 분교 포함 비교를 켤 수 있습니다.",
            "업데이트": f"{DATA_UPDATED} / {DATA_SOURCE.upper()}",
        },
        kpi_threshold_suffix=f"{selected_metric.threshold.value:.1f}% 이상" if selected_metric.threshold else "",
        chart_styler=chart_styler,
    )

    render_focus_range_chart(
        chart_df,
        metric=selected_metric,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        chart_title=f"{selected_metric.label} 기준선 인근 확대 비교",
        chart_styler=chart_styler,
        title="기준선 인근 확대 보기",
        caption="인증 기준 주변 구간을 확대해 학교별 차이를 더 쉽게 비교할 수 있습니다.",
        range_resolver=_focus_range,
    )

    render_comparison_heatmap(
        chart_df,
        metric=selected_metric,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        selected_schools=selected_schools,
        group_definitions=group_definitions,
        title="학교별 확보율 히트맵",
        caption="연도별 확보율 강도를 색으로 보여주어 선택 학교와 비교 그룹의 흐름을 빠르게 비교할 수 있습니다.",
        hover_value_label="확보율(%)",
    )

    render_bump_chart(
        chart_df,
        metric=selected_metric,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        selected_schools=selected_schools,
        group_definitions=group_definitions,
        title="학교별 순위 변화 범프 차트",
        caption="연도별 확보율 순위 변화를 통해 선택 학교와 그룹 평균의 상하위 흐름을 확인할 수 있습니다.",
        toggle_key=f"{PAGE.id}_bump_selected_only",
    )

    render_dual_metric_comparison(filtered_df)

    st.divider()
    render_metric_ai_analysis_panel(
        page_key=PAGE.id,
        df=df,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        latest_year=latest_year,
        metrics=[build_metric(JEONGWON), build_metric(JAEHAK)],
        selected_schools=selected_schools,
        group_definitions=group_definitions,
    )

    st.markdown("---")
    st.caption(f"데이터 출처: 대학알리미 | 업데이트: {DATA_UPDATED}")


main()
