"""KPI builders and render helpers."""

from __future__ import annotations

from typing import Iterable, Sequence

import pandas as pd
import streamlit as st

from utils.theme import is_mobile_compact_mode

from .models import KPIItem, MetricSpec


def _default_formatter(value: float, precision: int) -> str:
    return f"{value:.{precision}f}"


def format_metric_value(value: float, metric: MetricSpec) -> str:
    if metric.formatter is not None:
        return metric.formatter(value)
    return _default_formatter(value, metric.precision)


def _valid_metric_slice(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    if value_col not in df.columns:
        return pd.DataFrame()
    return df[df[value_col].notna()]


def build_single_metric_kpis(
    df: pd.DataFrame,
    *,
    metric: MetricSpec,
    latest_year: int | str,
    year_col: str,
    school_col: str,
    threshold_suffix: str = "",
) -> list[KPIItem]:
    """Build the four KPI cards used by most single-metric pages."""

    latest_df = df[df[year_col] == latest_year]
    value_col = metric.value_col
    latest_slice = _valid_metric_slice(latest_df, value_col)
    display_year = latest_year
    if latest_slice.empty:
        latest_slice = _valid_metric_slice(df, value_col)
        if not latest_slice.empty and year_col in latest_slice.columns:
            display_year = latest_slice[year_col].max()
    if latest_slice.empty:
        return []

    idx_max = latest_slice[value_col].idxmax()
    idx_min = latest_slice[value_col].idxmin()

    items = [
        KPIItem(
            label=f"{display_year} 평균",
            value=format_metric_value(latest_slice[value_col].mean(), metric),
        ),
        KPIItem(
            label=f"{metric.label} 최고",
            value=format_metric_value(latest_slice[value_col].max(), metric),
            delta=str(latest_slice.loc[idx_max, school_col]),
            delta_color="off",
        ),
        KPIItem(
            label=f"{metric.label} 최저",
            value=format_metric_value(latest_slice[value_col].min(), metric),
            delta=str(latest_slice.loc[idx_min, school_col]),
            delta_color="off",
        ),
    ]

    if metric.threshold is not None:
        comparator = (
            latest_slice[value_col] >= metric.threshold.value
            if metric.higher_is_better
            else latest_slice[value_col] <= metric.threshold.value
        )
        items.append(
            KPIItem(
                label=threshold_suffix or "기준 충족",
                value=f"{int(comparator.sum())} / {len(latest_slice)}",
                help=metric.threshold.label,
            )
        )
    return items


def build_dual_metric_kpis(
    df: pd.DataFrame,
    *,
    metrics: Sequence[MetricSpec],
    latest_year: int | str,
    school_col: str,
    year_col: str,
) -> list[KPIItem]:
    """Build three KPI cards per metric for dual-metric layouts."""

    latest_df = df[df[year_col] == latest_year]
    items: list[KPIItem] = []

    for metric in metrics:
        latest_slice = _valid_metric_slice(latest_df, metric.value_col)
        if latest_slice.empty:
            continue

        idx_max = latest_slice[metric.value_col].idxmax()
        items.append(
            KPIItem(
                label=f"{metric.label} 평균",
                value=format_metric_value(latest_slice[metric.value_col].mean(), metric),
            )
        )
        items.append(
            KPIItem(
                label=f"{metric.label} 최고",
                value=format_metric_value(latest_slice[metric.value_col].max(), metric),
                delta=str(latest_slice.loc[idx_max, school_col]),
                delta_color="off",
            )
        )

        if metric.threshold is not None:
            comparator = (
                latest_slice[metric.value_col] >= metric.threshold.value
                if metric.higher_is_better
                else latest_slice[metric.value_col] <= metric.threshold.value
            )
            items.append(
                KPIItem(
                    label=f"{metric.label} 기준 충족",
                    value=f"{int(comparator.sum())} / {len(latest_slice)}",
                    help=metric.threshold.label,
                )
            )
    return items


def render_kpis(items: Iterable[KPIItem], columns: int | None = None) -> None:
    """Render KPI cards across Streamlit columns."""

    item_list = list(items)
    if not item_list:
        return

    column_count = 1 if is_mobile_compact_mode() else columns or len(item_list)
    containers = st.columns(column_count)

    for index, item in enumerate(item_list):
        container = containers[index % column_count]
        with container:
            st.metric(
                item.label,
                item.value,
                delta=item.delta,
                help=item.help,
                delta_color=item.delta_color,
            )
