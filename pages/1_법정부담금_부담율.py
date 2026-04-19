from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.colors import qualitative

from registry import get_metric, get_series
from ui import (
    MetricSpec,
    SidebarConfig,
    SidebarMeta,
    ThresholdSpec,
    render_school_sidebar,
    render_single_metric_page,
)
from utils.ai_analysis import analyze_budam_with_lmstudio, build_budam_analysis_payload
from utils.ai_providers import LMStudioError
from utils.chart_utils import add_threshold_hline, create_trend_line_chart
from utils.config import APP_SUBTITLE, DATA_UPDATED
from utils.grouping import AVERAGE_LINE_SUFFIX, build_group_average_frame
from utils.query import get_dataset


PAGE = get_metric("budam")
SERIES = get_series("budam_rate")
YEAR_COL = "기준년도"
SCHOOL_COL = "학교명"
VALUE_COL = SERIES.column
CUSTOM_PRESET = "사용자 정의"
GROUP_SLOT_COUNT = 3
LOW_RANGE_MAX = 40.0
LABEL_POSITIONS = ("middle right", "top right", "bottom right")
DEFAULT_SLOT_PRESETS = {
    1: "서울 소재 여대",
    2: "경쟁 대학",
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
    "경쟁 대학": [
        "건국대학교",
        "경희대학교",
        "고려대학교",
        "국민대학교",
        "동국대학교",
        "서강대학교",
        "성균관대학교",
        "중앙대학교",
        "한양대학교",
    ],
    CUSTOM_PRESET: [],
}
AI_RESULT_KEY = "budam_ai_analysis_result"
AI_ERROR_KEY = "budam_ai_analysis_error"


def build_metric() -> MetricSpec:
    return MetricSpec(
        key=SERIES.id,
        label=SERIES.label,
        value_col=SERIES.column,
        y_axis_label=f"{SERIES.label} ({SERIES.unit})",
        precision=SERIES.decimals,
        threshold=ThresholdSpec(
            value=SERIES.threshold or 0.0,
            label=SERIES.threshold_label or "Threshold",
            color="#B45309",
            dash="dot",
        ),
        chart_title=f"{PAGE.title} 비교 추이",
    )


def _filter_preset_schools(schools: list[str], preset_name: str) -> list[str]:
    return [school for school in GROUP_PRESETS.get(preset_name, []) if school in schools]


def _apply_group_preset(slot: int, schools: list[str]) -> None:
    preset_key = f"budam_group_preset_{slot}"
    name_key = f"budam_group_name_{slot}"
    schools_key = f"budam_group_schools_{slot}"
    preset_name = st.session_state[preset_key]

    if preset_name == CUSTOM_PRESET:
        st.session_state[name_key] = st.session_state.get(name_key) or f"그룹 {slot}"
        st.session_state[schools_key] = st.session_state.get(schools_key, [])
        return

    st.session_state[name_key] = preset_name
    st.session_state[schools_key] = _filter_preset_schools(schools, preset_name)


def _ensure_group_state(slot: int, schools: list[str]) -> None:
    preset_key = f"budam_group_preset_{slot}"
    name_key = f"budam_group_name_{slot}"
    schools_key = f"budam_group_schools_{slot}"

    if preset_key in st.session_state:
        return

    default_preset = DEFAULT_SLOT_PRESETS[slot]
    st.session_state[preset_key] = default_preset
    if default_preset == CUSTOM_PRESET:
        st.session_state[name_key] = f"그룹 {slot}"
        st.session_state[schools_key] = []
    else:
        st.session_state[name_key] = default_preset
        st.session_state[schools_key] = _filter_preset_schools(schools, default_preset)


