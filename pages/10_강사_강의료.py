from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from registry import get_metric, get_series
from ui import MetricSpec, SidebarConfig, SidebarMeta, render_school_sidebar, render_single_metric_page
from utils.ai_panel import render_metric_ai_analysis_panel
from utils.auth import require_authenticated_user
from utils.chart_utils import create_trend_line_chart
from utils.comparison_charts import (
    apply_right_label_xaxis_padding,
    build_chart_frame,
    build_chart_styler,
    render_bump_chart,
    render_comparison_heatmap,
    resolve_distribution_focus_range,
)
from utils.comparison_sidebar import build_group_definitions
from utils.config import APP_SUBTITLE, DATA_UPDATED
from utils.query import get_dataset
from utils.theme import apply_app_theme, apply_mobile_plotly_layout, get_plotly_chart_config


PAGE = get_metric("lecturer_pay")
SERIES = get_series("lecturer_hourly_pay")

YEAR_COL = "기준년도"
SCHOOL_COL = "학교명"
LECTURER_PAY_THRESHOLDS = {
    2023: 50_600.0,
    2024: 51_800.0,
    2025: 53_100.0,
}

CUSTOM_PRESET = "직접 구성"
DEFAULT_SLOT_PRESETS = {
    1: "서울 여자 대학",
    2: "주요 경쟁 대학",
    3: CUSTOM_PRESET,
}
GROUP_PRESETS = {
    "서울 여자 대학": [
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


def _format_won(value: float) -> str:
    return f"{value:,.0f}원"


def _threshold_for_year(year: int | str) -> float:
    return LECTURER_PAY_THRESHOLDS.get(int(year), SERIES.threshold or 0.0)


def build_metric(latest_year: int | str) -> MetricSpec:
    return MetricSpec(
        key=SERIES.id,
        label=SERIES.label,
        value_col=SERIES.column,
        y_axis_label=f"{SERIES.label} ({SERIES.unit})",
        precision=SERIES.decimals,
        threshold=None,
        higher_is_better=True,
        chart_title=f"{PAGE.title} 비교 추이",
        formatter=_format_won,
    )


def _threshold_years_from_frame(frame: pd.DataFrame) -> list[int]:
    years = sorted(
        {
            int(year)
            for year in frame[YEAR_COL].dropna().unique()
            if int(year) in LECTURER_PAY_THRESHOLDS
        }
    )
    return years


def build_lecturer_chart_styler(
    base_styler,
    chart_df: pd.DataFrame,
    selected_schools: list[str],
    *,
    show_threshold_trace: bool = True,
):
    threshold_years = _threshold_years_from_frame(chart_df)

    def _style(fig: go.Figure) -> None:
        base_styler(fig)
        for trace in fig.data:
            if getattr(trace, "visible", None) == "legendonly":
                trace.update(text=None, mode="lines+markers")
        fig.update_layout(shapes=[])
        # Static annotations do not follow legend toggles, so keep labels trace-bound only.
        fig.update_layout(annotations=[])

        if not show_threshold_trace or not threshold_years:
            return

        fig.add_trace(
            go.Scatter(
                x=threshold_years,
                y=[LECTURER_PAY_THRESHOLDS[year] for year in threshold_years],
                mode="lines+markers+text",
                name="연도별 기준값",
                text=[""] * (len(threshold_years) - 1) + ["연도별 기준값"],
                textposition="middle right",
                textfont={"size": 12, "color": "#F59E0B"},
                line={"color": "#F59E0B", "width": 3, "dash": "dot"},
                marker={"size": 8, "color": "#F59E0B"},
                hovertemplate="기준년도=%{x}<br>기준값=%{y:,.0f}원<extra></extra>",
                showlegend=True,
                cliponaxis=False,
            )
        )
        apply_right_label_xaxis_padding(fig)

    return _style


def _focus_range(series: pd.Series, metric: MetricSpec) -> tuple[float, float] | None:
    if series.empty:
        return None
    data_min = float(series.min())
    data_max = float(series.max())
    threshold_min = min(LECTURER_PAY_THRESHOLDS.values())
    threshold_max = max(LECTURER_PAY_THRESHOLDS.values())
    lower = max(0.0, min(data_min, threshold_min) - 5_000)
    upper = max(data_max, threshold_max) + 5_000
    if upper <= lower:
        return None
    return lower, upper


def render_zoomed_pay_chart(
    chart_df: pd.DataFrame,
    *,
    chart_styler,
) -> None:
    st.subheader("강사 강의료 확대 보기")
    st.caption("대부분의 학교가 모여 있는 50k~60k 구간을 넓혀 실제 강사 강의료를 비교합니다.")

    zoom_df = chart_df.dropna(subset=[SERIES.column]).copy()
    if zoom_df.empty:
        st.info("연도별 기준값과 비교할 수 있는 데이터가 없습니다.")
        return

    fig = create_trend_line_chart(
        zoom_df,
        x=YEAR_COL,
        y=SERIES.column,
        color=SCHOOL_COL,
        title="강사 강의료 확대 비교",
        x_label=YEAR_COL,
        y_label="강사 강의료 (원)",
        height=460,
        hovermode="closest",
    )
    chart_styler(fig)
    visible_values = zoom_df[SERIES.column].dropna()
    threshold_values = pd.Series(list(LECTURER_PAY_THRESHOLDS.values()))
    resolved_range = resolve_distribution_focus_range(
        visible_values,
        lower_quantile=0.05,
        upper_quantile=0.90,
        padding_ratio=0.08,
        min_padding=1_500.0,
        include_values=tuple(threshold_values),
    )
    if resolved_range is not None:
        fig.update_yaxes(range=list(resolved_range))
    fig.update_traces(
        hovertemplate=f"{SCHOOL_COL}=%{{fullData.name}}<br>{YEAR_COL}=%{{x}}<br>강사 강의료=%{{y:,.0f}}원<extra></extra>"
    )
    apply_mobile_plotly_layout(fig)
    st.plotly_chart(fig, use_container_width=True, config=get_plotly_chart_config())


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

    df = get_dataset(PAGE.dataset_key)
    schools = sorted(df[SCHOOL_COL].dropna().unique())
    years = sorted(df[YEAR_COL].dropna().unique())
    latest_year = max(years)

    sidebar_values = render_school_sidebar(
        schools=schools,
        key_prefix=PAGE.id,
        default_schools=[PAGE.default_school] if PAGE.default_school in schools else schools[:1],
        config=SidebarConfig(
            header="학교 선택",
            school_label="비교 학교",
            school_help=f"총 {len(schools)}개 학교 가운데 비교할 학교를 선택합니다.",
            meta_lines=(
                SidebarMeta(text=f"업데이트: {DATA_UPDATED}"),
                SidebarMeta(text=f"대상 학교 수: {len(schools)}개"),
                SidebarMeta(text=f"기준년도 범위: {min(years)} ~ {latest_year}"),
                SidebarMeta(text="단위: 원"),
            ),
        ),
    )
    selected_schools = sidebar_values["selected_schools"]
    group_definitions = build_group_definitions(
        schools,
        key_prefix=PAGE.id,
        title="비교 대상 그룹",
        caption="선택 학교와 함께 비교할 그룹 평균선을 만들 수 있습니다.",
        group_presets=GROUP_PRESETS,
        default_slot_presets=DEFAULT_SLOT_PRESETS,
        custom_preset_label=CUSTOM_PRESET,
        group_name_help="차트에 표시할 그룹 이름입니다.",
        group_schools_help="각 그룹에 포함할 학교를 선택합니다.",
        default_group_name_template="비교 그룹 {slot}",
    )

    if not selected_schools:
        st.info("비교할 학교를 하나 이상 선택해 주세요.")
        st.stop()

    filtered_df = df[df[SCHOOL_COL].isin(selected_schools)].copy()
    if filtered_df.empty:
        st.error("선택한 학교에 해당하는 데이터가 없습니다.")
        st.stop()

    metric = build_metric(latest_year)
    chart_df = build_chart_frame(
        df,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        value_col=metric.value_col,
        selected_schools=selected_schools,
        group_definitions=group_definitions,
    )
    base_chart_styler = build_chart_styler(
        selected_schools,
        group_definitions,
        show_grouped_schools=True,
    )
    chart_styler = build_lecturer_chart_styler(base_chart_styler, chart_df, selected_schools)
    active_groups = [name for name, school_list in group_definitions.items() if name and school_list]

    if active_groups:
        st.info("현재 차트에는 선택 학교와 함께 다음 비교 그룹 평균이 표시됩니다: " + ", ".join(active_groups))
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
            "지표명": "강사의 시간당 지급기준 단가를 학교별로 비교하는 지표입니다.",
            "화면 표시값": "학교·연도별 시간당 지급기준 단가를 총 강의시간 수로 가중평균한 값입니다.",
            "산식": "Σ(시간당 지급기준 단가 × 총 강의시간 수) ÷ Σ(총 강의시간 수)",
            "해석 방향": "값이 높을수록 강사에게 지급되는 시간당 강의료 수준이 높은 것으로 볼 수 있습니다.",
            "연도별 기준값": PAGE.threshold_note,
            "비교 대상 그룹": "선택 학교와 비교 그룹 평균선을 함께 보여줘 상대적 위치를 확인할 수 있습니다.",
            "업데이트": DATA_UPDATED,
        },
        kpi_threshold_suffix=f"{_threshold_for_year(latest_year):,.0f}원 이상",
        chart_styler=chart_styler,
    )

    gap_chart_styler = build_lecturer_chart_styler(
        base_chart_styler,
        chart_df,
        selected_schools,
        show_threshold_trace=False,
    )
    render_zoomed_pay_chart(chart_df, chart_styler=gap_chart_styler)

    render_comparison_heatmap(
        chart_df,
        metric=metric,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        selected_schools=selected_schools,
        group_definitions=group_definitions,
        title="학교별 강사 강의료 히트맵",
        caption="연도별 강사 강의료 수준을 색으로 보여줘 어느 학교가 높고 낮은지 빠르게 비교할 수 있습니다.",
        hover_value_label="강사 강의료(원)",
    )

    render_bump_chart(
        chart_df,
        metric=metric,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        selected_schools=selected_schools,
        group_definitions=group_definitions,
        title="학교별 순위 변화 범프 차트",
        caption="강사 강의료 순위 변화를 통해 선택 학교와 비교 그룹 평균의 상대적 흐름을 볼 수 있습니다.",
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
    st.caption(f"데이터 출처: 강사 강의료 가공 CSV | 업데이트: {DATA_UPDATED}")


main()
