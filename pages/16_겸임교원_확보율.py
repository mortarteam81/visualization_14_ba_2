from __future__ import annotations

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
from utils.comparison_charts import (
    build_chart_frame,
    build_chart_styler,
    render_bump_chart,
    render_comparison_heatmap,
    render_focus_range_chart,
    resolve_threshold_focus_range,
)
from utils.comparison_page import render_single_school_metric_comparison
from utils.comparison_sidebar import build_default_group_preset_config, build_group_definitions, build_standard_sidebar_meta
from utils.config import DATA_UPDATED
from utils.query import get_dataset
from utils.source_display import render_source_caption
from utils.theme import apply_app_theme

try:
    from utils.analysis_scope import apply_default_analysis_scope
except ImportError:
    def apply_default_analysis_scope(df: pd.DataFrame, metric_or_manifest: object) -> pd.DataFrame:
        return df


PAGE = get_metric("adjunct_faculty")
QUOTA_FINAL = get_series("adjunct_faculty_quota_final")
ENROLLED_FINAL = get_series("adjunct_faculty_enrolled_final")

YEAR_COL = "기준년도"
SCHOOL_COL = "학교명"
MAX_RECOGNITION = 4.0

DEFAULT_SLOT_PRESETS, GROUP_PRESETS, CUSTOM_PRESET = build_default_group_preset_config()


def build_metric(series) -> MetricSpec:
    return MetricSpec(
        key=series.id,
        label=series.label,
        value_col=series.column,
        y_axis_label=f"{series.label} (%)",
        precision=series.decimals,
        threshold=ThresholdSpec(
            value=series.threshold or MAX_RECOGNITION,
            label=series.threshold_label or "최대 인정값",
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
        lower_offset=2.0,
        upper_offset=0.5,
        min_lower=0.0,
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
    st.caption("한국대학평가원 대학현황지표 기반 겸임교원 확보율 최종 인정값")

    df = get_dataset(PAGE.dataset_key)
    df = apply_default_analysis_scope(df, PAGE)
    schools = sorted(df[SCHOOL_COL].dropna().unique())
    years = sorted(df[YEAR_COL].dropna().unique())
    latest_year = max(years)

    with st.sidebar:
        st.header("옵션")
        criterion = st.radio(
            "비교 기준",
            options=["편제정원 기준", "재학생 기준"],
            index=0,
            help="겸임포함 확보율에서 전임교원 확보율을 뺀 뒤 0.3을 곱하고 4% 상한을 적용한 최종 인정값입니다.",
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

    selected_series = QUOTA_FINAL if criterion == "편제정원 기준" else ENROLLED_FINAL
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
        chart_title=f"{PAGE.title} 비교 추이 ({criterion})",
        selected_schools=selected_schools,
        definition_rows={
            "지표": "겸임포함 교원확보율에서 전임교원 확보율을 뺀 파생값에 0.3을 곱하고 4% 상한을 적용한 최종 인정값입니다.",
            "편제정원 기준": "편제정원 기준 겸임포함 확보율과 전임교원 확보율의 차이를 기반으로 계산합니다.",
            "재학생 기준": "재학생 기준 겸임포함 확보율과 전임교원 확보율의 차이를 기반으로 계산합니다.",
            "기준선": "인증 기준값이 아니라 최대 인정값 4%를 표시합니다.",
            "해석 방향": "값이 높을수록 겸임교원 확보 기여가 크지만, 최종 인정값은 4%를 초과하지 않습니다.",
            "비교 대상 그룹": "선택 학교 외에 그룹 평균과 그룹 구성 학교를 함께 표시해 상대적 위치를 확인합니다.",
            "업데이트": DATA_UPDATED,
        },
        kpi_threshold_suffix="4.0% 인정상한 도달",
        chart_styler=chart_styler,
    )

    render_focus_range_chart(
        chart_df,
        metric=selected_metric,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        chart_title=f"{selected_metric.label} 인정상한 인근 비교",
        chart_styler=chart_styler,
        title="최대 인정값 인근 보기",
        caption="4% 인정상한 주변 구간을 확대해 학교별 최종 인정값 차이를 비교합니다.",
        range_resolver=_focus_range,
    )

    render_comparison_heatmap(
        chart_df,
        metric=selected_metric,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        selected_schools=selected_schools,
        group_definitions=group_definitions,
        title="학교별 겸임교원 확보율 히트맵",
        caption="연도별 최종 인정값의 강도를 색으로 보여줘 선택 학교와 비교 그룹의 흐름을 빠르게 비교할 수 있습니다.",
        hover_value_label="최종 인정값(%)",
    )

    render_bump_chart(
        chart_df,
        metric=selected_metric,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        selected_schools=selected_schools,
        group_definitions=group_definitions,
        title="학교별 순위 변화 범프 차트",
        caption="최종 인정값 순위 변화를 통해 선택 학교와 그룹 평균의 상하위 흐름을 확인할 수 있습니다.",
        toggle_key=f"{PAGE.id}_bump_selected_only",
    )

    render_single_school_metric_comparison(
        filtered_df,
        metrics=[build_metric(QUOTA_FINAL), build_metric(ENROLLED_FINAL)],
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        section_title="기준별 비교",
        chart_title="편제정원 기준 vs 재학생 기준",
        y_label="겸임교원 확보율 최종 인정값 (%)",
        color_map={
            build_metric(QUOTA_FINAL).label: "#6EA8FF",
            build_metric(ENROLLED_FINAL).label: "#FF9A4D",
        },
        stats_expander_title="기준별 연도 통계",
        pivot_label_prefix="연도별 학교 비교",
    )

    st.divider()
    render_metric_ai_analysis_panel(
        page_key=PAGE.id,
        df=df,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        latest_year=latest_year,
        metrics=[build_metric(QUOTA_FINAL), build_metric(ENROLLED_FINAL)],
        selected_schools=selected_schools,
        group_definitions=group_definitions,
    )

    st.markdown("---")
    render_source_caption(PAGE)


main()
