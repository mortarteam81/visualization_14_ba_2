from __future__ import annotations

import pandas as pd

from utils.management_insights import (
    InsightMetricSpec,
    PENDING_METRIC_IDS,
    build_comparison_gap_trend_frame,
    build_management_insight_dataset,
    build_percentile_profile,
    build_quadrant_path_frame,
    build_rank_correlation,
    build_range_profile_classification,
    pending_metric_roadmap_frame,
)


def test_management_dataset_uses_implemented_metrics_only() -> None:
    dataset = build_management_insight_dataset()
    calculated_source_ids = {metric.source_metric_id for metric in dataset.metrics}

    assert calculated_source_ids
    assert "staff_per_student" in calculated_source_ids
    assert "scholarship_ratio" in calculated_source_ids
    assert "corp_transfer_ratio" in calculated_source_ids
    assert calculated_source_ids.isdisjoint(PENDING_METRIC_IDS)
    assert set(dataset.long["source_metric_id"]).isdisjoint(PENDING_METRIC_IDS)


def test_staff_per_student_is_lower_is_better_in_management_dataset() -> None:
    dataset = build_management_insight_dataset()

    metric = next(metric for metric in dataset.metrics if metric.source_metric_id == "staff_per_student")

    assert metric.higher_is_better is False


def test_scholarship_ratio_is_finance_metric_in_management_dataset() -> None:
    dataset = build_management_insight_dataset()

    metric = next(metric for metric in dataset.metrics if metric.source_metric_id == "scholarship_ratio")

    assert metric.group == "재정"
    assert metric.higher_is_better is True


def test_corp_transfer_ratio_is_finance_metric_in_management_dataset() -> None:
    dataset = build_management_insight_dataset()

    metric = next(metric for metric in dataset.metrics if metric.source_metric_id == "corp_transfer_ratio")

    assert metric.group == "재정"
    assert metric.higher_is_better is True


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


def test_range_profile_classifies_strength_and_weakness() -> None:
    metrics = (
        InsightMetricSpec("strong", "강점 지표", "strong", "강점", "%", "재정"),
        InsightMetricSpec("weak", "취약 지표", "weak", "취약", "%", "재정"),
        InsightMetricSpec("declining", "악화 지표", "declining", "악화", "%", "재정"),
    )
    rows = []
    values = {
        2023: {
            "A대": {"strong": 80.0, "weak": 20.0, "declining": 90.0},
            "B대": {"strong": 40.0, "weak": 70.0, "declining": 80.0},
            "C대": {"strong": 20.0, "weak": 90.0, "declining": 10.0},
        },
        2024: {
            "A대": {"strong": 90.0, "weak": 25.0, "declining": 30.0},
            "B대": {"strong": 50.0, "weak": 80.0, "declining": 90.0},
            "C대": {"strong": 10.0, "weak": 95.0, "declining": 10.0},
        },
    }
    metrics_by_key = {metric.key: metric for metric in metrics}
    for year, school_values in values.items():
        for school, metric_values in school_values.items():
            for key, value in metric_values.items():
                metric = metrics_by_key[key]
                rows.append(
                    {
                        "year": year,
                        "school_name": school,
                        "value": value,
                        "metric_key": key,
                        "metric_label": metric.label,
                        "source_metric_id": metric.source_metric_id,
                        "unit": metric.unit,
                        "group": metric.group,
                        "higher_is_better": metric.higher_is_better,
                        "decimals": metric.decimals,
                    }
                )
    long = pd.DataFrame(rows)

    classified = build_range_profile_classification(
        long,
        metrics,
        start_year=2023,
        end_year=2024,
        focus_school="A대",
        groups=["재정"],
    )

    classifications = dict(zip(classified["metric_key"], classified["classification"]))
    assert classifications["strong"] == "현재 강점"
    assert classifications["weak"] == "구조적 취약"
    assert classifications["declining"] == "악화 중"


def test_quadrant_path_frame_returns_start_and_end_rows() -> None:
    wide = pd.DataFrame(
        {
            "year": [2023, 2024, 2023, 2024],
            "school_name": ["A대", "A대", "B대", "B대"],
            "x": [1.0, 2.0, 5.0, 6.0],
            "y": [10.0, 20.0, 50.0, 60.0],
        }
    )

    path = build_quadrant_path_frame(
        wide,
        start_year=2023,
        end_year=2024,
        x_metric_key="x",
        y_metric_key="y",
        schools=["A대", "B대"],
    )

    assert set(path["phase"]) == {"시작", "종료"}
    assert path.groupby("school_name")["phase"].nunique().to_dict() == {"A대": 2, "B대": 2}


def test_comparison_gap_trend_reverses_lower_is_better_gap() -> None:
    metric = InsightMetricSpec(
        key="tuition_ratio",
        label="등록금 비율",
        source_metric_id="tuition",
        source_column="등록금비율",
        unit="%",
        group="재정",
        higher_is_better=False,
    )
    long = pd.DataFrame(
        {
            "year": [2023, 2023, 2024, 2024],
            "school_name": ["A대", "B대", "A대", "B대"],
            "metric_key": ["tuition_ratio"] * 4,
            "metric_label": ["등록금 비율"] * 4,
            "source_metric_id": ["tuition"] * 4,
            "unit": ["%"] * 4,
            "group": ["재정"] * 4,
            "higher_is_better": [False] * 4,
            "decimals": [1] * 4,
            "value": [70.0, 50.0, 30.0, 50.0],
        }
    )

    trend = build_comparison_gap_trend_frame(
        long,
        (metric,),
        start_year=2023,
        end_year=2024,
        focus_school="A대",
        comparison_schools=["B대"],
        groups=["재정"],
    )

    assert trend.loc[trend["year"] == 2023, "adjusted_gap"].iloc[0] == -20.0
    assert trend.loc[trend["year"] == 2024, "adjusted_gap"].iloc[0] == 20.0
