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
from utils.auth import require_authenticated_user
from utils.chart_utils import add_threshold_hline, create_trend_line_chart
from utils.comparison_charts import apply_right_label_xaxis_padding
from utils.comparison_sidebar import build_group_definitions as build_shared_group_definitions
from utils.config import APP_SUBTITLE, DATA_UPDATED
from utils.grouping import AVERAGE_LINE_SUFFIX, build_group_average_frame
from utils.query import get_dataset
from utils.theme import (
    apply_app_theme,
    disable_mobile_plotly_zoom,
    get_plotly_chart_config,
    is_mobile_compact_mode,
)


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


def _plotly_config() -> dict[str, object]:
    return get_plotly_chart_config()


def _resolve_column_name(df: pd.DataFrame, preferred: str, aliases: list[str]) -> str:
    for candidate in [preferred, *aliases]:
        if candidate in df.columns:
            return candidate

    normalized_map = {
        str(column).replace(" ", "").replace("_", ""): column
        for column in df.columns
    }
    for candidate in [preferred, *aliases]:
        normalized = candidate.replace(" ", "").replace("_", "")
        if normalized in normalized_map:
            return normalized_map[normalized]

    raise KeyError(f"'{preferred}' column was not found in dataset columns: {list(df.columns)}")


def build_metric() -> MetricSpec:
    return MetricSpec(
        key=SERIES.id,
        label=SERIES.label,
        value_col=SERIES.column,
        y_axis_label=f"{SERIES.label} ({SERIES.unit})",
        precision=SERIES.decimals,
        threshold=ThresholdSpec(
            value=SERIES.threshold or 0.0,
            label=SERIES.threshold_label or "기준값",
            color="#F59E0B",
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
    return build_shared_group_definitions(
        schools,
        key_prefix="budam",
        title="비교 대상 그룹",
        caption="프리셋으로 시작한 뒤 그룹 이름과 학교 목록을 자유롭게 조정할 수 있습니다.",
        group_presets=GROUP_PRESETS,
        default_slot_presets=DEFAULT_SLOT_PRESETS,
        custom_preset_label=CUSTOM_PRESET,
        slot_count=GROUP_SLOT_COUNT,
        preset_help="프리셋을 선택하면 추천 그룹 이름과 학교 목록이 채워집니다.",
        group_name_help="그래프 평균선 이름으로 사용됩니다.",
        group_schools_help="이 그룹에 포함할 학교를 직접 추가하거나 제외할 수 있습니다.",
        default_group_name_template="그룹 {slot}",
    )


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

    selected_palette = ["#6EA8FF", "#FF9A4D", "#4ADE80", "#C084FC", "#FF6B9A", "#67E8F9"]
    selected_colors = {
        school_name: selected_palette[index % len(selected_palette)]
        for index, school_name in enumerate(selected_schools)
    }
    grouped_palette = [
        "#8EC5FF",
        "#FDBA74",
        "#86EFAC",
        "#F9A8D4",
        "#C4B5FD",
        "#7DD3FC",
        "#FDE68A",
        "#93C5FD",
        "#FCA5A5",
        "#A7F3D0",
        "#D8B4FE",
        "#BFDBFE",
    ]
    grouped_colors = {
        school_name: grouped_palette[index % len(grouped_palette)]
        for index, school_name in enumerate(grouped_school_names)
    }
    average_palette = ["#FFD166", "#D8B4FE", "#FDBA74"]
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

    def _apply_last_point_label(trace: go.Scatter, text: str, color: str) -> None:
        raw_x = getattr(trace, "x", None)
        if raw_x is None:
            return

        point_count = len(list(raw_x))
        if point_count == 0:
            return

        labels = [""] * point_count
        labels[-1] = text
        trace.update(
            mode="lines+markers+text",
            text=labels,
            textposition=label_positions.get(text, "middle right"),
            textfont={"size": 12, "color": color},
            cliponaxis=False,
        )

    def _apply_last_point_trace_label(trace: go.Scatter, text: str) -> None:
        raw_x = getattr(trace, "x", None)
        if raw_x is None:
            return

        point_count = len(list(raw_x))
        if point_count == 0:
            return

        labels = [""] * point_count
        labels[-1] = text
        trace_color = getattr(getattr(trace, "line", None), "color", None) or "#E7EEF8"
        trace.update(
            mode="lines+markers+text",
            text=labels,
            textposition=label_positions.get(text, "middle right"),
            textfont={"size": 11, "color": trace_color},
            cliponaxis=False,
        )

    def _style(fig: go.Figure) -> None:
        for trace in fig.data:
            trace_name = getattr(trace, "name", "") or ""

            if trace_name in average_line_names:
                color = average_colors.get(trace_name, "#F6C453")
                trace.update(
                    opacity=1.0,
                    line={"width": 3.2, "dash": "dash", "color": color},
                    marker={"size": 7, "color": color},
                )
                _apply_last_point_label(trace, trace_name, color)
                continue

            if trace_name in selected_school_set:
                color = selected_colors.get(trace_name, "#4F8CFF")
                trace.update(
                    opacity=1.0,
                    line={"width": 3.8, "color": color},
                    marker={"size": 8, "color": color},
                )
                _apply_last_point_label(trace, trace_name, color)
                continue

            if trace_name in grouped_schools:
                color = grouped_colors.get(trace_name, "#94A3B8")
                trace.update(
                    opacity=0.5,
                    line={"width": 2.1, "color": color},
                    marker={"size": 5, "color": color},
                    visible="legendonly",
                )
                _apply_last_point_trace_label(trace, trace_name)

        fig.update_layout(
            title={"x": 0.02, "xanchor": "left"},
            plot_bgcolor="rgba(15, 23, 42, 0.82)",
            paper_bgcolor="rgba(15, 23, 42, 0.0)",
            hovermode="closest",
            margin={"r": 220, "b": 132, "t": 56},
            legend={
                "orientation": "h",
                "yanchor": "top",
                "y": -0.18,
                "xanchor": "left",
                "x": 0,
                "font": {"size": 11, "color": "#F8FBFF"},
                "title_font": {"size": 12, "color": "#F6C453"},
            },
            title_font={"size": 24, "color": "#F8FBFF"},
            font={"color": "#E5EDF7"},
        )
        fig.update_xaxes(
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
            title_font={"size": 15, "color": "#F8FBFF"},
            tickfont={"size": 12, "color": "#DDE6F3"},
            gridcolor="rgba(148, 163, 184, 0.10)",
            zeroline=False,
        )
        apply_right_label_xaxis_padding(fig)
        fig.update_yaxes(
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
            title_font={"size": 15, "color": "#F8FBFF"},
            tickfont={"size": 12, "color": "#DDE6F3"},
            gridcolor="rgba(148, 163, 184, 0.10)",
            zeroline=False,
        )

    return _style


def _ordered_heatmap_rows(
    chart_df: pd.DataFrame,
    *,
    selected_schools: list[str],
    group_definitions: dict[str, list[str]],
) -> list[str]:
    average_line_names = [
        f"{group_name} {AVERAGE_LINE_SUFFIX}"
        for group_name, schools_in_group in group_definitions.items()
        if group_name and schools_in_group
    ]
    grouped_school_names = sorted(
        {
            school
            for schools_in_group in group_definitions.values()
            for school in schools_in_group
        }
        - set(selected_schools)
    )
    visible_rows = set(chart_df[SCHOOL_COL].unique())
    return [
        *[school for school in selected_schools if school in visible_rows],
        *[line_name for line_name in average_line_names if line_name in visible_rows],
        *[school for school in grouped_school_names if school in visible_rows],
    ]


def render_comparison_heatmap(
    chart_df: pd.DataFrame,
    *,
    selected_schools: list[str],
    group_definitions: dict[str, list[str]],
) -> None:
    st.subheader("학교별 부담율 히트맵")
    st.caption("연도별 부담율 강도를 색으로 보여줘서, 어느 학교가 높은지 낮은지 빠르게 비교할 수 있습니다.")

    row_order = _ordered_heatmap_rows(
        chart_df,
        selected_schools=selected_schools,
        group_definitions=group_definitions,
    )
    if not row_order:
        return

    heatmap_frame = (
        chart_df.pivot_table(
            index=SCHOOL_COL,
            columns=YEAR_COL,
            values=VALUE_COL,
            aggfunc="mean",
        )
        .reindex(row_order)
        .dropna(how="all")
    )
    if heatmap_frame.empty:
        return

    years = list(heatmap_frame.columns)
    schools = list(heatmap_frame.index)
    height = max(420, 42 * len(schools) + 120)
    max_value = float(chart_df[VALUE_COL].max()) if not chart_df.empty else 100.0
    threshold_value = SERIES.threshold or 10.0
    threshold_ratio = min(1.0, threshold_value / max(max_value, threshold_value))
    colorscale = [
        [0.0, "#0F172A"],
        [max(0.08, threshold_ratio * 0.45), "#1D4ED8"],
        [threshold_ratio, "#F59E0B"],
        [1.0, "#EF4444"],
    ]

    fig = go.Figure(
        data=go.Heatmap(
            z=heatmap_frame.values,
            x=years,
            y=schools,
            colorscale=colorscale,
            zmin=0,
            zmax=max(max_value, threshold_value),
            colorbar=dict(
                title=dict(text="부담율 (%)", font=dict(color="#F8FBFF")),
                tickfont=dict(color="#E7EEF8"),
                bgcolor="rgba(15, 23, 42, 0.78)",
                outlinecolor="rgba(148, 163, 184, 0.18)",
            ),
            hovertemplate="학교명=%{y}<br>기준연도=%{x}<br>부담율(%)=%{z:.1f}<extra></extra>",
            xgap=3,
            ygap=3,
        )
    )
    fig.update_layout(
        title={"text": f"{PAGE.title} 히트맵 비교", "x": 0.02, "xanchor": "left"},
        title_font={"size": 24, "color": "#F8FBFF"},
        height=height,
        margin={"l": 40, "r": 40, "t": 56, "b": 40},
        paper_bgcolor="rgba(15, 23, 42, 0.0)",
        plot_bgcolor="rgba(15, 23, 42, 0.82)",
        font={"color": "#E5EDF7"},
    )
    fig.update_xaxes(
        title="기준연도",
        title_font={"size": 15, "color": "#F8FBFF"},
        tickfont={"size": 12, "color": "#DDE6F3"},
        side="top",
        showgrid=False,
    )
    fig.update_yaxes(
        title="학교명",
        title_font={"size": 15, "color": "#F8FBFF"},
        tickfont={"size": 12, "color": "#E7EEF8"},
        autorange="reversed",
    )
    disable_mobile_plotly_zoom(fig)
    st.plotly_chart(fig, use_container_width=True, config=_plotly_config())


def render_bump_chart(
    chart_df: pd.DataFrame,
    *,
    selected_schools: list[str],
    group_definitions: dict[str, list[str]],
) -> None:
    st.subheader("학교별 순위 변화 범프 차트")
    st.caption("연도별 부담율 순위 변화를 보여줘서, 선택 학교와 그룹 평균이 상위권인지 하위권인지 흐름으로 확인할 수 있습니다.")

    average_line_names = {
        f"{group_name} {AVERAGE_LINE_SUFFIX}"
        for group_name, schools_in_group in group_definitions.items()
        if group_name and schools_in_group
    }
    show_selected_only = st.toggle(
        "선택 학교만 보기",
        value=False,
        key="budam_bump_selected_only",
        help="켜면 선택 학교와 그룹 평균선만 남기고, 나머지 그룹 학교는 숨깁니다.",
    )

    if show_selected_only:
        row_order = [
            *selected_schools,
            *[line_name for line_name in average_line_names if line_name in chart_df[SCHOOL_COL].unique()],
        ]
    else:
        row_order = _ordered_heatmap_rows(
            chart_df,
            selected_schools=selected_schools,
            group_definitions=group_definitions,
        )
    if not row_order:
        return

    ranking_frame = chart_df[[YEAR_COL, SCHOOL_COL, VALUE_COL]].copy()
    ranking_frame["rank"] = (
        ranking_frame.groupby(YEAR_COL)[VALUE_COL]
        .rank(method="dense", ascending=False)
        .astype(int)
    )
    ranking_frame = ranking_frame[ranking_frame[SCHOOL_COL].isin(row_order)].copy()
    if ranking_frame.empty:
        return

    selected_palette = ["#7CB8FF", "#FFAE66", "#5AF08D", "#D09CFF", "#FF85AD", "#7CEBFF"]
    selected_colors = {
        school_name: selected_palette[index % len(selected_palette)]
        for index, school_name in enumerate(selected_schools)
    }
    grouped_school_names = sorted(
        {
            school
            for schools_in_group in group_definitions.values()
            for school in schools_in_group
        }
        - set(selected_schools)
    )
    grouped_palette = [
        "#8EC5FF",
        "#FDBA74",
        "#86EFAC",
        "#F9A8D4",
        "#C4B5FD",
        "#7DD3FC",
        "#FDE68A",
        "#93C5FD",
        "#FCA5A5",
        "#A7F3D0",
        "#D8B4FE",
        "#BFDBFE",
    ]
    grouped_colors = {
        school_name: grouped_palette[index % len(grouped_palette)]
        for index, school_name in enumerate(grouped_school_names)
    }
    average_palette = ["#FFD76A", "#E2C1FF", "#FFC98B"]
    average_colors = {
        line_name: average_palette[index % len(average_palette)]
        for index, line_name in enumerate(sorted(average_line_names))
    }

    fig = go.Figure()
    label_positions = {}
    label_cycle = ("middle right", "top right", "bottom right")
    for index, name in enumerate(row_order):
        label_positions[name] = label_cycle[index % len(label_cycle)]

    for school_name in row_order:
        school_frame = ranking_frame[ranking_frame[SCHOOL_COL] == school_name].sort_values(YEAR_COL)
        if school_frame.empty:
            continue

        is_selected = school_name in selected_schools
        is_average = school_name in average_line_names
        color = grouped_colors.get(school_name, "#A8B6CC")
        width = 2.0
        dash = "solid"
        opacity = 0.52
        marker_size = 7

        if is_average:
            color = average_colors.get(school_name, "#F6C453")
            width = 3.2
            dash = "dash"
            opacity = 1.0
            marker_size = 8
        elif is_selected:
            color = selected_colors.get(school_name, "#4F8CFF")
            width = 3.8
            opacity = 1.0
            marker_size = 8

        labels = [""] * len(school_frame)
        if len(school_frame) > 0:
            labels[-1] = school_name

        hover_name = school_name
        is_default_visible = show_selected_only or is_average or is_selected
        fig.add_trace(
            go.Scatter(
                x=school_frame[YEAR_COL],
                y=school_frame["rank"],
                mode="lines+markers+text",
                name=school_name,
                text=labels,
                textposition=label_positions.get(school_name, "middle right"),
                textfont={"size": 11, "color": color},
                line={"color": color, "width": width, "dash": dash},
                marker={"size": marker_size, "color": color},
                opacity=opacity,
                visible=True if is_default_visible else "legendonly",
                hovertemplate=(
                    f"학교명={hover_name}<br>기준연도=%{{x}}<br>순위=%{{y}}위<extra></extra>"
                ),
                cliponaxis=False,
            )
        )

    max_rank = int(ranking_frame["rank"].max())
    fig.update_layout(
        title={"text": f"{PAGE.title} 순위 변화", "x": 0.02, "xanchor": "left"},
        title_font={"size": 24, "color": "#F8FBFF"},
        height=max(440, 38 * len(row_order) + 120),
        margin={"l": 40, "r": 180, "t": 56, "b": 132},
        paper_bgcolor="rgba(15, 23, 42, 0.0)",
        plot_bgcolor="rgba(15, 23, 42, 0.82)",
        font={"color": "#E5EDF7"},
        hovermode="closest",
        legend={
            "orientation": "h",
            "yanchor": "top",
            "y": -0.18,
            "xanchor": "left",
            "x": 0,
            "bgcolor": "rgba(15, 23, 42, 0.72)",
            "bordercolor": "rgba(148, 163, 184, 0.16)",
            "borderwidth": 1,
            "font": {"size": 11, "color": "#F8FBFF"},
            "title": {"text": "학교명", "font": {"size": 12, "color": "#F6C453"}},
        },
    )
    fig.update_xaxes(
        title="기준연도",
        title_font={"size": 15, "color": "#F8FBFF"},
        tickfont={"size": 12, "color": "#DDE6F3"},
        showgrid=True,
        gridcolor="rgba(148, 163, 184, 0.10)",
        zeroline=False,
    )
    apply_right_label_xaxis_padding(fig)
    fig.update_yaxes(
        title="순위",
        title_font={"size": 15, "color": "#F8FBFF"},
        tickfont={"size": 12, "color": "#DDE6F3"},
        autorange="reversed",
        dtick=1,
        range=[max_rank + 0.5, 0.5],
        showgrid=True,
        gridcolor="rgba(148, 163, 184, 0.10)",
        zeroline=False,
    )
    disable_mobile_plotly_zoom(fig)
    st.plotly_chart(fig, use_container_width=True, config=_plotly_config())


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
            color=metric.threshold.color or "#F59E0B",
            dash=metric.threshold.dash,
        )
    chart_styler(fig)
    fig.update_yaxes(range=[0, LOW_RANGE_MAX])
    disable_mobile_plotly_zoom(fig)
    st.plotly_chart(fig, use_container_width=True, config=_plotly_config())


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

    if is_mobile_compact_mode():
        tone = st.selectbox("분석 톤", ["보고서형", "간결형"], key="budam_ai_tone")
        focus = st.selectbox("분석 초점", ["선택 학교 중심", "그룹 비교 중심"], key="budam_ai_focus")
        run_analysis = st.button("AI 분석 실행", width="stretch", type="primary")
    else:
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

    if is_mobile_compact_mode():
        st.markdown("**핵심 요약**")
        st.write(result["summary"] or "요약이 생성되지 않았습니다.")
        st.markdown("**기준선 해석**")
        st.write(result["threshold_assessment"] or "기준선 해석이 생성되지 않았습니다.")

        st.markdown("**경영 시사점**")
        management_implications = result.get("management_implications", [])
        if management_implications:
            for item in management_implications:
                st.markdown(f"- {item}")
        else:
            st.caption("경영 시사점이 생성되지 않았습니다.")

        _render_analysis_list("주요 시사점", result["highlights"])
        _render_analysis_list("권고 액션", result["recommended_actions"])
        _render_analysis_list("주의 요소", result["risks"])
        _render_analysis_list("해석 유의사항", result["caveats"])
        return

    summary_col, threshold_col = st.columns([1.3, 1])
    with summary_col:
        st.markdown("**핵심 요약**")
        st.write(result["summary"] or "요약이 생성되지 않았습니다.")
    with threshold_col:
        st.markdown("**기준선 해석**")
        st.write(result["threshold_assessment"] or "기준선 해석이 생성되지 않았습니다.")

    st.markdown("**경영 시사점**")
    management_implications = result.get("management_implications", [])
    if management_implications:
        for item in management_implications:
            st.markdown(f"- {item}")
    else:
        st.caption("경영 시사점이 생성되지 않았습니다.")

    detail_col1, detail_col2 = st.columns(2)
    with detail_col1:
        _render_analysis_list("주요 시사점", result["highlights"])
        _render_analysis_list("권고 액션", result["recommended_actions"])
    with detail_col2:
        _render_analysis_list("주의 요소", result["risks"])
        _render_analysis_list("해석 유의사항", result["caveats"])


def main() -> None:
    global YEAR_COL, SCHOOL_COL, VALUE_COL

    st.set_page_config(page_title=f"{PAGE.title} | 교육 여건 지표", page_icon=PAGE.icon, layout="wide")
    require_authenticated_user()
    apply_app_theme()
    st.title(f"{PAGE.icon} {PAGE.title}")
    st.caption(APP_SUBTITLE)

    df = get_dataset(PAGE.dataset_key)
    YEAR_COL = _resolve_column_name(df, "기준년도", ["기준연도"])
    SCHOOL_COL = _resolve_column_name(df, "학교명", [])
    VALUE_COL = _resolve_column_name(df, SERIES.column, ["부담율", "부담률"])
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
        selected_schools=selected_schools,
        definition_rows={
            "출처": "대학알리미 공시자료 (서울 소재 사립대학)",
            "산식": "법정부담금 부담액 ÷ 법정부담금 기준액 × 100 (%)",
            "4주기 인증 기준": PAGE.threshold_note,
            "그래프 읽기": "선택 학교는 진하게, 그룹 평균은 점선으로, 그룹 학교는 보조선으로 표시합니다.",
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

    render_comparison_heatmap(
        chart_df,
        selected_schools=selected_schools,
        group_definitions=group_definitions,
    )

    render_bump_chart(
        chart_df,
        selected_schools=selected_schools,
        group_definitions=group_definitions,
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
