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
    title: str = "연도별 통계",
) -> None:
    if title:
        st.subheader(title)
    st.dataframe(df, width="stretch")


def render_pivot_table(
    df: pd.DataFrame,
    *,
    label: str = "연도별 학교 비교",
    expanded: bool = False,
) -> None:
    with st.expander(label, expanded=expanded):
        st.dataframe(df, width="stretch")


def render_definition_table(rows: Mapping[str, str], *, label: str = "용어 설명") -> None:
    if not rows:
        return

    markdown = ["| 항목 | 설명 |", "|------|------|"]
    for key, value in rows.items():
        markdown.append(f"| **{key}** | {value} |")

    with st.expander(label):
        st.markdown("\n".join(markdown))
