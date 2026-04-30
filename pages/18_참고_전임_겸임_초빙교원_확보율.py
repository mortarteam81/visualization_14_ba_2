from __future__ import annotations

from collections.abc import Sequence

import pandas as pd
import streamlit as st

from registry import get_metric, get_series
from ui import (
    MetricSpec,
    SidebarConfig,
    ThresholdSpec,
    render_school_sidebar,
    render_single_metric_page,
)
from utils.ai_panel import render_metric_ai_analysis_panel
from utils.auth import require_authenticated_user
from utils.chart_utils import add_threshold_hline, create_trend_line_chart
from utils.comparison_charts import (
    build_chart_frame,
    build_chart_styler,
    render_bump_chart,
    render_comparison_heatmap,
    render_focus_range_chart,
    resolve_threshold_focus_range,
)
from utils.comparison_sidebar import build_default_group_preset_config, build_group_definitions, build_standard_sidebar_meta
from utils.config import DATA_UPDATED
from utils.query import get_dataset
from utils.source_display import render_source_caption
from utils.theme import (
    apply_app_theme,
    disable_mobile_plotly_zoom,
    get_plotly_chart_config,
    is_mobile_compact_mode,
)

try:
    from utils.analysis_scope import apply_default_analysis_scope
except ImportError:
    def apply_default_analysis_scope(df: pd.DataFrame, metric_or_manifest: object) -> pd.DataFrame:
        return df


PAGE = get_metric("faculty_securing_reference")
FULLTIME_QUOTA = get_series("faculty_reference_fulltime_quota_rate")
FULLTIME_ENROLLED = get_series("faculty_reference_fulltime_enrolled_rate")
ADJUNCT_INCLUDED_QUOTA = get_series("faculty_reference_adjunct_included_quota_rate")
ADJUNCT_INCLUDED_ENROLLED = get_series("faculty_reference_adjunct_included_enrolled_rate")
INVITED_INCLUDED_QUOTA = get_series("faculty_reference_invited_included_quota_rate")
INVITED_INCLUDED_ENROLLED = get_series("faculty_reference_invited_included_enrolled_rate")

YEAR_COL = "기준년도"
SCHOOL_COL = "학교명"
STANDARD_RATE = 100.0

DEFAULT_SLOT_PRESETS, GROUP_PRESETS, CUSTOM_PRESET = build_default_group_preset_config()
SERIES_BY_BASIS = {
    "편제정원 기준": (FULLTIME_QUOTA, ADJUNCT_INCLUDED_QUOTA, INVITED_INCLUDED_QUOTA),
    "재학생 기준": (FULLTIME_ENROLLED, ADJUNCT_INCLUDED_ENROLLED, INVITED_INCLUDED_ENROLLED),
}
SERIES_BY_SCOPE = {
    "전임교원": {
        "편제정원 기준": FULLTIME_QUOTA,
        "재학생 기준": FULLTIME_ENROLLED,
    },
    "겸임포함": {
        "편제정원 기준": ADJUNCT_INCLUDED_QUOTA,
        "재학생 기준": ADJUNCT_INCLUDED_ENROLLED,
    },
    "초빙포함": {
        "편제정원 기준": INVITED_INCLUDED_QUOTA,
        "재학생 기준": INVITED_INCLUDED_ENROLLED,
    },
}


def build_metric(series) -> MetricSpec:
    return MetricSpec(
        key=series.id,
        label=series.label,
        value_col=series.column,
        y_axis_label=f"{series.label} (%)",
        precision=series.decimals,
        threshold=ThresholdSpec(
            value=series.threshold or STANDARD_RATE,
            label=series.threshold_label or "교원확보율 100%",
            color="#F59E0B",
            dash="dot",
        ),
        higher_is_better=True,
        chart_title=f"{PAGE.title} 비교 추이",
    )


def _focus_range(series: pd.Series, metric: MetricSpec) -> tuple[float, float] | None:
    if series.empty:
        return None
    return resolve_threshold_focus_range(
        series,
        metric,
        lower_offset=30.0,
        upper_offset=20.0,
        min_lower=0.0,
    )


