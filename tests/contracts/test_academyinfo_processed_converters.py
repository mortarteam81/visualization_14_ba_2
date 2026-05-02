from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUDAM_CANDIDATE = PROJECT_ROOT / "data/conversion_outputs/academyinfo/budam/budam_2011_2024_candidate.csv"
DORMITORY_CANDIDATE = PROJECT_ROOT / "data/conversion_outputs/academyinfo/dormitory_accommodation_status/dormitory_accommodation_status_2025_candidate.csv"
GYOWON_CANDIDATE = PROJECT_ROOT / "data/conversion_outputs/academyinfo/gyowon/gyowon_2008_2025_candidate.csv"
JIROSUNG_CANDIDATE = PROJECT_ROOT / "data/conversion_outputs/academyinfo/jirosung/jirosung_2008_2024_candidate.csv"
LECTURER_PAY_CANDIDATE = PROJECT_ROOT / "data/conversion_outputs/academyinfo/lecturer_pay/lecturer_pay_2023_2025_candidate.csv"
RESEARCH_CANDIDATE = PROJECT_ROOT / "data/conversion_outputs/academyinfo/research/research_2007_2024_candidate.csv"
PAPER_CANDIDATE = PROJECT_ROOT / "data/conversion_outputs/academyinfo/paper/paper_2007_2024_candidate.csv"
BUDAM_REPORT = PROJECT_ROOT / "data/validation/processing_reports/academyinfo_budam.processing_report.json"
DORMITORY_REPORT = PROJECT_ROOT / "data/validation/processing_reports/academyinfo_dormitory_accommodation_status.processing_report.json"
GYOWON_REPORT = PROJECT_ROOT / "data/validation/processing_reports/academyinfo_gyowon.processing_report.json"
JIROSUNG_REPORT = PROJECT_ROOT / "data/validation/processing_reports/academyinfo_jirosung.processing_report.json"
LECTURER_PAY_REPORT = PROJECT_ROOT / "data/validation/processing_reports/academyinfo_lecturer_pay.processing_report.json"
RESEARCH_REPORT = PROJECT_ROOT / "data/validation/processing_reports/academyinfo_research.processing_report.json"
PAPER_REPORT = PROJECT_ROOT / "data/validation/processing_reports/academyinfo_paper.processing_report.json"
BUDAM_MISMATCH = PROJECT_ROOT / "data/validation/mismatch_reports/academyinfo_budam.mismatch.csv"
DORMITORY_MISMATCH = PROJECT_ROOT / "data/validation/mismatch_reports/academyinfo_dormitory_accommodation_status.mismatch.csv"
GYOWON_MISMATCH = PROJECT_ROOT / "data/validation/mismatch_reports/academyinfo_gyowon.mismatch.csv"
JIROSUNG_MISMATCH = PROJECT_ROOT / "data/validation/mismatch_reports/academyinfo_jirosung.mismatch.csv"
LECTURER_PAY_MISMATCH = PROJECT_ROOT / "data/validation/mismatch_reports/academyinfo_lecturer_pay.mismatch.csv"
RESEARCH_MISMATCH = PROJECT_ROOT / "data/validation/mismatch_reports/academyinfo_research.mismatch.csv"
PAPER_MISMATCH = PROJECT_ROOT / "data/validation/mismatch_reports/academyinfo_paper.mismatch.csv"


def _load_report(path: Path) -> dict:
    assert path.exists(), path
    return json.loads(path.read_text(encoding="utf-8"))


def test_academyinfo_budam_candidate_outputs_are_raw_backed_and_national() -> None:
    assert BUDAM_CANDIDATE.exists()
    assert BUDAM_MISMATCH.exists()
    frame = pd.read_csv(BUDAM_CANDIDATE)
    mismatch = pd.read_csv(BUDAM_MISMATCH)
    report = _load_report(BUDAM_REPORT)

    assert str(BUDAM_CANDIDATE.relative_to(PROJECT_ROOT)) == report["output_file"]
    assert report["version"] == "academyinfo_budam_raw_xlsx_candidate_v1"
    assert report["source_input_kind"] == "raw_xlsx"
    assert report["source_preservation_status"] == "raw_preserved"
    assert report["row_counts"]["source_input_rows"] == 2424
    assert report["row_counts"]["candidate_rows"] == len(frame) == 2424
    assert report["row_counts"]["mismatch_rows"] == len(mismatch) == 0
    assert report["coverage"]["comparison_11_present_latest_year"] == 11
    assert report["coverage"]["default_scope_34_present_latest_year"] == 34
    assert set(frame.columns) >= {"기준년도", "학교명", "부담율"}
    assert frame["학교명"].eq("성신여자대학교").any()


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


def test_academyinfo_gyowon_candidate_outputs_are_raw_backed_and_national() -> None:
    assert GYOWON_CANDIDATE.exists()
    assert GYOWON_MISMATCH.exists()
    frame = pd.read_csv(GYOWON_CANDIDATE)
    mismatch = pd.read_csv(GYOWON_MISMATCH)
    report = _load_report(GYOWON_REPORT)

    assert str(GYOWON_CANDIDATE.relative_to(PROJECT_ROOT)) == report["output_file"]
    assert report["version"] == "academyinfo_gyowon_raw_xlsx_candidate_v1"
    assert report["source_input_kind"] == "raw_xlsx"
    assert report["source_preservation_status"] == "raw_preserved"
    assert report["row_counts"]["source_input_rows"] == 4563
    assert report["row_counts"]["candidate_rows"] == len(frame) == 3106
    assert report["row_counts"]["mismatch_rows"] == len(mismatch) == 1
    assert report["coverage"]["comparison_11_present_latest_year"] == 11
    assert report["coverage"]["default_scope_34_present_latest_year"] == 34
    assert set(frame.columns) >= {"기준년도", "학교명", "전임교원 확보율(학생정원 기준)", "전임교원 확보율(재학생 기준)"}
    assert frame["학교명"].eq("성신여자대학교").any()


