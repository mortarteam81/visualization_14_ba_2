from __future__ import annotations

import pandas as pd

from ui import MetricSpec, ThresholdSpec
from utils.comparison_charts import (
    build_mobile_latest_comparison_frame,
    finite_metric_values,
    resolve_distribution_focus_range,
    resolve_threshold_focus_range,
)
from utils.grouping import AVERAGE_LINE_SUFFIX


def test_finite_metric_values_drops_nan_and_infinity() -> None:
    values = finite_metric_values(pd.Series([1.0, None, float("inf"), -float("inf"), "2.5"]))

    assert values.tolist() == [1.0, 2.5]


def test_threshold_focus_range_uses_threshold_window_not_outlier_max() -> None:
    metric = MetricSpec(
        key="sample",
        label="Sample",
        value_col="value",
        y_axis_label="Sample (%)",
        threshold=ThresholdSpec(value=0.4, label="기준값"),
    )

    resolved = resolve_threshold_focus_range(
        pd.Series([0.0, 0.5, 3.0, 26.9]),
        metric,
        lower_offset=0.4,
        upper_offset=5.0,
    )

    assert resolved == (0.0, 5.4)


def test_distribution_focus_range_includes_required_boundary_value() -> None:
    resolved = resolve_distribution_focus_range(
        pd.Series([25.0, 35.0, 45.0, 90.0]),
        lower_quantile=0.10,
        upper_quantile=0.75,
        padding_ratio=0.0,
        include_values=(70.0,),
    )

    assert resolved == (28.0, 70.0)


def test_mobile_latest_comparison_frame_uses_latest_year_and_group_averages() -> None:
    metric = MetricSpec(
        key="sample",
        label="Sample",
        value_col="value",
        y_axis_label="Sample (%)",
        precision=1,
    )
    group_average = f"Group {AVERAGE_LINE_SUFFIX}"
    frame = pd.DataFrame(
        {
            "year": [2023, 2024, 2023, 2024, 2023, 2024, 2024],
            "school": ["Alpha", "Alpha", "Beta", "Beta", group_average, group_average, "Hidden"],
            "value": [60.0, 70.0, 77.0, 80.0, 62.0, 65.0, 99.0],
        }
    )

    result = build_mobile_latest_comparison_frame(
        frame,
        metric=metric,
        year_col="year",
        school_col="school",
        selected_schools=["Alpha", "Beta"],
        group_definitions={"Group": ["Hidden"]},
    )

    assert result["school"].tolist() == ["Beta", "Alpha", group_average]
    assert result["순위"].tolist() == [1, 2, 3]
    assert result["최신연도"].tolist() == [2024, 2024, 2024]
    assert result["전년 대비"].tolist() == [3.0, 10.0, 3.0]
    assert result["구분"].tolist() == ["선택 학교", "선택 학교", "비교그룹 평균"]


def test_mobile_latest_comparison_frame_respects_lower_is_better() -> None:
    metric = MetricSpec(
        key="sample",
        label="Sample",
        value_col="value",
        y_axis_label="Sample",
        higher_is_better=False,
    )
    frame = pd.DataFrame(
        {
            "year": [2024, 2024],
            "school": ["Alpha", "Beta"],
            "value": [10.0, 5.0],
        }
    )

    result = build_mobile_latest_comparison_frame(
        frame,
        metric=metric,
        year_col="year",
        school_col="school",
        selected_schools=["Alpha", "Beta"],
        group_definitions={},
    )

    assert result["school"].tolist() == ["Beta", "Alpha"]
    assert result["순위"].tolist() == [1, 2]
