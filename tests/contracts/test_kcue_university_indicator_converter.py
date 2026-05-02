from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_DIR = PROJECT_ROOT / "data/conversion_outputs/kcue"
CANDIDATE_WIDE = CANDIDATE_DIR / "kcue_university_indicators_2015_2025_v1_candidate_utf8.csv"
CANDIDATE_LONG = CANDIDATE_DIR / "kcue_university_metric_values_2015_2025_v1_candidate_utf8.csv"
STAFF_PER_STUDENT_CANDIDATE = CANDIDATE_DIR / "staff_per_student_2015_2025_candidate.csv"
SOURCE_METADATA = CANDIDATE_DIR / "kcue_university_indicators_v1_candidate.source.json"
CANDIDATE_METADATA = CANDIDATE_DIR / "kcue_university_indicators_v1_candidate.metadata.json"
PROCESSING_REPORT = PROJECT_ROOT / "data/validation/processing_reports/kcue_university_indicators_v1_candidate.processing_report.json"
MISMATCH_REPORT = PROJECT_ROOT / "data/validation/mismatch_reports/kcue_university_indicators_v1_candidate.mismatch.csv"
STAFF_PER_STUDENT_PROCESSING_REPORT = PROJECT_ROOT / "data/validation/processing_reports/kcue_staff_per_student.processing_report.json"
STAFF_PER_STUDENT_MISMATCH_REPORT = PROJECT_ROOT / "data/validation/mismatch_reports/kcue_staff_per_student.mismatch.csv"
STAFF_PER_STUDENT_DOWNLOAD_CROSSCHECK_REPORT = PROJECT_ROOT / "data/validation/mismatch_reports/kcue_staff_per_student_download_crosscheck.csv"
STAFF_PER_STUDENT_SOURCE_ACQUISITION = PROJECT_ROOT / "data/raw/kcue_university_indicators/staff_per_student_verification/source_acquisition.json"

CURRENT_WIDE = PROJECT_ROOT / "data/processed/kcue_university_indicators/kcue_university_indicators_2015_2025_v1_utf8.csv"
CURRENT_LONG = PROJECT_ROOT / "data/processed/kcue_university_indicators/kcue_university_metric_values_2015_2025_v1_utf8.csv"

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

SOURCE_VALUE_ONLY_2025 = {
    "adjunct_faculty_rate",
    "faculty_combined_rate",
    "full_time_faculty_rate",
    "research_performance_vs_standard",
    "student_recruitment_performance",
}


def test_kcue_candidate_outputs_exist_and_match_current_shape() -> None:
    for path in (
        CANDIDATE_WIDE,
        CANDIDATE_LONG,
        STAFF_PER_STUDENT_CANDIDATE,
        SOURCE_METADATA,
        CANDIDATE_METADATA,
        PROCESSING_REPORT,
        MISMATCH_REPORT,
        STAFF_PER_STUDENT_PROCESSING_REPORT,
        STAFF_PER_STUDENT_MISMATCH_REPORT,
        STAFF_PER_STUDENT_DOWNLOAD_CROSSCHECK_REPORT,
        STAFF_PER_STUDENT_SOURCE_ACQUISITION,
    ):
        assert path.exists(), path

    candidate_wide = pd.read_csv(CANDIDATE_WIDE)
    candidate_long = pd.read_csv(CANDIDATE_LONG)
    current_wide = pd.read_csv(CURRENT_WIDE)
    current_long = pd.read_csv(CURRENT_LONG)

    assert candidate_wide.shape == current_wide.shape == (2054, 111)
    assert candidate_long.shape == current_long.shape == (43184, 14)
    assert list(candidate_wide.columns) == list(current_wide.columns)
    assert list(candidate_long.columns) == list(current_long.columns)


def test_kcue_candidate_processing_report_records_zero_mismatch_and_coverage() -> None:
    report = json.loads(PROCESSING_REPORT.read_text(encoding="utf-8"))
    assert report["dataset_id"] == "kcue_university_indicators"
    assert report["raw_file_count"] == 11
    assert report["row_counts"]["wide_candidate"] == 2054
    assert report["row_counts"]["long_candidate"] == 43184
    assert report["mismatch_summary"] == {"total": 0, "high": 0}

    comparison = report["coverage"]["comparison_11"]
    assert comparison["present_school_count"] == 11
    assert set(comparison["years_by_school"]) == COMPARISON_SCHOOLS
    assert all(years == list(range(2015, 2026)) for years in comparison["years_by_school"].values())

    assert report["coverage"]["outlier_schools"]["present_school_count"] == 5
    assert report["coverage"]["risk_schools"]["present_school_count"] >= 13


