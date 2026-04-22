from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ui import MetricSpec
from utils.chart_utils import add_threshold_hline, create_trend_line_chart
from utils.grouping import AVERAGE_LINE_SUFFIX, build_group_average_frame


ChartStyler = Callable[[go.Figure], None]
FocusRangeResolver = Callable[[pd.Series, MetricSpec], tuple[float, float] | None]

DEFAULT_SELECTED_PALETTE = ["#6EA8FF", "#FF9A4D", "#4ADE80", "#C084FC", "#FF6B9A", "#67E8F9"]
DEFAULT_GROUPED_PALETTE = [
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
DEFAULT_AVERAGE_PALETTE = ["#FFD166", "#D8B4FE", "#FDBA74"]
DEFAULT_LABEL_POSITIONS = ("middle right", "top right", "bottom right")
RIGHT_LABEL_X_PADDING_RATIO = 0.16
RIGHT_LABEL_X_PADDING_MIN = 0.35
RIGHT_LABEL_X_PADDING_PER_CHAR_RATIO = 0.035
RIGHT_LABEL_X_PADDING_MAX_RATIO = 0.5


def apply_right_label_xaxis_padding(
    fig: go.Figure,
    *,
    pad_ratio: float = RIGHT_LABEL_X_PADDING_RATIO,
    min_pad: float = RIGHT_LABEL_X_PADDING_MIN,
) -> None:
    """Leave room for trace-bound labels at the final x-value."""
    x_values: list[float] = []
    max_label_length = 0
    for trace in fig.data:
        if getattr(trace, "visible", None) is False:
            continue

        raw_x = getattr(trace, "x", None)
        if raw_x is None:
            continue

        for value in raw_x:
            try:
                numeric_value = float(value)
            except (TypeError, ValueError):
                continue
            if pd.isna(numeric_value):
                continue
            x_values.append(numeric_value)

        raw_text = getattr(trace, "text", None)
        if isinstance(raw_text, str):
            max_label_length = max(max_label_length, len(raw_text))
        elif raw_text is not None:
            for label in reversed(list(raw_text)):
                if label:
                    max_label_length = max(max_label_length, len(str(label)))
                    break

    if not x_values:
        return

    x_min = min(x_values)
    x_max = max(x_values)
    span = x_max - x_min
    label_pad = span * RIGHT_LABEL_X_PADDING_PER_CHAR_RATIO * max_label_length
    right_pad = max(span * pad_ratio, label_pad, min_pad)
    if span > 0:
        right_pad = min(right_pad, max(span * RIGHT_LABEL_X_PADDING_MAX_RATIO, min_pad))
    left_pad = max(span * 0.03, min_pad * 0.2)
    fig.update_xaxes(range=[x_min - left_pad, x_max + right_pad])


def build_chart_frame(
    df: pd.DataFrame,
    *,
    year_col: str,
    school_col: str,
    value_col: str,
    selected_schools: Sequence[str],
    group_definitions: Mapping[str, Sequence[str]],
) -> pd.DataFrame:
    grouped_schools = sorted(
        {
            school
            for schools_in_group in group_definitions.values()
            for school in schools_in_group
        }
    )
    visible_schools = sorted(set(selected_schools) | set(grouped_schools))
    selected_df = df[df[school_col].isin(visible_schools)].copy()
    selected_df = selected_df[[year_col, school_col, value_col]]

    group_average_df = build_group_average_frame(
        df,
        year_col=year_col,
        school_col=school_col,
        value_col=value_col,
        groups=group_definitions,
    )
    if group_average_df.empty:
        return selected_df

    return pd.concat([selected_df, group_average_df], ignore_index=True)


def build_chart_styler(
    selected_schools: Sequence[str],
    group_definitions: Mapping[str, Sequence[str]],
    *,
    selected_palette: Sequence[str] = DEFAULT_SELECTED_PALETTE,
    grouped_palette: Sequence[str] = DEFAULT_GROUPED_PALETTE,
    average_palette: Sequence[str] = DEFAULT_AVERAGE_PALETTE,
    label_positions: Sequence[str] = DEFAULT_LABEL_POSITIONS,
    show_grouped_schools: bool = False,
    label_grouped_schools: bool = True,
) -> ChartStyler:
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

    selected_colors = {
        school_name: selected_palette[index % len(selected_palette)]
        for index, school_name in enumerate(selected_schools)
    }
    grouped_colors = {
        school_name: grouped_palette[index % len(grouped_palette)]
        for index, school_name in enumerate(grouped_school_names)
    }
    average_colors = {
        line_name: average_palette[index % len(average_palette)]
        for index, line_name in enumerate(sorted(average_line_names))
    }
    position_map = {
        line_name: label_positions[index % len(label_positions)]
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
            textposition=position_map.get(text, "middle right"),
            textfont={"size": 12, "color": color},
            cliponaxis=False,
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
            textposition=position_map.get(text, "middle right"),
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
                    visible=True if show_grouped_schools else "legendonly",
                )
                if label_grouped_schools:
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


def _ordered_comparison_rows(
    chart_df: pd.DataFrame,
    *,
    school_col: str,
    selected_schools: Sequence[str],
    group_definitions: Mapping[str, Sequence[str]],
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
    visible_rows = set(chart_df[school_col].unique())
    return [
        *[school for school in selected_schools if school in visible_rows],
        *[line_name for line_name in average_line_names if line_name in visible_rows],
        *[school for school in grouped_school_names if school in visible_rows],
    ]


def _default_focus_range_resolver(series: pd.Series, metric: MetricSpec) -> tuple[float, float] | None:
    if series.empty:
        return None
    data_min = float(series.min())
    data_max = float(series.max())
    threshold = metric.threshold.value if metric.threshold else 0.0
    lower = max(0.0, min(data_min, threshold - 20))
    upper = max(data_max, threshold + 20)
    if upper <= lower:
        return None
    return lower, upper


def _unit_from_metric(metric: MetricSpec) -> str:
    label = metric.y_axis_label
    if "(" in label and label.endswith(")"):
        return label.rsplit("(", 1)[1].removesuffix(")").strip()
    return "%"


def render_focus_range_chart(
    chart_df: pd.DataFrame,
    *,
    metric: MetricSpec,
    year_col: str,
    school_col: str,
    chart_title: str,
    chart_styler: ChartStyler,
    title: str,
    caption: str,
    range_resolver: FocusRangeResolver | None = None,
) -> None:
    st.subheader(title)
    st.caption(caption)

    fig = create_trend_line_chart(
        chart_df,
        x=year_col,
        y=metric.value_col,
        color=school_col,
        title=chart_title,
        x_label=year_col,
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
    resolver = range_resolver or _default_focus_range_resolver
    resolved_range = resolver(series, metric)
    if resolved_range is not None:
        fig.update_yaxes(range=list(resolved_range))

    st.plotly_chart(fig, width="stretch")


def render_comparison_heatmap(
    chart_df: pd.DataFrame,
    *,
    metric: MetricSpec,
    year_col: str,
    school_col: str,
    selected_schools: Sequence[str],
    group_definitions: Mapping[str, Sequence[str]],
    title: str,
    caption: str,
    hover_value_label: str,
) -> None:
    st.subheader(title)
    st.caption(caption)

    row_order = _ordered_comparison_rows(
        chart_df,
        school_col=school_col,
        selected_schools=selected_schools,
        group_definitions=group_definitions,
    )
    if not row_order:
        return

    heatmap_frame = (
        chart_df.pivot_table(
            index=school_col,
            columns=year_col,
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
    min_value = float(chart_df[metric.value_col].min()) if not chart_df.empty else 0.0
    max_value = float(chart_df[metric.value_col].max()) if not chart_df.empty else 100.0
    threshold_value = metric.threshold.value if metric.threshold is not None else max_value * 0.7
    threshold_ratio = (threshold_value - min_value) / max(max_value - min_value, 1.0)
    threshold_ratio = min(1.0, max(0.0, threshold_ratio))
    unit = _unit_from_metric(metric)

    if metric.higher_is_better:
        colorscale = [
            [0.0, "#0F172A"],
            [max(0.08, threshold_ratio * 0.45), "#1D4ED8"],
            [threshold_ratio, "#F59E0B"],
            [1.0, "#10B981"],
        ]
    else:
        colorscale = [
            [0.0, "#10B981"],
            [max(0.08, threshold_ratio * 0.75), "#38BDF8"],
            [threshold_ratio, "#F59E0B"],
            [1.0, "#F97316"],
        ]

    fig = go.Figure(
        data=go.Heatmap(
            z=heatmap_frame.values,
            x=years,
            y=schools,
            colorscale=colorscale,
            zmin=min_value,
            zmax=max(max_value, threshold_value),
            colorbar=dict(
                title=dict(text=f"{metric.label} ({unit})", font=dict(color="#F8FBFF")),
                tickfont=dict(color="#E7EEF8"),
                bgcolor="rgba(15, 23, 42, 0.78)",
                outlinecolor="rgba(148, 163, 184, 0.18)",
            ),
            hovertemplate=f"학교명=%{{y}}<br>기준년도=%{{x}}<br>{hover_value_label}=%{{z:.2f}}<extra></extra>",
            xgap=3,
            ygap=3,
        )
    )
    fig.update_layout(
        title={"text": title, "x": 0.02, "xanchor": "left"},
        title_font={"size": 24, "color": "#F8FBFF"},
        height=height,
        margin={"l": 40, "r": 40, "t": 56, "b": 40},
        paper_bgcolor="rgba(15, 23, 42, 0.0)",
        plot_bgcolor="rgba(15, 23, 42, 0.82)",
        font={"color": "#E5EDF7"},
    )
    fig.update_xaxes(
        title=year_col,
        title_font={"size": 15, "color": "#F8FBFF"},
        tickfont={"size": 12, "color": "#DDE6F3"},
        side="top",
        showgrid=False,
    )
    fig.update_yaxes(
        title=school_col,
        title_font={"size": 15, "color": "#F8FBFF"},
        tickfont={"size": 12, "color": "#E7EEF8"},
        autorange="reversed",
    )
    st.plotly_chart(fig, width="stretch")


def render_bump_chart(
    chart_df: pd.DataFrame,
    *,
    metric: MetricSpec,
    year_col: str,
    school_col: str,
    selected_schools: Sequence[str],
    group_definitions: Mapping[str, Sequence[str]],
    title: str,
    caption: str,
    toggle_key: str,
    toggle_label: str = "선택 학교만 보기",
    toggle_help: str = "선택 학교와 그룹 평균만 우선적으로 볼 수 있습니다.",
) -> None:
    st.subheader(title)
    st.caption(caption)

    average_line_names = {
        f"{group_name} {AVERAGE_LINE_SUFFIX}"
        for group_name, schools_in_group in group_definitions.items()
        if group_name and schools_in_group
    }
    show_selected_only = st.toggle(
        toggle_label,
        value=False,
        key=toggle_key,
        help=toggle_help,
    )

    if show_selected_only:
        visible_rows = set(chart_df[school_col].unique())
        row_order = [
            *[school for school in selected_schools if school in visible_rows],
            *[name for name in average_line_names if name in visible_rows],
        ]
    else:
        row_order = _ordered_comparison_rows(
            chart_df,
            school_col=school_col,
            selected_schools=selected_schools,
            group_definitions=group_definitions,
        )
    if not row_order:
        return

    ranking_frame = chart_df[[year_col, school_col, metric.value_col]].copy()
    ranking_frame["rank"] = (
        ranking_frame.groupby(year_col)[metric.value_col]
        .rank(method="dense", ascending=not metric.higher_is_better)
        .astype(int)
    )
    ranking_frame = ranking_frame[ranking_frame[school_col].isin(row_order)].copy()
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
    grouped_colors = {
        school_name: DEFAULT_GROUPED_PALETTE[index % len(DEFAULT_GROUPED_PALETTE)]
        for index, school_name in enumerate(grouped_school_names)
    }
    average_colors = {
        line_name: DEFAULT_AVERAGE_PALETTE[index % len(DEFAULT_AVERAGE_PALETTE)]
        for index, line_name in enumerate(sorted(average_line_names))
    }

    fig = go.Figure()
    position_map = {}
    for index, name in enumerate(row_order):
        position_map[name] = DEFAULT_LABEL_POSITIONS[index % len(DEFAULT_LABEL_POSITIONS)]

    for school_name in row_order:
        school_frame = ranking_frame[ranking_frame[school_col] == school_name].sort_values(year_col)
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
        labels[-1] = school_name

        is_default_visible = show_selected_only or is_average or is_selected
        fig.add_trace(
            go.Scatter(
                x=school_frame[year_col],
                y=school_frame["rank"],
                mode="lines+markers+text",
                name=school_name,
                text=labels,
                textposition=position_map.get(school_name, "middle right"),
                textfont={"size": 11, "color": color},
                line={"color": color, "width": width, "dash": dash},
                marker={"size": marker_size, "color": color},
                opacity=opacity,
                visible=True if is_default_visible else "legendonly",
                hovertemplate=f"학교명={school_name}<br>{year_col}=%{{x}}<br>순위=%{{y}}<extra></extra>",
                cliponaxis=False,
            )
        )

    max_rank = int(ranking_frame["rank"].max())
    fig.update_layout(
        title={"text": title, "x": 0.02, "xanchor": "left"},
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
        title=year_col,
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
    st.plotly_chart(fig, width="stretch")