def test_academyinfo_research_candidate_outputs_are_raw_backed_and_national() -> None:
    assert RESEARCH_CANDIDATE.exists()
    assert RESEARCH_MISMATCH.exists()
    frame = pd.read_csv(RESEARCH_CANDIDATE)
    mismatch = pd.read_csv(RESEARCH_MISMATCH)
    report = _load_report(RESEARCH_REPORT)

    assert str(RESEARCH_CANDIDATE.relative_to(PROJECT_ROOT)) == report["output_file"]
    assert report["version"] == "academyinfo_research_raw_xlsx_candidate_v1"
    assert report["source_input_kind"] == "raw_xlsx"
    assert report["source_preservation_status"] == "raw_preserved"
    assert report["row_counts"]["source_input_rows"] == 4444
    assert report["row_counts"]["candidate_rows"] == len(frame) == 3108
    assert report["row_counts"]["mismatch_rows"] == len(mismatch) == 0
    assert report["coverage"]["comparison_11_present_latest_year"] == 11
    assert report["coverage"]["default_scope_34_present_latest_year"] == 34
    assert set(frame.columns) >= {"기준년도", "학교명", "전임교원 1인당 연구비(교내)", "전임교원 1인당 연구비(교외)"}
    assert frame["학교명"].eq("성신여자대학교").any()


def test_academyinfo_paper_candidate_outputs_are_raw_backed_and_national() -> None:
    assert PAPER_CANDIDATE.exists()
    assert PAPER_MISMATCH.exists()
    frame = pd.read_csv(PAPER_CANDIDATE)
    mismatch = pd.read_csv(PAPER_MISMATCH)
    report = _load_report(PAPER_REPORT)

    assert str(PAPER_CANDIDATE.relative_to(PROJECT_ROOT)) == report["output_file"]
    assert report["version"] == "academyinfo_paper_raw_xlsx_candidate_v1"
    assert report["source_input_kind"] == "raw_xlsx"
    assert report["source_preservation_status"] == "raw_preserved"
    assert report["row_counts"]["source_input_rows"] == 4445
    assert report["row_counts"]["candidate_rows"] == len(frame) == 3108
    assert report["row_counts"]["mismatch_rows"] == len(mismatch) == 0
    assert report["coverage"]["comparison_11_present_latest_year"] == 11
    assert report["coverage"]["default_scope_34_present_latest_year"] == 34
    assert set(frame.columns) >= {
        "기준년도",
        "학교명",
        "전임교원1인당논문실적(국내, 연구재단등재지(후보포함))",
        "전임교원1인당논문실적(국제, SCI급/SCOPUS학술지)",
    }
    assert frame["학교명"].eq("성신여자대학교").any()


def test_academyinfo_jirosung_candidate_outputs_are_raw_backed_and_national() -> None:
    assert JIROSUNG_CANDIDATE.exists()
    assert JIROSUNG_MISMATCH.exists()
    frame = pd.read_csv(JIROSUNG_CANDIDATE)
    mismatch = pd.read_csv(JIROSUNG_MISMATCH)
    report = _load_report(JIROSUNG_REPORT)

    assert str(JIROSUNG_CANDIDATE.relative_to(PROJECT_ROOT)) == report["output_file"]
    assert report["version"] == "academyinfo_jirosung_raw_xlsx_candidate_v1"
    assert report["source_input_kind"] == "raw_xlsx"
    assert report["source_preservation_status"] == "raw_preserved"
    assert report["row_counts"]["source_input_rows"] == 5387
    assert report["row_counts"]["candidate_rows"] == len(frame) == 3678
    assert report["row_counts"]["mismatch_rows"] == len(mismatch) == 0
    assert report["coverage"]["comparison_11_present_latest_year"] == 11
    assert report["coverage"]["default_scope_34_present_latest_year"] == 34
    assert set(frame.columns) >= {"기준년도", "학교명", "본분교명", "졸업생_진로_성과"}
    assert frame["학교명"].eq("성신여자대학교").any()


def test_academyinfo_dormitory_mismatch_report_captures_current_asset_drift() -> None:
    frame = pd.read_csv(DORMITORY_MISMATCH)

    assert set(frame.columns) >= {"severity", "field", "school_name", "year", "processed_value", "raw_value", "reason", "source_path"}
    assert len(frame) == 7
    assert {"성균관대학교", "홍익대학교"}.issubset(set(frame["school_name"]))
    assert "Current dashboard asset value differs from raw-XLSX candidate value." in set(frame["reason"])


def test_academyinfo_gyowon_mismatch_report_captures_single_current_asset_drift() -> None:
    frame = pd.read_csv(GYOWON_MISMATCH)

    assert len(frame) == 1
    row = frame.iloc[0]
    assert row["severity"] == "medium"
    assert row["school_name"] == "성균관대학교"
    assert int(row["year"]) == 2024
    assert row["field"] == "전임교원 확보율(재학생 기준)"
    assert row["reason"] == "Current dashboard asset value differs from raw-XLSX candidate value."


def test_academyinfo_lecturer_pay_gap_mismatch_report_is_nonempty_and_medium_severity() -> None:
    frame = pd.read_csv(LECTURER_PAY_MISMATCH)

    assert len(frame) == 1
    assert frame["severity"].tolist() == ["medium"]
    assert frame["reason"].str.contains("original AcademyInfo XLSX", case=False).all()
