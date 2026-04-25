from __future__ import annotations

import pandas as pd

from utils.management_insights import (
    InsightMetricSpec,
    PENDING_METRIC_IDS,
    build_management_insight_dataset,
    build_percentile_profile,
    build_rank_correlation,
    pending_metric_roadmap_frame,
)


def test_management_dataset_uses_implemented_metrics_only() -> None:
    dataset = build_management_insight_dataset()
    calculated_source_ids = {metric.source_metric_id for metric in dataset.metrics}

    assert calculated_source_ids
    assert calculated_source_ids.isdisjoint(PENDING_METRIC_IDS)
    assert set(dataset.long["source_metric_id"]).isdisjoint(PENDING_METRIC_IDS)


def test_percentile_profile_reverses_lower_is_better_metric() -> None:
    metric = InsightMetricSpec(
        key="tuition_ratio",
        label="등록금 비율",
        source_metric_id="tuition",
        source_column="등록금비율",
        unit="%",
        group="재정",
        higher_is_better=False,
    )
    frame = pd.DataFrame(
        {
            "year": [2024, 2024, 2024],
            "school_name": ["A대", "B대", "C대"],
            "metric_key": ["tuition_ratio"] * 3,
            "metric_label": ["등록금 비율"] * 3,
            "source_metric_id": ["tuition"] * 3,
            "unit": ["%"] * 3,
            "group": ["재정"] * 3,
            "higher_is_better": [False] * 3,
            "decimals": [1] * 3,
            "value": [30.0, 50.0, 70.0],
        }
    )

    profile = build_percentile_profile(
        frame,
        (metric,),
        year=2024,
        school_name="A대",
        groups=["재정"],
    )

    assert profile.loc[0, "percentile"] == 100.0


def test_rank_correlation_uses_pandas_rank_without_scipy() -> None:
    wide = pd.DataFrame(
        {
            "year": [2024, 2024, 2024, 2024],
            "school_name": ["A대", "B대", "C대", "D대"],
            "first": [1.0, 2.0, 3.0, 4.0],
            "second": [10.0, 20.0, 30.0, 40.0],
            "third": [40.0, 30.0, 20.0, 10.0],
        }
    )

    correlation = build_rank_correlation(
        wide,
        ["first", "second", "third"],
        year=2024,
        min_pair_count=3,
    )

    assert correlation.loc["first", "second"] == 1.0
    assert correlation.loc["first", "third"] == -1.0


def test_pending_metrics_are_shown_on_roadmap_not_calculation() -> None:
    dataset = build_management_insight_dataset()
    roadmap = pending_metric_roadmap_frame()

    assert set(roadmap["metric_id"]) == set(PENDING_METRIC_IDS)
    assert set(roadmap["계산 포함"]) == {"아니오"}
    assert set(roadmap["metric_id"]).isdisjoint(set(dataset.long["source_metric_id"]))
