from __future__ import annotations

import pandas as pd

from utils.ui.kpi import build_dual_metric_kpis, build_single_metric_kpis
from utils.ui.models import MetricSpec, ThresholdSpec


def _metric(value_col: str = "값") -> MetricSpec:
    return MetricSpec(
        key=value_col,
        label=value_col,
        value_col=value_col,
        y_axis_label=value_col,
        threshold=ThresholdSpec(value=10.0, label="기준값"),
    )


def test_build_single_metric_kpis_returns_empty_when_metric_values_are_missing() -> None:
    frame = pd.DataFrame(
        {
            "기준년도": [2024, 2024],
            "학교명": ["A대", "B대"],
            "값": [None, None],
        }
    )

    assert build_single_metric_kpis(
        frame,
        metric=_metric(),
        latest_year=2024,
        year_col="기준년도",
        school_col="학교명",
    ) == []


def test_build_single_metric_kpis_falls_back_to_available_year_when_latest_is_empty() -> None:
    frame = pd.DataFrame(
        {
            "기준년도": [2023, 2024],
            "학교명": ["A대", "A대"],
            "값": [12.5, None],
        }
    )

    items = build_single_metric_kpis(
        frame,
        metric=_metric(),
        latest_year=2024,
        year_col="기준년도",
        school_col="학교명",
    )

    assert items[0].label == "2023 평균"
    assert items[0].value == "12.5"


def test_build_dual_metric_kpis_skips_metrics_without_latest_values() -> None:
    frame = pd.DataFrame(
        {
            "기준년도": [2024, 2024],
            "학교명": ["A대", "B대"],
            "첫번째": [11.0, 13.0],
            "두번째": [None, None],
        }
    )

    items = build_dual_metric_kpis(
        frame,
        metrics=[_metric("첫번째"), _metric("두번째")],
        latest_year=2024,
        year_col="기준년도",
        school_col="학교명",
    )

    assert [item.label for item in items] == ["첫번째 평균", "첫번째 최고", "첫번째 기준 충족"]
