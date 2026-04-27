from __future__ import annotations

import pandas as pd

from ui import MetricSpec, ThresholdSpec
from utils.comparison_charts import (
    finite_metric_values,
    resolve_distribution_focus_range,
    resolve_threshold_focus_range,
)


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
