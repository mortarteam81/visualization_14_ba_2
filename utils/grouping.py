from __future__ import annotations

from collections.abc import Mapping, Sequence

import pandas as pd


AVERAGE_LINE_SUFFIX = "평균"


def build_group_average_frame(
    df: pd.DataFrame,
    *,
    year_col: str,
    school_col: str,
    value_col: str,
    groups: Mapping[str, Sequence[str]],
) -> pd.DataFrame:
    """Build synthetic per-year average rows for configured school groups."""

    frames: list[pd.DataFrame] = []

    for group_name, schools in groups.items():
        normalized_schools = [school for school in schools if school]
        if not group_name or not normalized_schools:
            continue

        group_df = df[df[school_col].isin(normalized_schools)].copy()
        if group_df.empty:
            continue

        averaged = (
            group_df.groupby(year_col, as_index=False)[value_col]
            .mean()
            .assign(**{school_col: f"{group_name} {AVERAGE_LINE_SUFFIX}"})
        )
        frames.append(averaged[[year_col, school_col, value_col]])

    if not frames:
        return pd.DataFrame(columns=[year_col, school_col, value_col])

    return pd.concat(frames, ignore_index=True)
