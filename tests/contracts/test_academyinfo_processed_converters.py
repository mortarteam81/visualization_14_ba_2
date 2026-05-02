from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DORMITORY_CANDIDATE = PROJECT_ROOT / "data/conversion_outputs/academyinfo/dormitory_accommodation_status/dormitory_accommodation_status_2025_candidate.csv"
LECTURER_PAY_CANDIDATE = PROJECT_ROOT / "data/conversion_outputs/academyinfo/lecturer_pay/lecturer_pay_2023_2025_candidate.csv"
DORMITORY_REPORT = PROJECT_ROOT / "data/validation/processing_reports/academyinfo_dormitory_accommodation_status.processing_report.json"
LECTURER_PAY_REPORT = PROJECT_ROOT / "data/validation/processing_reports/academyinfo_lecturer_pay.processing_report.json"
DORMITORY_MISMATCH = PROJECT_ROOT / "data/validation/mismatch_reports/academyinfo_dormitory_accommodation_status.mismatch.csv"
LECTURER_PAY_MISMATCH = PROJECT_ROOT / "data/validation/mismatch_reports/academyinfo_lecturer_pay.mismatch.csv"


def _load_report(path: Path) -> dict:
    assert path.exists(), path
    return json.loads(path.read_text(encoding="utf-8"))


def test_academyinfo_dormitory_candidate_outputs_are_separate_and_covered() -> None:
    assert DORMITORY_CANDIDATE.exists()
    assert DORMITORY_MISMATCH.exists()
    frame = pd.read_csv(DORMITORY_CANDIDATE)
    mismatch = pd.read_csv(DORMITORY_MISMATCH)
    report = _load_report(DORMITORY_REPORT)

    assert str(DORMITORY_CANDIDATE.relative_to(PROJECT_ROOT)) == report["output_file"]
    assert report["version"] == "academyinfo_dormitory_raw_xlsx_candidate_v1"
    assert report["source_input_kind"] == "raw_xlsx"
    assert report["source_preservation_status"] == "raw_preserved"
    assert report["row_counts"]["source_input_rows"] == 4145
    assert report["row_counts"]["candidate_rows"] == len(frame) == 602
    assert report["row_counts"]["mismatch_rows"] == len(mismatch) == 7
    assert set(mismatch["severity"]) == {"medium"}
    assert report["coverage"]["comparison_11_present_latest_year"] == 11
    assert report["coverage"]["default_scope_34_present_latest_year"] == 34
    assert set(frame.columns) >= {"기준년도", "학교명", "기숙사수용률"}
    assert frame["학교명"].eq("성신여자대학교").any()


def test_academyinfo_lecturer_pay_candidate_outputs_are_separate_and_gap_reported() -> None:
    assert LECTURER_PAY_CANDIDATE.exists()
    assert LECTURER_PAY_MISMATCH.exists()
    frame = pd.read_csv(LECTURER_PAY_CANDIDATE)
    report = _load_report(LECTURER_PAY_REPORT)

    assert str(LECTURER_PAY_CANDIDATE.relative_to(PROJECT_ROOT)) == report["output_file"]
    assert report["source_preservation_status"] == "gap_original_xlsx_missing"
    assert report["row_counts"]["candidate_rows"] == len(frame) == 99
    assert report["coverage"]["comparison_11_present_latest_year"] == 11
    assert report["coverage"]["default_scope_34_present_latest_year"] == 33
    assert report["coverage"]["default_scope_34_missing_latest_year"] == ["감리교신학대학교"]
    assert set(frame.columns) >= {"기준년도", "학교명", "강사강의료"}


def test_academyinfo_dormitory_mismatch_report_captures_current_asset_drift() -> None:
    frame = pd.read_csv(DORMITORY_MISMATCH)

    assert set(frame.columns) >= {"severity", "field", "school_name", "year", "processed_value", "raw_value", "reason", "source_path"}
    assert len(frame) == 7
    assert {"성균관대학교", "홍익대학교"}.issubset(set(frame["school_name"]))
    assert "Current dashboard asset value differs from raw-XLSX candidate value." in set(frame["reason"])


def test_academyinfo_lecturer_pay_gap_mismatch_report_is_nonempty_and_medium_severity() -> None:
    frame = pd.read_csv(LECTURER_PAY_MISMATCH)

    assert len(frame) == 1
    assert frame["severity"].tolist() == ["medium"]
    assert frame["reason"].str.contains("original AcademyInfo XLSX", case=False).all()
