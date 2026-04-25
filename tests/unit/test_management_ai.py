from __future__ import annotations

import json

import pandas as pd

from utils.management_ai import (
    MANAGEMENT_QUESTIONS,
    filter_payload_for_question,
    normalize_management_analysis_result,
    questions_for_mode,
)
from utils.management_insights import (
    InsightDataset,
    InsightMetricSpec,
    PENDING_METRIC_IDS,
    build_range_management_ai_payload,
    build_single_year_management_ai_payload,
    summarize_rank_correlation_pairs,
)


def _synthetic_dataset() -> InsightDataset:
    metrics = (
        InsightMetricSpec(
            key="tuition_ratio",
            label="등록금 비율",
            source_metric_id="tuition",
            source_column="등록금비율",
            unit="%",
            group="재정",
            higher_is_better=False,
        ),
        InsightMetricSpec(
            key="external_research_fund",
            label="교외 연구비",
            source_metric_id="research",
            source_column="교외연구비",
            unit="천원",
            group="연구성과",
            decimals=0,
        ),
        InsightMetricSpec(
            key="career_outcome_rate",
            label="졸업생 진로 성과",
            source_metric_id="jirosung",
            source_column="졸업생_진로_성과",
            unit="%",
            group="학생성과",
        ),
    )
    rows = []
    values = {
        2023: {
            "A대": {"tuition_ratio": 60.0, "external_research_fund": 100.0, "career_outcome_rate": 80.0},
            "B대": {"tuition_ratio": 50.0, "external_research_fund": 150.0, "career_outcome_rate": 70.0},
            "C대": {"tuition_ratio": 40.0, "external_research_fund": 80.0, "career_outcome_rate": 85.0},
        },
        2024: {
            "A대": {"tuition_ratio": 30.0, "external_research_fund": 200.0, "career_outcome_rate": 75.0},
            "B대": {"tuition_ratio": 50.0, "external_research_fund": 220.0, "career_outcome_rate": 72.0},
            "C대": {"tuition_ratio": 70.0, "external_research_fund": 90.0, "career_outcome_rate": 86.0},
        },
    }
    metrics_by_key = {metric.key: metric for metric in metrics}
    for year, school_values in values.items():
        for school, metric_values in school_values.items():
            for metric_key, value in metric_values.items():
                metric = metrics_by_key[metric_key]
                rows.append(
                    {
                        "year": year,
                        "school_name": school,
                        "value": value,
                        "metric_key": metric.key,
                        "metric_label": metric.label,
                        "source_metric_id": metric.source_metric_id,
                        "unit": metric.unit,
                        "group": metric.group,
                        "higher_is_better": metric.higher_is_better,
                        "decimals": metric.decimals,
                    }
                )
    long = pd.DataFrame(rows)
    wide = (
        long.pivot_table(
            index=["year", "school_name"],
            columns="metric_key",
            values="value",
            aggfunc="mean",
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )
    return InsightDataset(long=long, wide=wide, metrics=metrics, skipped_sources=())


def test_question_pool_has_unique_ids_and_supported_modes() -> None:
    question_ids = [question.question_id for question in MANAGEMENT_QUESTIONS]

    assert len(question_ids) == len(set(question_ids))
    assert all(question.label for question in MANAGEMENT_QUESTIONS)
    assert all(question.payload_sections for question in MANAGEMENT_QUESTIONS)
    assert all(question in questions_for_mode("year_range") for question in questions_for_mode("year_range"))


def test_filter_payload_for_question_keeps_only_required_sections() -> None:
    question = next(question for question in MANAGEMENT_QUESTIONS if question.question_id == "policy_priorities")
    payload = {
        "analysis_mode": "year_range",
        "focus_school": "A대",
        "coverage": {"years": []},
        "comparison_gap_changes": {"improved_vs_comparison": []},
        "quadrant": {"should": "not be included"},
        "raw_logs": "never include",
    }

    filtered = filter_payload_for_question(payload, question)

    assert "comparison_gap_changes" in filtered
    assert "quadrant" not in filtered
    assert "raw_logs" not in filtered


def test_single_year_payload_uses_implemented_metrics_and_pending_roadmap_only() -> None:
    dataset = _synthetic_dataset()

    payload = build_single_year_management_ai_payload(
        dataset,
        year=2024,
        focus_school="A대",
        comparison_schools=["B대", "C대"],
        groups=["재정", "연구성과", "학생성과"],
        min_pair_count=3,
    )

    assert payload["included_series_count"] == 3
    assert payload["excluded_pending_metric_count"] == len(PENDING_METRIC_IDS)
    assert {item["calculation_included"] for item in payload["pending_metrics"]} == {False}
    assert {item["metric_id"] for item in payload["pending_metrics"]} == set(PENDING_METRIC_IDS)


def test_range_payload_calculates_direction_for_lower_is_better_metric() -> None:
    dataset = _synthetic_dataset()

    payload = build_range_management_ai_payload(
        dataset,
        start_year=2023,
        end_year=2024,
        focus_school="A대",
        comparison_schools=["B대", "C대"],
        groups=["재정", "연구성과", "학생성과"],
    )

    improved = {
        item["metric_key"]: item
        for item in payload["trend_changes"]["improved"]
    }
    tuition_change = improved["tuition_ratio"]

    assert tuition_change["raw_delta"] == -30.0
    assert tuition_change["adjusted_delta"] == 30.0
    assert tuition_change["trend_interpretation"] == "개선"


def test_correlation_summary_limits_pairs_without_full_matrix() -> None:
    metrics = (
        InsightMetricSpec("first", "첫 지표", "first", "first", "점", "테스트"),
        InsightMetricSpec("second", "둘째 지표", "second", "second", "점", "테스트"),
        InsightMetricSpec("third", "셋째 지표", "third", "third", "점", "테스트"),
    )
    wide = pd.DataFrame(
        {
            "year": [2024, 2024, 2024, 2024],
            "school_name": ["A대", "B대", "C대", "D대"],
            "first": [1.0, 2.0, 3.0, 4.0],
            "second": [10.0, 20.0, 30.0, 40.0],
            "third": [40.0, 30.0, 20.0, 10.0],
        }
    )

    summary = summarize_rank_correlation_pairs(
        wide,
        metrics,
        ["first", "second", "third"],
        year=2024,
        min_pair_count=3,
        top_n=1,
    )

    assert len(summary["positive"]) == 1
    assert len(summary["negative"]) == 1
    assert "matrix" not in summary


def test_normalize_management_analysis_result_handles_evidence_and_data_used() -> None:
    result = normalize_management_analysis_result(
        json.dumps(
            {
                "summary": "요약",
                "evidence": ["근거 1"],
                "management_implications": "시사점",
                "recommended_actions": ["액션"],
                "risks": ["위험"],
                "caveats": ["유의"],
                "data_used": {"period": "2020-2024", "included_series_count": 15},
            },
            ensure_ascii=False,
        )
    )

    assert result["summary"] == "요약"
    assert result["evidence"] == ["근거 1"]
    assert result["management_implications"] == ["시사점"]
    assert result["data_used"]["period"] == "2020-2024"
