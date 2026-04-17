from __future__ import annotations

import pandas as pd

from utils.grouping import AVERAGE_LINE_SUFFIX, build_group_average_frame


def test_build_group_average_frame_returns_group_lines() -> None:
    frame = pd.DataFrame(
        {
            "기준년도": [2023, 2023, 2024, 2024],
            "학교명": ["A", "B", "A", "B"],
            "부담율": [10.0, 20.0, 30.0, 40.0],
        }
    )

    result = build_group_average_frame(
        frame,
        year_col="기준년도",
        school_col="학교명",
        value_col="부담율",
        groups={"그룹1": ["A", "B"]},
    )

    assert list(result["학교명"].unique()) == [f"그룹1 {AVERAGE_LINE_SUFFIX}"]
    assert result["부담율"].tolist() == [15.0, 35.0]


def test_build_group_average_frame_skips_empty_groups() -> None:
    frame = pd.DataFrame(
        {
            "기준년도": [2024],
            "학교명": ["A"],
            "부담율": [10.0],
        }
    )

    result = build_group_average_frame(
        frame,
        year_col="기준년도",
        school_col="학교명",
        value_col="부담율",
        groups={"그룹1": [], "그룹2": ["Z"]},
    )

    assert result.empty
