from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

import pandas as pd
import streamlit as st

from ui import MetricSpec, build_dual_metric_kpis, build_pivot_table, build_yearly_stats, render_kpis, render_pivot_table, render_stats_table
from utils.chart_utils import add_threshold_hlines, create_multi_metric_line_chart


MetricSectionRenderer = Callable[[MetricSpec], None]


def render_dual_metric_sections(
    *,
    filtered_df: pd.DataFrame,
    metrics: Sequence[MetricSpec],
    latest_year: int | str,
    school_col: str,
    year_col: str,
    render_metric_section: MetricSectionRenderer,
) -> None:
    render_kpis(
        build_dual_metric_kpis(
            filtered_df,
            metrics=metrics,
            latest_year=latest_year,
            school_col=school_col,
            year_col=year_col,
        ),
        columns=min(6, max(1, len(metrics) * 3)),
    )
    st.divider()

    tabs = st.tabs([metric.label for metric in metrics])
    for tab, metric in zip(tabs, metrics):
        with tab:
            render_metric_section(metric)


def render_single_school_metric_comparison(
    filtered_df: pd.DataFrame,
    *,
    metrics: Sequence[MetricSpec],
    year_col: str,
    school_col: str,
    section_title: str,
    chart_title: str,
    y_label: str,
    color_map: Mapping[str, str],
    stats_expander_title: str | None = None,
    pivot_label_prefix: str | None = None,
) -> None:
    if len(filtered_df[school_col].unique()) != 1:
        return

    st.subheader(section_title)
    comparison_fig = create_multi_metric_line_chart(
        filtered_df,
        x=year_col,
        metrics=[(metric.label, metric.value_col) for metric in metrics],
        title=chart_title,
        y_label=y_label,
        color_map=dict(color_map),
    )
    thresholds = [metric.threshold for metric in metrics if metric.threshold is not None]
    if thresholds:
        add_threshold_hlines(comparison_fig, thresholds)
    st.plotly_chart(comparison_fig, use_container_width=True)

    if stats_expander_title is not None:
        with st.expander(stats_expander_title, expanded=False):
            for metric in metrics:
                render_stats_table(
                    build_yearly_stats(filtered_df, year_col=year_col, metric=metric),
                    title=metric.label,
                )

    if pivot_label_prefix is not None:
        for metric in metrics:
            render_pivot_table(
                build_pivot_table(
                    filtered_df,
                    year_col=year_col,
                    school_col=school_col,
                    value_col=metric.value_col,
                    precision=metric.precision,
                ),
                label=f"{pivot_label_prefix}: {metric.label}",
            )
