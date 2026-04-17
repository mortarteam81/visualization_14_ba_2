"""Statistics and pivot helpers for shared metric pages."""

from __future__ import annotations

from typing import Mapping

import pandas as pd
import streamlit as st

from .models import MetricSpec


def build_yearly_stats(
    df: pd.DataFrame,
    *,
    year_col: str,
    metric: MetricSpec,
) -> pd.DataFrame:
    """Aggregate yearly statistics for a metric."""

    stats = (
        df.groupby(year_col)[metric.value_col]
        .agg(["mean", "max", "min", "count"])
        .rename(columns=dict(metric.stats_labels))
        .round(metric.precision)
    )
    return stats


def build_pivot_table(
    df: pd.DataFrame,
    *,
    year_col: str,
    school_col: str,
    value_col: str,
    precision: int = 1,
) -> pd.DataFrame:
    """Build a year-by-school pivot table."""

    return (
        df.pivot_table(
            index=year_col,
            columns=school_col,
            values=value_col,
            aggfunc="mean",
        ).round(precision)
    )


def render_stats_table(
    df: pd.DataFrame,
    *,
    title: str = "Yearly stats",
) -> None:
    st.subheader(title)
    st.dataframe(df, use_container_width=True)


def render_pivot_table(
    df: pd.DataFrame,
    *,
    label: str = "Year by school",
    expanded: bool = False,
) -> None:
    with st.expander(label, expanded=expanded):
        st.dataframe(df, use_container_width=True)


def render_definition_table(rows: Mapping[str, str], *, label: str = "Definitions") -> None:
    if not rows:
        return

    markdown = ["| Item | Description |", "|------|-------------|"]
    for key, value in rows.items():
        markdown.append(f"| **{key}** | {value} |")

    with st.expander(label):
        st.markdown("\n".join(markdown))
