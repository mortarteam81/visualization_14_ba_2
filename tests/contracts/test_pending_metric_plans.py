from __future__ import annotations

import sqlite3
from pathlib import Path

from registry import METRIC_REGISTRY
from registry.pending_metrics import (
    CLASSROOM_AREA_STANDARD_SQM,
    LAB_AREA_FIELDS,
    LAB_AREA_STANDARD_SQM,
    LAB_AREA_STUDENT_WEIGHTS,
    LAB_EQUIPMENT_DEFINITION_YEARS,
    LAB_EQUIPMENT_FIELDS,
    PENDING_METRIC_PLANS,
)
from scripts.build_pending_metric_db import bootstrap_database, load_csv_as_raw_records


EXPECTED_PENDING_METRICS = {
    "corp_finance_ratio",
    "student_recruitment",
    "classroom_area",
    "lab_area",
    "lab_equipment",
}


def test_pending_metric_plan_covers_all_unimplemented_registry_metrics() -> None:
    unimplemented_ids = {
        metric.id for metric in METRIC_REGISTRY.values() if not metric.implemented
    }

    assert unimplemented_ids == EXPECTED_PENDING_METRICS
    assert set(PENDING_METRIC_PLANS) == EXPECTED_PENDING_METRICS


def test_pending_metric_plans_have_registry_compatible_series_proposals() -> None:
    for metric_id, plan in PENDING_METRIC_PLANS.items():
        registry_metric = METRIC_REGISTRY[metric_id]

        assert plan.metric_id == registry_metric.id
        assert plan.dataset_key == registry_metric.dataset_key
        assert plan.title == registry_metric.title
        assert plan.source_priority
        assert plan.raw_source_urls
        assert plan.numerator
        assert plan.denominator
        assert plan.formula
        assert plan.unit
        assert plan.proposed_series

        for series in plan.proposed_series:
            assert series.id
            assert series.label
            assert series.column
            assert series.unit == plan.unit
            assert series.decimals >= 0


def test_pending_metric_plan_priorities_are_explicit() -> None:
    priorities = {plan.implementation_priority for plan in PENDING_METRIC_PLANS.values()}

    assert priorities == {1, 2}
    assert {
        metric_id
        for metric_id, plan in PENDING_METRIC_PLANS.items()
        if plan.implementation_priority == 1
    } == {
        "student_recruitment",
    }


def test_kuee_4th_cycle_facility_definitions_are_captured() -> None:
    classroom_plan = PENDING_METRIC_PLANS["classroom_area"]
    lab_area_plan = PENDING_METRIC_PLANS["lab_area"]
    lab_equipment_plan = PENDING_METRIC_PLANS["lab_equipment"]

    assert CLASSROOM_AREA_STANDARD_SQM == 1.2
    assert "계열별 산출 지표가 아니라" in classroom_plan.notes
    assert "전체 강의실 면적 / 재학생 수" in classroom_plan.formula

    assert LAB_AREA_STANDARD_SQM == 2.5
    assert LAB_AREA_FIELDS == (
        "인문사회계열",
        "자연과학계열",
        "공학계열",
        "의학계열",
        "예체능계열",
    )
    assert abs(LAB_AREA_STUDENT_WEIGHTS["인문사회계열"] - (1 / 3)) < 0.000001
    assert "인문사회계열 재학생 수를 1/3로 가중" in lab_area_plan.formula

    assert LAB_EQUIPMENT_FIELDS == (
        "자연과학계열",
        "공학계열",
        "의학계열",
        "예체능계열",
    )
    assert "인문사회계열" not in LAB_EQUIPMENT_FIELDS
    assert LAB_EQUIPMENT_DEFINITION_YEARS == (2024, 2025)
    assert lab_equipment_plan.unit == "천원"
    assert "시약·샘플 구입비는 제외" in lab_equipment_plan.notes


def test_bootstrap_pending_metric_database(tmp_path: Path) -> None:
    db_path = tmp_path / "pending_metrics.sqlite"

    bootstrap_database(db_path, PENDING_METRIC_PLANS.values())

    with sqlite3.connect(db_path) as connection:
        plan_count = connection.execute("SELECT COUNT(*) FROM pending_metric_plans").fetchone()[0]
        source_count = connection.execute("SELECT COUNT(*) FROM raw_sources").fetchone()[0]
        review_count = connection.execute(
            "SELECT COUNT(*) FROM pending_metric_plans WHERE needs_definition_review = 1"
        ).fetchone()[0]

    assert plan_count == 5
    assert source_count >= 5
    assert review_count >= 4


def test_load_csv_as_raw_records(tmp_path: Path) -> None:
    db_path = tmp_path / "pending_metrics.sqlite"
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("학교명,기준년도,값\n성신여자대학교,2025,12.3\n", encoding="utf-8-sig")

    bootstrap_database(db_path, PENDING_METRIC_PLANS.values())
    inserted = load_csv_as_raw_records(
        db_path,
        source_id="pending:student_recruitment:raw:1",
        table_name="student_recruitment_sample",
        csv_path=csv_path,
    )

    with sqlite3.connect(db_path) as connection:
        payload = connection.execute(
            "SELECT payload_json FROM raw_records WHERE source_id = ? AND row_number = 1",
            ("pending:student_recruitment:raw:1",),
        ).fetchone()[0]

    assert inserted == 1
    assert "성신여자대학교" in payload
    assert "2025" in payload