def _scope_label(series_label: str) -> str:
    return series_label.split("(", maxsplit=1)[0]


def _build_cumulative_long_frame(
    frame: pd.DataFrame,
    *,
    metrics: Sequence[MetricSpec],
) -> pd.DataFrame:
    pieces: list[pd.DataFrame] = []
    multiple_schools = frame[SCHOOL_COL].nunique() > 1
    for metric in metrics:
        metric_frame = frame[[YEAR_COL, SCHOOL_COL, metric.value_col]].copy()
        metric_frame = metric_frame.rename(columns={metric.value_col: "확보율"})
        metric_frame["교원범위"] = _scope_label(metric.label)
        metric_frame["비교항목"] = metric_frame["교원범위"]
        if multiple_schools:
            metric_frame["비교항목"] = metric_frame[SCHOOL_COL] + " · " + metric_frame["교원범위"]
        pieces.append(metric_frame)
    return pd.concat(pieces, ignore_index=True)


def _plotly_config() -> dict[str, object]:
    return get_plotly_chart_config()


def _render_cumulative_comparison_basis(
    filtered_df: pd.DataFrame,
    basis: str,
    series_tuple: Sequence,
) -> None:
    metrics = [build_metric(series) for series in series_tuple]
    long_df = _build_cumulative_long_frame(filtered_df, metrics=metrics)
    fig = create_trend_line_chart(
        long_df,
        x=YEAR_COL,
        y="확보율",
        color="비교항목",
        title=f"{basis} 누적 교원확보율 비교",
        y_label="교원확보율 (%)",
    )
    add_threshold_hline(
        fig,
        threshold=STANDARD_RATE,
        label="교원확보율 100%",
        dash="dot",
    )
    disable_mobile_plotly_zoom(fig)
    st.plotly_chart(fig, use_container_width=True, config=_plotly_config())

    with st.expander(f"{basis} 연도별 데이터", expanded=False):
        if is_mobile_compact_mode():
            st.caption("표는 좌우로 스크롤해서 전체 열을 확인할 수 있습니다.")
        table_columns = [YEAR_COL, SCHOOL_COL, *[metric.value_col for metric in metrics]]
        st.dataframe(
            filtered_df[table_columns].sort_values([SCHOOL_COL, YEAR_COL]),
            use_container_width=True,
            hide_index=True,
        )


def render_cumulative_comparison_tabs(filtered_df: pd.DataFrame) -> None:
    st.subheader("전임·겸임포함·초빙포함 누적 확보율")
    if is_mobile_compact_mode():
        basis = st.selectbox(
            "누적 확보율 기준",
            list(SERIES_BY_BASIS),
            key=f"{PAGE.id}_compact_cumulative_basis",
        )
        _render_cumulative_comparison_basis(filtered_df, basis, SERIES_BY_BASIS[basis])
        return

    tabs = st.tabs(list(SERIES_BY_BASIS))
    for tab, (basis, series_tuple) in zip(tabs, SERIES_BY_BASIS.items()):
        with tab:
            _render_cumulative_comparison_basis(filtered_df, basis, series_tuple)


