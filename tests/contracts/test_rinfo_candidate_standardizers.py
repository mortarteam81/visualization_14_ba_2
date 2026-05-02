from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

STAFF_SCOPE_CANDIDATE = PROJECT_ROOT / "data" / "conversion_outputs" / "rinfo" / "library_staff" / "library_staff_per_1000_students_2008_2025_candidate_scope34_no_inf.csv"
MATERIAL_SCOPE_CANDIDATE = PROJECT_ROOT / "data" / "conversion_outputs" / "rinfo" / "material_purchase" / "library_material_purchase_per_student_2008_2025_candidate_scope34_no_inf.csv"
STAFF_REPORT = PROJECT_ROOT / "data" / "validation" / "processing_reports" / "rinfo_library_staff.processing_report.json"
MATERIAL_REPORT = PROJECT_ROOT / "data" / "validation" / "processing_reports" / "rinfo_material_purchase.processing_report.json"
STAFF_COVERAGE = PROJECT_ROOT / "data" / "validation" / "mismatch_reports" / "rinfo_library_staff_coverage.csv"
MATERIAL_COVERAGE = PROJECT_ROOT / "data" / "validation" / "mismatch_reports" / "rinfo_material_purchase_coverage.csv"
MATERIAL_LIMITATION = PROJECT_ROOT / "data" / "validation" / "mismatch_reports" / "rinfo_material_purchase_detail_mapping_limitation.csv"

COMPARISON_SCHOOLS = {
    "성신여자대학교",
    "숙명여자대학교",
    "덕성여자대학교",
    "서울여자대학교",
    "동덕여자대학교",
    "이화여자대학교",
    "한성대학교",
    "서경대학교",
    "광운대학교",
    "세종대학교",
    "숭실대학교",
}


def _assert_no_inf(path: Path, metric_col: str) -> pd.DataFrame:
    assert path.exists(), f"missing candidate output: {path}"
    frame = pd.read_csv(path)
    metric = pd.to_numeric(frame[metric_col], errors="coerce")
    assert not metric.isin([math.inf, -math.inf]).any()
    assert frame["is_scope34_exact"].eq(True).all()
    assert frame["university_name"].nunique() == 34
    assert len(frame) == 612
    assert COMPARISON_SCHOOLS <= set(frame["university_name"])
    return frame


def test_rinfo_library_staff_scope34_candidate_has_no_inf_and_exact_scope() -> None:
    frame = _assert_no_inf(STAFF_SCOPE_CANDIDATE, "library_staff_per_1000_students_recalculated")
    assert {"ok", "not_calculable_or_missing"} >= set(frame["metric_calc_status"].unique())


def test_rinfo_material_purchase_scope34_candidate_has_no_inf_and_exact_scope() -> None:
    frame = _assert_no_inf(MATERIAL_SCOPE_CANDIDATE, "material_purchase_expense_per_student")
    assert "not_calculable_zero_denominator" in set(frame["metric_calc_status"].unique())


def test_rinfo_reports_disclose_source_gap_scope_leakage_and_comparison_coverage() -> None:
    for report_path in [STAFF_REPORT, MATERIAL_REPORT]:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["status"] == "partial_source_gap_candidate_generated"
        assert report["input"]["raw_source_profile"]["source_preservation_status"] == "gap"
        assert report["no_inf_policy"]["remaining_inf_count"] == 0
        assert report["scope_validation"]["scope34_missing_schools"] == []
        assert report["scope_validation"]["comparison11_present_count"] == 11
        assert "서울사이버대학교" in report["scope_validation"]["simple_filter_extra_schools_excluded_by_exact_scope"]


def test_rinfo_coverage_reports_include_comparison_and_risk_groups() -> None:
    for coverage_path in [STAFF_COVERAGE, MATERIAL_COVERAGE]:
        coverage = pd.read_csv(coverage_path)
        assert set(coverage["coverage_group"]) == {"comparison11", "risk_schools", "scope34"}
        comparison = coverage[coverage["coverage_group"] == "comparison11"]
        assert comparison["present_in_processed"].all()
        assert set(comparison["school_name"]) == COMPARISON_SCHOOLS


def test_rinfo_material_purchase_detail_mapping_limitation_is_reported() -> None:
    limitation = pd.read_csv(MATERIAL_LIMITATION)
    assert limitation.loc[0, "status"] == "mapping_suspect"
    assert bool(limitation.loc[0, "other_electronic_resources_expense_equals_total_all_rows"])
    assert int(limitation.loc[0, "row_count"]) == 8226
