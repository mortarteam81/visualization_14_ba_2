"""
공통 차트 생성 유틸리티
- 모든 지표 페이지에서 재사용할 수 있는 함수 모음
"""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.config import CHART_HEIGHT, CHART_THRESHOLD_COLOR, CHART_TEMPLATE


def create_trend_line_chart(
    df,
    x: str,
    y: str,
    color: str,
    title: str,
    x_label: str = "",
    y_label: str = "",
    height: int = CHART_HEIGHT,
    hovermode: str = "x unified",
) -> go.Figure:
    """
    연도별 추이 라인 차트 생성.

    Parameters
    ----------
    df      : 시각화할 DataFrame
    x       : x축 컬럼명
    y       : y축 컬럼명
    color   : 색상 구분 컬럼명 (학교명 등)
    title   : 차트 제목
    x_label : x축 레이블 (생략 시 컬럼명 사용)
    y_label : y축 레이블 (생략 시 컬럼명 사용)
    height  : 차트 높이(px)
    """
    fig = px.line(
        df,
        x=x,
        y=y,
        color=color,
        title=title,
        labels={y: y_label or y, x: x_label or x},
        markers=True,
        template=CHART_TEMPLATE,
    )
    fig.update_layout(
        hovermode=hovermode,
        title_font=dict(size=24, color="#F8FBFF"),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.18,
            xanchor="left",
            x=0,
            bgcolor="rgba(15, 23, 42, 0.72)",
            bordercolor="rgba(148, 163, 184, 0.16)",
            borderwidth=1,
            font=dict(size=11, color="#E7EEF8"),
            title_font=dict(size=12, color="#F6C453"),
        ),
        height=height,
        paper_bgcolor="rgba(15, 23, 42, 0.0)",
        plot_bgcolor="rgba(15, 23, 42, 0.82)",
        font=dict(color="#E5EDF7"),
        margin=dict(l=40, r=40, t=56, b=132),
    )
    fig.update_xaxes(
        title_font=dict(size=15, color="#F8FBFF"),
        tickfont=dict(size=12, color="#DDE6F3"),
        showgrid=True,
        gridcolor="rgba(148, 163, 184, 0.10)",
        zeroline=False,
        linecolor="rgba(148, 163, 184, 0.18)",
    )
    fig.update_yaxes(
        title_font=dict(size=15, color="#F8FBFF"),
        tickfont=dict(size=12, color="#DDE6F3"),
        showgrid=True,
        gridcolor="rgba(148, 163, 184, 0.10)",
        zeroline=False,
        linecolor="rgba(148, 163, 184, 0.18)",
    )
    return fig


def add_threshold_hline(
    fig: go.Figure,
    threshold: float,
    label: str,
    color: str = CHART_THRESHOLD_COLOR,
    dash: str = "dash",
) -> go.Figure:
    """
    차트에 기준값 수평선 추가.

    Parameters
    ----------
    fig       : 대상 Figure
    threshold : 기준값
    label     : 주석 텍스트
    color     : 선 색상
    dash      : 선 스타일 ('dash', 'dot', 'solid' 등)
    """
    fig.add_hline(
        y=threshold,
        line_dash=dash,
        line_color=color,
        annotation_text=label,
        annotation_position="top right",
    )
    return fig


def add_threshold_hlines(
    fig: go.Figure,
    thresholds: Sequence[object],
) -> go.Figure:
    """
    Add multiple threshold lines to a chart.

    The threshold objects are expected to expose `value`, `label`,
    and optionally `color`, `dash`, and `annotation_position`.
    """

    for threshold in thresholds:
        fig.add_hline(
            y=threshold.value,
            line_dash=getattr(threshold, "dash", "dash"),
            line_color=getattr(threshold, "color", CHART_THRESHOLD_COLOR) or CHART_THRESHOLD_COLOR,
            annotation_text=threshold.label,
            annotation_position=getattr(threshold, "annotation_position", "top right"),
        )
    return fig


def create_multi_metric_line_chart(
    df,
    x: str,
    metrics: Sequence[tuple[str, str]],
    title: str,
    y_label: str = "",
    height: int = CHART_HEIGHT,
    color_map: dict[str, str] | None = None,
) -> go.Figure:
    """
    Create a comparison line chart for multiple metric columns in one dataframe.
    """

    rename_map = {value_col: label for label, value_col in metrics}
    long_df = (
        pd.DataFrame(df[[x] + [value_col for _, value_col in metrics]])
        .rename(columns=rename_map)
        .melt(
            id_vars=x,
            value_vars=[label for label, _ in metrics],
            var_name="metric",
            value_name="value",
        )
    )

    fig = px.line(
        long_df,
        x=x,
        y="value",
        color="metric",
        markers=True,
        title=title,
        labels={x: x, "value": y_label or "value", "metric": "Metric"},
        template=CHART_TEMPLATE,
        color_discrete_map=color_map,
    )
    fig.update_layout(
        hovermode="x unified",
        title_font=dict(size=24, color="#F8FBFF"),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.18,
            xanchor="left",
            x=0,
            bgcolor="rgba(15, 23, 42, 0.72)",
            bordercolor="rgba(148, 163, 184, 0.16)",
            borderwidth=1,
            font=dict(size=11, color="#E7EEF8"),
            title_font=dict(size=12, color="#F6C453"),
        ),
        height=height,
        paper_bgcolor="rgba(15, 23, 42, 0.0)",
        plot_bgcolor="rgba(15, 23, 42, 0.82)",
        font=dict(color="#E5EDF7"),
        margin=dict(l=40, r=40, t=56, b=132),
    )
    fig.update_xaxes(
        title_font=dict(size=15, color="#F8FBFF"),
        tickfont=dict(size=12, color="#DDE6F3"),
        showgrid=True,
        gridcolor="rgba(148, 163, 184, 0.10)",
        zeroline=False,
        linecolor="rgba(148, 163, 184, 0.18)",
    )
    fig.update_yaxes(
        title_font=dict(size=15, color="#F8FBFF"),
        tickfont=dict(size=12, color="#DDE6F3"),
        showgrid=True,
        gridcolor="rgba(148, 163, 184, 0.10)",
        zeroline=False,
        linecolor="rgba(148, 163, 184, 0.18)",
    )
    return fig


def style_traces_by_name_contains(
    fig: go.Figure,
    text: str,
    *,
    dash: str = "dash",
    width: int = 4,
) -> go.Figure:
    """Apply a shared style to traces whose label contains the given text."""

    for trace in fig.data:
        trace_name = getattr(trace, "name", "") or ""
        if text in trace_name:
            trace.update(line={"dash": dash, "width": width})
    return fig