def build_group_definitions(schools: list[str]) -> dict[str, list[str]]:
    preset_options = list(GROUP_PRESETS.keys())

    with st.sidebar:
        st.divider()
        st.subheader("비교 대상 그룹")
        st.caption("프리셋으로 시작한 뒤 그룹 이름과 학교 목록을 자유롭게 조정할 수 있습니다.")

        for slot in range(1, GROUP_SLOT_COUNT + 1):
            _ensure_group_state(slot, schools)

            with st.expander(f"그룹 {slot}", expanded=slot == 1):
                st.selectbox(
                    "프리셋",
                    options=preset_options,
                    key=f"budam_group_preset_{slot}",
                    help="프리셋을 선택하면 추천 그룹 이름과 학교 목록이 채워집니다.",
                    on_change=_apply_group_preset,
                    args=(slot, schools),
                )
                st.text_input(
                    "그룹 이름",
                    key=f"budam_group_name_{slot}",
                    help="그래프 평균선 이름으로 사용됩니다.",
                )
                st.multiselect(
                    "그룹 학교",
                    schools,
                    key=f"budam_group_schools_{slot}",
                    help="이 그룹에 포함할 학교를 직접 추가하거나 제외할 수 있습니다.",
                )

    return {
        st.session_state[f"budam_group_name_{slot}"].strip(): st.session_state[f"budam_group_schools_{slot}"]
        for slot in range(1, GROUP_SLOT_COUNT + 1)
    }


def build_chart_frame(
    df: pd.DataFrame,
    selected_schools: list[str],
    group_definitions: dict[str, list[str]],
) -> pd.DataFrame:
    grouped_schools = sorted(
        {
            school
            for schools_in_group in group_definitions.values()
            for school in schools_in_group
        }
    )
    visible_schools = sorted(set(selected_schools) | set(grouped_schools))
    selected_df = df[df[SCHOOL_COL].isin(visible_schools)].copy()
    group_average_df = build_group_average_frame(
        df,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        value_col=VALUE_COL,
        groups=group_definitions,
    )
    if group_average_df.empty:
        return selected_df
    return pd.concat([selected_df, group_average_df], ignore_index=True)


def build_chart_styler(selected_schools: list[str], group_definitions: dict[str, list[str]]):
    grouped_schools = {
        school
        for schools_in_group in group_definitions.values()
        for school in schools_in_group
    }
    average_line_names = {
        f"{group_name} {AVERAGE_LINE_SUFFIX}"
        for group_name, schools_in_group in group_definitions.items()
        if group_name and schools_in_group
    }
    selected_school_set = set(selected_schools)
    grouped_school_names = sorted(grouped_schools - selected_school_set)

    selected_palette = ["#0F4C81", "#C44E52", "#2C7C5B", "#7A4FA3", "#C17C10", "#1F6F8B"]
    selected_colors = {
        school_name: selected_palette[index % len(selected_palette)]
        for index, school_name in enumerate(selected_schools)
    }
    grouped_palette = qualitative.Safe + qualitative.Set2 + qualitative.Pastel
    grouped_colors = {
        school_name: grouped_palette[index % len(grouped_palette)]
        for index, school_name in enumerate(grouped_school_names)
    }
    average_palette = ["#111827", "#7C3AED", "#D97706"]
    average_colors = {
        line_name: average_palette[index % len(average_palette)]
        for index, line_name in enumerate(sorted(average_line_names))
    }
    label_positions = {
        line_name: LABEL_POSITIONS[index % len(LABEL_POSITIONS)]
        for index, line_name in enumerate(
            [*selected_schools, *sorted(average_line_names), *grouped_school_names]
        )
    }

    def _apply_last_point_label(trace: go.Scatter, text: str) -> None:
        point_count = len(trace.x) if getattr(trace, "x", None) is not None else 0
        if point_count == 0:
            return
        labels = [""] * point_count
        labels[-1] = text
        trace.update(
            mode="lines+markers+text",
            text=labels,
            textposition=label_positions.get(text, "middle right"),
            textfont={"size": 11},
            cliponaxis=False,
        )

    def _style(fig: go.Figure) -> None:
        for trace in fig.data:
            trace_name = getattr(trace, "name", "") or ""

            if trace_name in average_line_names:
                color = average_colors.get(trace_name, "#111827")
                trace.update(
                    opacity=1.0,
                    line={"width": 3, "dash": "dash", "color": color},
                    marker={"size": 7, "color": color},
                )
                _apply_last_point_label(trace, trace_name)
                continue

            if trace_name in selected_school_set:
                color = selected_colors.get(trace_name, "#0F4C81")
                trace.update(
                    opacity=1.0,
                    line={"width": 3.4, "color": color},
                    marker={"size": 8, "color": color},
                )
                _apply_last_point_label(trace, trace_name)
                continue

            if trace_name in grouped_schools:
                color = grouped_colors.get(trace_name, "#94A3B8")
                trace.update(
                    opacity=0.58,
                    line={"width": 2, "color": color},
                    marker={"size": 5, "color": color},
                )
                _apply_last_point_label(trace, trace_name)

        fig.update_layout(
            title={"x": 0.02, "xanchor": "left"},
            plot_bgcolor="#FAFAF8",
            paper_bgcolor="#FFFFFF",
            hovermode="closest",
            margin={"r": 180},
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "left",
                "x": 0,
            },
        )
        fig.update_xaxes(showspikes=True, spikemode="across", spikesnap="cursor")
        fig.update_yaxes(showspikes=True, spikemode="across", spikesnap="cursor")

    return _style