def test_kcue_candidate_reports_4th_cycle_source_value_only_metrics() -> None:
    report = json.loads(PROCESSING_REPORT.read_text(encoding="utf-8"))
    source_only = {item["metric_id"]: item for item in report["source_value_only_4th_cycle"]}
    assert set(source_only) == SOURCE_VALUE_ONLY_2025
    assert all(item["status"] == "source_value_only" for item in source_only.values())
    assert all(item["reference_years"] == [2025] for item in source_only.values())
    assert all(item["rows"] == 184 for item in source_only.values())


def test_kcue_candidate_metadata_has_raw_hashes_and_review_policy() -> None:
    source = json.loads(SOURCE_METADATA.read_text(encoding="utf-8"))
    assert source["source_url"] == "https://aims.kcue.or.kr/EgovPageLink.do?subMenu=5020000"
    assert len(source["raw_files"]) == 11
    assert all(len(item["sha256"]) == 64 for item in source["raw_files"])

    metadata = json.loads(CANDIDATE_METADATA.read_text(encoding="utf-8"))
    assert metadata["verification_status"] == "candidate_verified_against_current"
    assert "Do not promote automatically" in metadata["promotion_policy"]
    assert metadata["candidate_assets"]["wide"].startswith("data/conversion_outputs/kcue/")

    mismatch = pd.read_csv(MISMATCH_REPORT)
    assert list(mismatch.columns) == ["asset", "severity", "key", "column", "candidate_value", "current_value", "reason"]
    assert mismatch.empty


def test_kcue_staff_per_student_candidate_is_validation_ready() -> None:
    candidate = pd.read_csv(STAFF_PER_STUDENT_CANDIDATE)
    report = json.loads(STAFF_PER_STUDENT_PROCESSING_REPORT.read_text(encoding="utf-8"))
    mismatch = pd.read_csv(STAFF_PER_STUDENT_MISMATCH_REPORT)
    download_crosscheck = pd.read_csv(STAFF_PER_STUDENT_DOWNLOAD_CROSSCHECK_REPORT)
    source_acquisition = json.loads(STAFF_PER_STUDENT_SOURCE_ACQUISITION.read_text(encoding="utf-8"))

    assert candidate.shape[0] == 374
    assert candidate["기준년도"].min() == 2015
    assert candidate["기준년도"].max() == 2025
    assert candidate["학교명"].nunique() == 34
    assert "직원1인당학생수" in candidate.columns
    assert report["dataset_id"] == "staff_per_student"
    assert report["source_dataset_id"] == "kcue_university_indicators"
    assert report["source_preservation_status"] == "raw_preserved"
    assert report["source_input_kind"] == "raw_xlsx"
    assert report["row_counts"]["source_input_rows"] == 2054
    assert report["row_counts"]["candidate_rows"] == 374
    assert report["mismatch_summary"] == {"total": 0, "high": 0, "medium": 0}
    assert report["official_download_crosscheck"]["status"] == "matched"
    assert report["official_download_crosscheck"]["checked_rows"] == 552
    assert report["official_download_crosscheck"]["mismatch_rows"] == 0
    assert report["official_download_crosscheck"]["verification_file_count"] == 1
    assert source_acquisition["download_purpose"] == "데이터 분석"
    assert "email" not in json.dumps(source_acquisition, ensure_ascii=False).lower()
    assert len(source_acquisition["verification_files"]) == 1
    assert list(mismatch.columns) == [
        "severity",
        "field",
        "school_name",
        "year",
        "processed_value",
        "raw_value",
        "reason",
        "source_path",
    ]
    assert mismatch.empty
    assert list(download_crosscheck.columns) == [
        "severity",
        "school_name",
        "year",
        "downloaded_value",
        "processed_value",
        "display_value",
        "reason",
        "source_path",
    ]
    assert download_crosscheck.empty
