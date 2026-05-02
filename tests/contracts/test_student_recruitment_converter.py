from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_V2 = PROJECT_ROOT / "data/processed/student_recruitment/student_recruitment_2026_candidate_v2.csv"
PROCESSING_REPORT = PROJECT_ROOT / "data/validation/processing_reports/student_recruitment_2026_v2.processing_report.json"
SOURCE_METADATA = PROJECT_ROOT / "data/metadata/student_recruitment.source.json"
CANDIDATE_METADATA = PROJECT_ROOT / "data/metadata/student_recruitment_candidate.metadata.json"
MISMATCH_REPORT = PROJECT_ROOT / "data/validation/mismatch_reports/student_recruitment_2026_v2.mismatch.csv"

COMPARISON_STUDENT_FILL_RATES = {
    "성신여자대학교": 110.0,
    "숙명여자대학교": 117.0,
    "덕성여자대학교": 120.2,
    "서울여자대학교": 117.2,
    "동덕여자대학교": 101.3,
    "이화여자대학교": 127.2,
    "한성대학교": 118.6,
    "서경대학교": 132.1,
    "광운대학교": 119.6,
    "세종대학교": 133.4,
    "숭실대학교": 136.8,
}


def test_student_recruitment_v2_candidate_populates_comparison_student_fill_rates() -> None:
    assert CANDIDATE_V2.exists()
    frame = pd.read_csv(CANDIDATE_V2)

    assert len(frame) == 489
    assert frame["재학생충원율"].notna().sum() > 0

    comparison = frame[frame["학교명"].isin(COMPARISON_STUDENT_FILL_RATES)]
    assert len(comparison) == len(COMPARISON_STUDENT_FILL_RATES)
    assert comparison["재학생충원율"].notna().all()

    actual = dict(zip(comparison["학교명"], comparison["재학생충원율"]))
    assert actual == COMPARISON_STUDENT_FILL_RATES
    assert comparison["재학생충원율_확보상태"].str.contains("원자료 병합").all()


def test_student_recruitment_v2_preserves_branch_campus_rows() -> None:
    frame = pd.read_csv(CANDIDATE_V2, dtype={"학교코드": str, "대표학교코드": str})

    catholic = frame[frame["학교명"] == "가톨릭대학교"]
    assert set(catholic["본분교명"]) >= {"본교", "제2캠퍼스", "제3캠퍼스"}
    assert catholic["학교코드"].nunique() == len(catholic)

    konkuk_glocal = frame[frame["학교명"] == "건국대학교(글로컬)"]
    assert not konkuk_glocal.empty
    assert set(konkuk_glocal["본분교명"]) == {"분교"}


def test_student_recruitment_v2_processing_report_and_metadata_exist() -> None:
    for path in (PROCESSING_REPORT, SOURCE_METADATA, CANDIDATE_METADATA, MISMATCH_REPORT):
        assert path.exists(), path

    report = json.loads(PROCESSING_REPORT.read_text(encoding="utf-8"))
    assert report["dataset_id"] == "student_recruitment"
    assert report["coverage"]["comparison_11_rows"] == 11
    assert report["coverage"]["comparison_11_student_fill_non_null"] == 11
    assert report["coverage"]["default_scope_34_rows"] == 34
    assert report["coverage"]["default_scope_34_student_fill_non_null"] == 34
    assert report["mismatch_summary"]["high"] == 0

    source = json.loads(SOURCE_METADATA.read_text(encoding="utf-8"))
    raw_files = source["raw_files"]
    assert {item["metric_part"] for item in raw_files} == {
        "freshman_fill",
        "student_fill",
        "enrolled_students",
    }
    assert all(len(item["sha256"]) == 64 for item in raw_files)
