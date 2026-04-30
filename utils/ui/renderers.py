"""Top-level reusable page renderers for Streamlit metric pages."""

from __future__ import annotations

from typing import Any, Callable, Mapping, Sequence

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.chart_utils import (
    add_threshold_hline,
    add_threshold_hlines,
    create_multi_metric_line_chart,
    create_trend_line_chart,
    emphasize_selected_traces,
    style_traces_by_name_contains,
)
from utils.theme import is_mobile_compact_mode

from .kpi import build_dual_metric_kpis, build_single_metric_kpis, render_kpis
from .models import MetricSpec, OptionSection
from .tables import (
    build_pivot_table,
    build_yearly_stats,
    render_definition_table,
    render_pivot_table,
    render_stats_table,
)


def _plotly_config() -> dict[str, bool]:
    config = {"responsive": True}
    if is_mobile_compact_mode():
        config["displayModeBar"] = False
    return config


def _apply_mobile_chart_layout(fig: go.Figure) -> None:
    if not is_mobile_compact_mode():
        return

    fig.update_layout(
        height=360,
        margin=dict(l=8, r=8, t=52, b=32),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.36,
            xanchor="left",
            x=0,
            font=dict(size=10),
        ),
        font=dict(size=11),
    )


def _select_metric_for_mobile(metrics: Sequence[MetricSpec], *, key_prefix: str) -> MetricSpec:
    metric_options = {metric.label: metric for metric in metrics}
    metric_labels = list(metric_options.keys())
    selected_label = st.selectbox(
        "표시할 지표",
        metric_labels,
        key=f"{key_prefix}_{'_'.join(metric.value_col for metric in metrics)}",
    )
    return metric_options[selected_label]


def _apply_selected_school_styling(
    fig: go.Figure,
    *,
    selected_schools: Sequence[str] | None = None,
) -> None:
    """Apply shared selected-school emphasis when a page uses the standard renderer path."""

    if not selected_schools:
        return

    emphasize_selected_traces(fig, list(selected_schools))


def _render_single_chart(
    df: pd.DataFrame,
    *,
    year_col: str,
    school_col: str,
    metric: MetricSpec,
    title: str,
    selected_schools: Sequence[str] | None = None,
    chart_styler: Callable[[go.Figure], None] | None = None,
) -> None:
    fig = create_trend_line_chart(
        df,
        x=year_col,
        y=metric.value_col,
        color=school_col,
        title=title,
        x_label=year_col,
        y_label=metric.y_axis_label,
    )
    if metric.threshold is not None:
        add_threshold_hline(
            fig,
            threshold=metric.threshold.value,
            label=metric.threshold.label,
            color=metric.threshold.color or "red",
            dash=metric.threshold.dash,
        )
    style_traces_by_name_contains(fig, "평균")
    if chart_styler is not None:
        chart_styler(fig)
    else:
        _apply_selected_school_styling(fig, selected_schools=selected_schools)
    _apply_mobile_chart_layout(fig)
    st.plotly_chart(fig, use_container_width=True, config=_plotly_config())


def render_single_metric_page(
    *,
    df: pd.DataFrame,
    chart_df: pd.DataFrame | None = None,
    metric: MetricSpec,
    year_col: str,
    school_col: str,
    latest_year: int | str,
    chart_title: str,
    selected_schools: Sequence[str] | None = None,
    stats_title: str = "연도별 통계",
    pivot_label: str = "연도별 학교 비교",
    definition_rows: Mapping[str, str] | None = None,
    kpi_threshold_suffix: str = "",
    chart_styler: Callable[[go.Figure], None] | None = None,
) -> None:
    """Render the standard single-metric layout."""

    if df.empty:
        st.info("No data is available for the current selection.")
        return

    render_kpis(
        build_single_metric_kpis(
            df,
            metric=metric,
            latest_year=latest_year,
            year_col=year_col,
            school_col=school_col,
            threshold_suffix=kpi_threshold_suffix,
        ),
        columns=4,
    )
    st.divider()

    st.subheader(metric.chart_title or metric.label)
    _render_single_chart(
        chart_df if chart_df is not None else df,
        year_col=year_col,
        school_col=school_col,
        metric=metric,
        title=chart_title,
        selected_schools=selected_schools,
        chart_styler=chart_styler,
    )

    with st.expander(stats_title, expanded=False):
        render_stats_table(
            build_yearly_stats(df, year_col=year_col, metric=metric),
            title="",
        )

    render_pivot_table(
        build_pivot_table(
            df,
            year_col=year_col,
            school_col=school_col,
            value_col=metric.value_col,
            precision=metric.precision,
        ),
        label=pivot_label,
    )
    render_definition_table(definition_rows or {})


