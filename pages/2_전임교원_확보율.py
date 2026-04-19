from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
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
from utils.chart_utils import (
    add_threshold_hline,
    add_threshold_hlines,
    create_multi_metric_line_chart,
    create_trend_line_chart,
)
from utils.config import APP_SUBTITLE, DATA_SOURCE, DATA_UPDATED
from utils.grouping import AVERAGE_LINE_SUFFIX, build_group_average_frame
from utils.query import get_dataset
from utils.theme import apply_app_theme


PAGE = get_metric("gyowon")
JEONGWON = get_series("gyowon_jeongwon")
JAEHAK = get_series("gyowon_jaehak")

YEAR_COL = "기준년도"
SCHOOL_COL = "학교명"
BRANCH_COL = "본분교명"
MAIN_BRANCH = "본교"

CUSTOM_PRESET = "사용자 정의"
GROUP_SLOT_COUNT = 3
LABEL_POSITIONS = ("middle right", "top right", "bottom right")
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


def _filter_preset_schools(schools: list[str], preset_name: str) -> list[str]:
    return [school for school in GROUP_PRESETS.get(preset_name, []) if school in schools]


def _apply_group_preset(slot: int, schools: list[str]) -> None:
    preset_key = f"gyowon_group_preset_{slot}"
    name_key = f"gyowon_group_name_{slot}"
    schools_key = f"gyowon_group_schools_{slot}"
    preset_name = st.session_state[preset_key]

    if preset_name == CUSTOM_PRESET:
        st.session_state[name_key] = st.session_state.get(name_key) or f"그룹 {slot}"
        st.session_state[schools_key] = st.session_state.get(schools_key, [])
        return

    st.session_state[name_key] = preset_name
    st.session_state[schools_key] = _filter_preset_schools(schools, preset_name)


def _ensure_group_state(slot: int, schools: list[str]) -> None:
    preset_key = f"gyowon_group_preset_{slot}"
    name_key = f"gyowon_group_name_{slot}"
    schools_key = f"gyowon_group_schools_{slot}"

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
        st.caption("그룹 평균선을 함께 보려면 비교할 학교 묶음을 지정해 주세요.")

        for slot in range(1, GROUP_SLOT_COUNT + 1):
            _ensure_group_state(slot, schools)

            with st.expander(f"그룹 {slot}", expanded=slot == 1):
                st.selectbox(
                    "프리셋",
                    options=preset_options,
                    key=f"gyowon_group_preset_{slot}",
                    help="프리셋을 선택하면 추천 그룹 구성이 자동으로 채워집니다.",
                    on_change=_apply_group_preset,
                    args=(slot, schools),
                )
                st.text_input(
                    "그룹 이름",
                    key=f"gyowon_group_name_{slot}",
                    help="그래프 평균선 이름으로 사용됩니다.",
                )
                st.multiselect(
                    "그룹 학교",
                    schools,
                    key=f"gyowon_group_schools_{slot}",
                    help="그룹에 포함할 학교를 직접 조정할 수 있습니다.",
                )

    return {
        st.session_state[f"gyowon_group_name_{slot}"].strip(): st.session_state[f"gyowon_group_schools_{slot}"]
        for slot in range(1, GROUP_SLOT_COUNT + 1)
    }