def render_low_range_chart(
    chart_df: pd.DataFrame,
    *,
    metric: MetricSpec,
    chart_title: str,
    chart_styler,
) -> None:
    st.subheader("저구간 확대 보기")
    st.caption(
        f"{LOW_RANGE_MAX:.0f}% 이하 구간을 확대해 낮은 부담율대 학교들의 연도별 차이를 더 쉽게 비교할 수 있습니다."
    )
    fig = create_trend_line_chart(
        chart_df,
        x=YEAR_COL,
        y=metric.value_col,
        color=SCHOOL_COL,
        title=chart_title,
        x_label=YEAR_COL,
        y_label=metric.y_axis_label,
        height=420,
        hovermode="closest",
    )
    if metric.threshold is not None:
        add_threshold_hline(
            fig,
            threshold=metric.threshold.value,
            label=metric.threshold.label,
            color=metric.threshold.color or "#B45309",
            dash=metric.threshold.dash,
        )
    chart_styler(fig)
    fig.update_yaxes(range=[0, LOW_RANGE_MAX])
    st.plotly_chart(fig, width="stretch")


def _render_analysis_list(title: str, items: list[str]) -> None:
    st.markdown(f"**{title}**")
    if not items:
        st.caption("표시할 내용이 없습니다.")
        return
    for item in items:
        st.markdown(f"- {item}")


def render_ai_analysis_panel(
    *,
    df: pd.DataFrame,
    selected_schools: list[str],
    group_definitions: dict[str, list[str]],
    latest_year: int,
) -> None:
    st.subheader("AI 분석")
    st.caption("LM Studio 로컬 모델이 현재 선택 결과를 바탕으로 요약과 해석을 생성합니다.")

    control_col1, control_col2, control_col3 = st.columns([1, 1, 1.2])
    with control_col1:
        tone = st.selectbox("분석 톤", ["보고서형", "간결형"], key="budam_ai_tone")
    with control_col2:
        focus = st.selectbox("분석 초점", ["선택 학교 중심", "그룹 비교 중심"], key="budam_ai_focus")
    with control_col3:
        run_analysis = st.button("AI 분석 실행", width="stretch", type="primary")

    if run_analysis:
        payload = build_budam_analysis_payload(
            df,
            year_col=YEAR_COL,
            school_col=SCHOOL_COL,
            value_col=VALUE_COL,
            selected_schools=selected_schools,
            group_definitions=group_definitions,
            latest_year=latest_year,
            threshold=SERIES.threshold or 0.0,
        )
        try:
            with st.spinner("LM Studio로 분석 결과를 생성하는 중입니다..."):
                st.session_state[AI_RESULT_KEY] = analyze_budam_with_lmstudio(
                    payload,
                    tone=tone,
                    focus=focus,
                )
                st.session_state[AI_ERROR_KEY] = ""
        except LMStudioError as exc:
            st.session_state[AI_RESULT_KEY] = None
            st.session_state[AI_ERROR_KEY] = str(exc)
        except Exception as exc:  # pragma: no cover - defensive UI fallback
            st.session_state[AI_RESULT_KEY] = None
            st.session_state[AI_ERROR_KEY] = f"AI 분석 중 예상하지 못한 오류가 발생했습니다: {exc}"

    error_message = st.session_state.get(AI_ERROR_KEY, "")
    if error_message:
        st.error(error_message)
        st.caption("LM Studio 서버 주소와 모델 로드 상태, base URL 또는 포트 설정을 확인해 주세요.")
        return

    result = st.session_state.get(AI_RESULT_KEY)
    if not result:
        st.info("분석 옵션을 선택한 뒤 `AI 분석 실행`을 누르면 현재 선택 학교와 그룹 기준 해석을 볼 수 있습니다.")
        return

    summary_col, threshold_col = st.columns([1.3, 1])
    with summary_col:
        st.markdown("**핵심 요약**")
        st.write(result["summary"] or "요약이 생성되지 않았습니다.")
    with threshold_col:
        st.markdown("**기준선 해석**")
        st.write(result["threshold_assessment"] or "기준선 해석이 생성되지 않았습니다.")

    detail_col1, detail_col2 = st.columns(2)
    with detail_col1:
        _render_analysis_list("주요 시사점", result["highlights"])
        _render_analysis_list("권고 액션", result["recommended_actions"])
    with detail_col2:
        _render_analysis_list("주의 요소", result["risks"])
        _render_analysis_list("해석 유의사항", result["caveats"])