def render_dual_metric_page(
    *,
    df: pd.DataFrame,
    metrics: Sequence[MetricSpec],
    year_col: str,
    school_col: str,
    latest_year: int | str,
    selected_schools: Sequence[str] | None = None,
    pivot_label: str = "연도별 학교 비교",
    definition_rows: Mapping[str, str] | None = None,
) -> None:
    """Render a two-metric page as tabs with shared KPI logic."""

    if df.empty:
        st.info("No data is available for the current selection.")
        return

    render_kpis(
        build_dual_metric_kpis(
            df,
            metrics=metrics,
            latest_year=latest_year,
            school_col=school_col,
            year_col=year_col,
        ),
        columns=min(6, max(1, len(metrics) * 3)),
    )
    st.divider()

    def render_metric_section(metric: MetricSpec) -> None:
        st.subheader(metric.chart_title or metric.label)
        _render_single_chart(
            df,
            year_col=year_col,
            school_col=school_col,
            metric=metric,
            title=metric.chart_title or metric.label,
            selected_schools=selected_schools,
        )

        with st.expander("연도별 통계", expanded=False):
            render_stats_table(
                build_yearly_stats(df, year_col=year_col, metric=metric),
                title="",
            )

        render_pivot_table(
            build_pivot_table(
                df,
                year_col=year_col,
                school_col=school_col,
                value_col=metric.value_col,
                precision=metric.precision,
            ),
            label=f"{pivot_label}: {metric.label}",
        )

    if is_mobile_compact_mode():
        render_metric_section(_select_metric_for_mobile(metrics, key_prefix="dual_metric_page_mobile_metric"))
    else:
        tabs = st.tabs([metric.label for metric in metrics])
        for tab, metric in zip(tabs, metrics):
            with tab:
                render_metric_section(metric)

    render_definition_table(definition_rows or {})


def render_optional_page(
    *,
    df: pd.DataFrame,
    base_metric: MetricSpec,
    comparison_metrics: Sequence[MetricSpec] | None = None,
    year_col: str,
    school_col: str,
    latest_year: int | str,
    chart_title: str,
    selected_schools: Sequence[str] | None = None,
    definition_rows: Mapping[str, str] | None = None,
    sections: Sequence[OptionSection] = (),
    context: Mapping[str, Any] | None = None,
) -> None:
    """Render a single-metric page with optional comparison and extra sections."""

    if df.empty:
        st.info("No data is available for the current selection.")
        return

    merged_context = {"df": df, "latest_year": latest_year}
    if context:
        merged_context.update(context)

    render_single_metric_page(
        df=df,
        metric=base_metric,
        year_col=year_col,
        school_col=school_col,
        latest_year=latest_year,
        chart_title=chart_title,
        selected_schools=selected_schools,
        definition_rows=definition_rows,
    )

    if comparison_metrics:
        comparison_title = "Metric comparison"
        if len(df[school_col].unique()) == 1:
            st.subheader(comparison_title)
            fig = create_multi_metric_line_chart(
                df,
                x=year_col,
                metrics=[(metric.label, metric.value_col) for metric in comparison_metrics],
                title=comparison_title,
                y_label=comparison_metrics[0].y_axis_label,
            )
            thresholds = [metric.threshold for metric in comparison_metrics if metric.threshold is not None]
            if thresholds:
                add_threshold_hlines(fig, thresholds)
            _apply_mobile_chart_layout(fig)
            st.plotly_chart(fig, use_container_width=True, config=_plotly_config())

    for section in sections:
        if section.when is not None and not section.when(merged_context):
            continue

        if section.mode == "plain":
            section.renderer(merged_context)
            continue

        with st.expander(section.label, expanded=section.expanded):
            section.renderer(merged_context)