def build_chart_frame(
    df: pd.DataFrame,
    *,
    value_col: str,
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
    selected_df = selected_df[[YEAR_COL, SCHOOL_COL, value_col]]

    group_average_df = build_group_average_frame(
        df,
        year_col=YEAR_COL,
        school_col=SCHOOL_COL,
        value_col=value_col,
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

    def _apply_last_point_label(fig: go.Figure, trace: go.Scatter, text: str, color: str) -> None:
        raw_x = getattr(trace, "x", None)
        raw_y = getattr(trace, "y", None)
        x_values = list(raw_x) if raw_x is not None else []
        y_values = list(raw_y) if raw_y is not None else []
        if not x_values or not y_values:
            return

        trace.update(mode="lines+markers", cliponaxis=False)
        fig.add_annotation(
            x=1.02,
            y=y_values[-1],
            xref="paper",
            yref="y",
            text=text,
            yshift={"middle right": 0, "top right": -14, "bottom right": 14}.get(
                label_positions.get(text, "middle right"),
                0,
            ),
            showarrow=False,
            xanchor="left",
            align="left",
            font={"size": 12, "color": color},
            bgcolor="rgba(15, 23, 42, 0.0)",
            borderpad=0,
        )

    def _apply_last_point_trace_label(trace: go.Scatter, text: str, color: str) -> None:
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
            textfont={"size": 11, "color": color},
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
                _apply_last_point_label(fig, trace, trace_name, color)
                continue

            if trace_name in selected_school_set:
                color = selected_colors.get(trace_name, "#4F8CFF")
                trace.update(
                    opacity=1.0,
                    line={"width": 3.8, "color": color},
                    marker={"size": 8, "color": color},
                )
                _apply_last_point_label(fig, trace, trace_name, color)
                continue

            if trace_name in grouped_schools:
                color = grouped_colors.get(trace_name, "#94A3B8")
                trace.update(
                    opacity=0.5,
                    line={"width": 2.1, "color": color},
                    marker={"size": 5, "color": color},
                    visible="legendonly",
                )
                _apply_last_point_trace_label(trace, trace_name, color)

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


def _ordered_comparison_rows(
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


def render_focus_range_chart(
    chart_df: pd.DataFrame,
    *,
    metric: MetricSpec,
    chart_title: str,
    chart_styler,
) -> None:
    st.subheader("기준선 인근 확대 보기")
    st.caption("기준선 주변 구간을 확대해 학교 간 차이를 더 쉽게 비교할 수 있습니다.")

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

    series = chart_df[metric.value_col].dropna()
    if not series.empty:
        data_min = float(series.min())
        data_max = float(series.max())
        if metric.threshold is not None:
            lower = max(0.0, min(data_min, metric.threshold.value - 15))
            upper = max(metric.threshold.value + 20, min(data_max, metric.threshold.value + 35))
        else:
            lower = max(0.0, data_min - 10)
            upper = data_max + 10
        if upper > lower:
            fig.update_yaxes(range=[lower, upper])

    st.plotly_chart(fig, width="stretch")


def render_comparison_heatmap(
    chart_df: pd.DataFrame,
    *,
    metric: MetricSpec,
    selected_schools: list[str],
    group_definitions: dict[str, list[str]],
) -> None:
    st.subheader("학교별 확보율 히트맵")
    st.caption("연도별 확보율 강도를 색으로 보여주어 높은 학교와 낮은 학교를 빠르게 비교할 수 있습니다.")

    row_order = _ordered_comparison_rows(
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
            values=metric.value_col,
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
    max_value = float(chart_df[metric.value_col].max()) if not chart_df.empty else 100.0
    threshold_value = metric.threshold.value if metric.threshold is not None else max_value * 0.7
    threshold_ratio = min(1.0, threshold_value / max(max_value, threshold_value, 1.0))
    colorscale = [
        [0.0, "#0F172A"],
        [max(0.08, threshold_ratio * 0.45), "#1D4ED8"],
        [threshold_ratio, "#F59E0B"],
        [1.0, "#10B981"],
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
                title=dict(text="확보율 (%)", font=dict(color="#F8FBFF")),
                tickfont=dict(color="#E7EEF8"),
                bgcolor="rgba(15, 23, 42, 0.78)",
                outlinecolor="rgba(148, 163, 184, 0.18)",
            ),
            hovertemplate="학교명=%{y}<br>기준년도=%{x}<br>확보율(%)=%{z:.1f}<extra></extra>",
            xgap=3,
            ygap=3,
        )
    )
    fig.update_layout(
        title={"text": f"{metric.label} 히트맵 비교", "x": 0.02, "xanchor": "left"},
        title_font={"size": 24, "color": "#F8FBFF"},
        height=height,
        margin={"l": 40, "r": 40, "t": 56, "b": 40},
        paper_bgcolor="rgba(15, 23, 42, 0.0)",
        plot_bgcolor="rgba(15, 23, 42, 0.82)",
        font={"color": "#E5EDF7"},
    )
    fig.update_xaxes(
        title="기준년도",
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
    st.plotly_chart(fig, width="stretch")


def render_bump_chart(
    chart_df: pd.DataFrame,
    *,
    metric: MetricSpec,
    selected_schools: list[str],
    group_definitions: dict[str, list[str]],
) -> None:
    st.subheader("학교별 순위 변화 범프 차트")
    st.caption("연도별 확보율 순위 변화를 통해 선택 학교와 그룹 평균의 흐름을 살펴볼 수 있습니다.")

    average_line_names = {
        f"{group_name} {AVERAGE_LINE_SUFFIX}"
        for group_name, schools_in_group in group_definitions.items()
        if group_name and schools_in_group
    }
    show_selected_only = st.toggle(
        "선택 학교만 보기",
        value=False,
        key=f"{PAGE.id}_bump_selected_only",
        help="선택한 학교와 그룹 평균만 남기고 나머지 학교는 접습니다.",
    )

    if show_selected_only:
        visible_rows = set(chart_df[SCHOOL_COL].unique())
        row_order = [
            *[school for school in selected_schools if school in visible_rows],
            *[name for name in average_line_names if name in visible_rows],
        ]
    else:
        row_order = _ordered_comparison_rows(
            chart_df,
            selected_schools=selected_schools,
            group_definitions=group_definitions,
        )
    if not row_order:
        return

    ranking_frame = chart_df[[YEAR_COL, SCHOOL_COL, metric.value_col]].copy()
    ranking_frame["rank"] = (
        ranking_frame.groupby(YEAR_COL)[metric.value_col]
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
                hovertemplate=f"학교명={school_name}<br>기준년도=%{{x}}<br>순위=%{{y}}<extra></extra>",
                cliponaxis=False,
            )
        )

    max_rank = int(ranking_frame["rank"].max())
    fig.update_layout(
        title={"text": f"{metric.label} 순위 변화", "x": 0.02, "xanchor": "left"},
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
        title="기준년도",
        title_font={"size": 15, "color": "#F8FBFF"},
        tickfont={"size": 12, "color": "#DDE6F3"},
        showgrid=True,
        gridcolor="rgba(148, 163, 184, 0.10)",
        zeroline=False,
    )
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
    st.plotly_chart(fig, width="stretch")


def render_dual_metric_comparison(filtered_df: pd.DataFrame) -> None:
    if len(filtered_df[SCHOOL_COL].unique()) != 1:
        return

    comparison_metrics = [
        build_metric(JEONGWON),
        build_metric(JAEHAK),
    ]
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
            help="4주기 인증 기준선은 학생정원 기준일 때만 적용됩니다.",
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
    group_definitions = build_group_definitions(schools)

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
            "지표": "대학알리미 공시자료 기반 전임교원 확보율 비교 지표입니다.",
            "학생정원 기준": "학생정원을 기준으로 계산한 전임교원 확보율입니다.",
            "재학생 기준": "재학생 수를 기준으로 계산한 전임교원 확보율입니다.",
            "4주기 인증 기준": PAGE.threshold_note,
            "비교 대상 그룹": "선택 학교 외에 그룹 평균과 그룹 구성 학교를 함께 볼 수 있습니다.",
            "분교 포함": "기본은 본교만 표시하며 필요할 때 분교 포함 비교가 가능합니다.",
            "업데이트": f"{DATA_UPDATED} / {DATA_SOURCE.upper()}",
        },
        kpi_threshold_suffix=f"{selected_metric.threshold.value:.1f}% 이상" if selected_metric.threshold else "",
        chart_styler=chart_styler,
    )

    render_focus_range_chart(
        chart_df,
        metric=selected_metric,
        chart_title=f"{selected_metric.label} 기준선 인근 확대 비교",
        chart_styler=chart_styler,
    )

    render_comparison_heatmap(
        chart_df,
        metric=selected_metric,
        selected_schools=selected_schools,
        group_definitions=group_definitions,
    )

    render_bump_chart(
        chart_df,
        metric=selected_metric,
        selected_schools=selected_schools,
        group_definitions=group_definitions,
    )

    render_dual_metric_comparison(filtered_df)

    st.markdown("---")
    st.caption(f"데이터 출처: 대학알리미 | 업데이트: {DATA_UPDATED}")


main()