def main() -> None:
    st.set_page_config(page_title=f"{PAGE.title} | 교육 여건 지표", page_icon=PAGE.icon, layout="wide")
    st.title(f"{PAGE.icon} {PAGE.title}")
    st.caption(APP_SUBTITLE)

    df = get_dataset(PAGE.dataset_key)
    schools = sorted(df[SCHOOL_COL].unique())
    years = sorted(df[YEAR_COL].unique())
    latest_year = max(years)
    metric = build_metric()

    sidebar_values = render_school_sidebar(
        schools=schools,
        default_schools=[PAGE.default_school] if PAGE.default_school in schools else schools[:1],
        config=SidebarConfig(
            header="필터",
            school_label="비교 학교 선택",
            school_help=f"전체 {len(schools)}개 학교 중 비교할 학교를 선택하세요.",
            meta_lines=(
                SidebarMeta(text=f"기준일: {DATA_UPDATED}"),
                SidebarMeta(text=f"전체 학교 수: {len(schools)}개"),
                SidebarMeta(text=f"분석 기간: {min(years)} ~ {latest_year}년"),
            ),
        ),
    )
    group_definitions = build_group_definitions(schools)

    selected_schools = sidebar_values["selected_schools"]
    if not selected_schools:
        st.info("사이드바에서 학교를 선택해 주세요.")
        st.stop()

    filtered_df = df[df[SCHOOL_COL].isin(selected_schools)].copy()
    if filtered_df.empty:
        st.error("선택한 학교에 해당하는 데이터가 없습니다.")
        st.stop()

    chart_df = build_chart_frame(df, selected_schools, group_definitions)
    chart_styler = build_chart_styler(selected_schools, group_definitions)
    active_groups = [name for name, school_list in group_definitions.items() if name and school_list]

    if active_groups:
        st.info(
            f"그래프에는 선택 학교, 그룹 구성 학교, 그룹 평균선이 함께 표시됩니다: {', '.join(active_groups)}"
        )
    else:
        st.caption("활성화된 그룹이 없어 현재는 선택 학교 추이만 표시됩니다.")

    render_single_metric_page(
        df=filtered_df,
        chart_df=chart_df,
        metric=metric,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        latest_year=latest_year,
        chart_title=f"{PAGE.title} 비교 추이",
        definition_rows={
            "출처": "대학알리미 공시자료 (서울 소재 사립대학)",
            "산식": "법정부담금 부담액 ÷ 법정부담금 기준액 × 100 (%)",
            "4주기 인증 기준": PAGE.threshold_note,
            "그래프 읽기": "선택 학교는 진하게, 그룹 평균은 점선으로, 그룹 학교는 색을 유지한 보조선으로 표시합니다.",
            "저구간 확대 보기": f"추가 차트에서 0 ~ {LOW_RANGE_MAX:.0f}% 범위를 확대해 낮은 부담율 구간 비교를 돕습니다.",
            "데이터 기준일": DATA_UPDATED,
        },
        kpi_threshold_suffix=f"{SERIES.threshold:.1f}% 이상",
        chart_styler=chart_styler,
    )

    render_low_range_chart(
        chart_df,
        metric=metric,
        chart_title=f"{PAGE.title} 저구간 확대 비교",
        chart_styler=chart_styler,
    )

    st.divider()
    render_ai_analysis_panel(
        df=df,
        selected_schools=selected_schools,
        group_definitions=group_definitions,
        latest_year=latest_year,
    )

    st.markdown("---")
    st.caption(f"데이터 출처: 대학알리미 | 기준일: {DATA_UPDATED}")


main()
