from __future__ import annotations

import pandas as pd
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
from utils.auth import require_authenticated_user
from utils.comparison_charts import (
    build_chart_frame,
    build_chart_styler,
    render_bump_chart,
    render_comparison_heatmap,
    render_focus_range_chart,
    resolve_distribution_focus_range,
)
from utils.comparison_sidebar import build_group_definitions
from utils.config import APP_SUBTITLE, DATA_UPDATED
from utils.query import get_dataset
from utils.theme import apply_app_theme


PAGE = get_metric("staff_per_student")
SERIES = get_series("students_per_staff")

YEAR_COL = "기준년도"
SCHOOL_COL = "학교명"

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


def _format_students(value: float) -> str:
    return f"{value:,.1f}명"


def build_metric() -> MetricSpec:
    return MetricSpec(
        key=SERIES.id,
        label=SERIES.label,
        value_col=SERIES.column,
        y_axis_label=f"{SERIES.label} ({SERIES.unit})",
        precision=SERIES.decimals,
        threshold=ThresholdSpec(
            value=SERIES.threshold or 70.0,
            label=SERIES.threshold_label or "기준값",
            color="#F59E0B",
            dash="dot",
        ),
        higher_is_better=False,
        chart_title=f"{PAGE.title} 비교 추이",
        formatter=_format_students,
    )


def _focus_range(series: pd.Series, metric: MetricSpec) -> tuple[float, float] | None:
    if series.empty:
        return None
    threshold = metric.threshold.value if metric.threshold else 70.0
    return resolve_distribution_focus_range(
        series,
        lower_quantile=0.10,
        upper_quantile=0.85,
        padding_ratio=0.08,
        min_padding=2.0,
        include_values=(threshold,),
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

    df = get_dataset(PAGE.dataset_key)
    schools = sorted(df[SCHOOL_COL].dropna().unique())
    years = sorted(df[YEAR_COL].dropna().unique())
    latest_year = max(years)

    sidebar_values = render_school_sidebar(
        schools=schools,
        default_schools=[PAGE.default_school] if PAGE.default_school in schools else schools[:1],
        config=SidebarConfig(
            header="학교 선택",
            school_label="비교 학교",
            school_help=f"총 {len(schools)}개 학교 가운데 비교할 학교를 선택합니다.",
            meta_lines=(
                SidebarMeta(text=f"업데이트: {DATA_UPDATED}"),
                SidebarMeta(text=f"대상 학교 수: {len(schools)}개"),
                SidebarMeta(text=f"기준년도 범위: {min(years)} ~ {latest_year}"),
                SidebarMeta(text="단위: 명"),
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

    metric = build_metric()
    chart_df = build_chart_frame(
        df,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        value_col=metric.value_col,
        selected_schools=selected_schools,
        group_definitions=group_definitions,
    )
    chart_styler = build_chart_styler(selected_schools, group_definitions)
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
            "지표명": "직원 1인당 학생수를 보여주는 교육 지원 여건 지표입니다.",
            "화면 표시값": "한국대학평가원 대학현황지표의 직원 1인당 학생수 재계산값을 우선 사용합니다.",
            "산식": "재학생 수 ÷ 직원총계 (명)",
            "해석 방향": "값이 낮을수록 직원 1인이 담당하는 학생 수가 적어 학생 지원 여건이 상대적으로 양호한 것으로 볼 수 있습니다.",
            "기준값": "70명 이하",
            "비교 대상 그룹": "선택 학교와 비교 그룹 평균선을 함께 보여줘 상대적 위치를 확인할 수 있습니다.",
            "업데이트": DATA_UPDATED,
        },
        kpi_threshold_suffix="70명 이하",
        chart_styler=chart_styler,
    )

    render_focus_range_chart(
        chart_df,
        metric=metric,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        chart_title=f"{metric.label} 집중 구간 비교",
        chart_styler=chart_styler,
        title="집중 구간 보기",
        caption="학교 간 차이가 나타나는 구간을 확대해 직원 1인당 학생수의 세부 차이를 비교합니다.",
        range_resolver=_focus_range,
    )

    render_comparison_heatmap(
        chart_df,
        metric=metric,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        selected_schools=selected_schools,
        group_definitions=group_definitions,
        title="학교별 직원 1인당 학생수 히트맵",
        caption="연도별 직원 1인당 학생수 강도를 색으로 보여줘 어느 학교가 높고 낮은지 빠르게 비교할 수 있습니다.",
        hover_value_label="직원 1인당 학생수(명)",
    )

    render_bump_chart(
        chart_df,
        metric=metric,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        selected_schools=selected_schools,
        group_definitions=group_definitions,
        title="학교별 순위 변화 범프 차트",
        caption="직원 1인당 학생수 순위 변화를 통해 선택 학교와 비교 그룹 평균의 상대적 흐름을 볼 수 있습니다.",
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
    st.caption(f"데이터 출처: 한국대학평가원 대학현황지표 가공 CSV | 업데이트: {DATA_UPDATED}")


main()