def main() -> None:
    st.set_page_config(
        page_title=f"{PAGE.title} | 대학알리미 시각화 대시보드",
        page_icon=PAGE.icon,
        layout="wide",
    )
    require_authenticated_user()
    apply_app_theme()
    st.title(f"{PAGE.icon} {PAGE.title}")
    st.caption("첨단분야 학과 증원 기준 검토를 위한 누적 교원확보율 참고 지표")

    df = get_dataset(PAGE.dataset_key)
    df = apply_default_analysis_scope(df, PAGE)
    schools = sorted(df[SCHOOL_COL].dropna().unique())
    years = sorted(df[YEAR_COL].dropna().unique())
    latest_year = max(years)

    with st.sidebar:
        st.header("옵션")
        criterion = st.radio(
            "비교 기준",
            options=list(SERIES_BY_BASIS),
            index=0,
            help="편제정원 기준과 재학생 기준 확보율을 전환합니다.",
        )
        scope = st.radio(
            "교원 범위",
            options=list(SERIES_BY_SCOPE),
            index=2,
            help="메인 차트에 표시할 누적 교원확보율 범위를 선택합니다.",
        )

    sidebar_values = render_school_sidebar(
        schools=schools,
        key_prefix=PAGE.id,
        default_schools=[PAGE.default_school] if PAGE.default_school in schools else schools[:1],
        config=SidebarConfig(
            header="학교 선택",
            school_label="비교 학교",
            school_help=f"총 {len(schools)}개 학교 가운데 비교할 학교를 선택합니다.",
            meta_lines=build_standard_sidebar_meta(
                data_updated=DATA_UPDATED,
                school_count=len(schools),
                year_min=min(years),
                year_max=latest_year,
                unit="%",
                source=PAGE,
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

    selected_series = SERIES_BY_SCOPE[scope][criterion]
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
        st.info("현재 차트에는 선택 학교와 함께 다음 비교 그룹 평균이 표시됩니다: " + ", ".join(active_groups))
    else:
        st.caption("활성화된 그룹이 없어 현재는 선택 학교 추이만 표시됩니다.")

    render_single_metric_page(
        df=filtered_df,
        chart_df=chart_df,
        metric=selected_metric,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        latest_year=latest_year,
        chart_title=f"{PAGE.title} 비교 추이 ({criterion}, {scope})",
        selected_schools=selected_schools,
        definition_rows={
            "지표": "전임교원, 겸임포함, 초빙포함 교원확보율을 누적 기준으로 함께 보는 참고 지표입니다.",
            "전임교원": "전임교원만 반영한 교원확보율입니다.",
            "겸임포함": "전임교원 확보율에 겸임교원 반영분을 포함한 누적 확보율입니다.",
            "초빙포함": "전임교원과 겸임교원에 초빙교원 반영분까지 포함한 누적 확보율입니다.",
            "첨단분야 증원 참고 기준": "수도권 대학 첨단분야 학과 증원 검토 시 교원확보율 100% 기준을 확인하기 위한 참고선입니다.",
            "비교 대상 그룹": "선택 학교 외에 그룹 평균과 그룹 구성 학교를 함께 표시해 상대적 위치를 확인합니다.",
            "업데이트": DATA_UPDATED,
        },
        kpi_threshold_suffix="100.0% 이상",
        chart_styler=chart_styler,
    )

    render_focus_range_chart(
        chart_df,
        metric=selected_metric,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        chart_title=f"{selected_metric.label} 100% 기준선 인근 비교",
        chart_styler=chart_styler,
        title="100% 기준선 인근 확대 보기",
        caption="교원확보율 100% 주변 구간을 확대해 학교별 충족 여지를 비교합니다.",
        range_resolver=_focus_range,
    )

    render_comparison_heatmap(
        chart_df,
        metric=selected_metric,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        selected_schools=selected_schools,
        group_definitions=group_definitions,
        title="학교별 교원확보율 히트맵",
        caption="연도별 확보율 강도를 색으로 보여줘 선택 학교와 비교 그룹의 흐름을 빠르게 비교할 수 있습니다.",
        hover_value_label="교원확보율(%)",
    )

    render_bump_chart(
        chart_df,
        metric=selected_metric,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        selected_schools=selected_schools,
        group_definitions=group_definitions,
        title="학교별 순위 변화 범프 차트",
        caption="교원확보율 순위 변화를 통해 선택 학교와 그룹 평균의 상하위 흐름을 확인할 수 있습니다.",
        toggle_key=f"{PAGE.id}_bump_selected_only",
    )

    render_cumulative_comparison_tabs(filtered_df)

    st.divider()
    render_metric_ai_analysis_panel(
        page_key=PAGE.id,
        df=df,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        latest_year=latest_year,
        metrics=[build_metric(series) for series in PAGE.series],
        selected_schools=selected_schools,
        group_definitions=group_definitions,
    )

    st.markdown("---")
    render_source_caption(PAGE)


main()
