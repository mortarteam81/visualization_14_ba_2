from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_CSV = PROJECT_ROOT / "data/raw/academyinfo/university_key_indicators/2026/academyinfo_key_indicators_2026.csv"
STUDENT_RECRUITMENT_CANDIDATE = PROJECT_ROOT / "data/processed/student_recruitment/student_recruitment_2026_candidate.csv"


def test_academyinfo_key_indicators_raw_csv_was_persisted() -> None:
    assert RAW_CSV.exists()

    frame = pd.read_csv(RAW_CSV)

    assert len(frame) > 0
    assert {
        "공시연도",
        "학교코드",
        "학교명",
        "본분교명",
        "설립유형",
        "지역명",
        "재학생수(학부)",
        "신입생충원율(학부)",
    }.issubset(frame.columns)


def test_student_recruitment_candidate_marks_missing_student_fill_rate() -> None:
    assert STUDENT_RECRUITMENT_CANDIDATE.exists()

    frame = pd.read_csv(STUDENT_RECRUITMENT_CANDIDATE)

    assert len(frame) > 0
    assert "신입생충원율(학부)" in frame.columns
    assert "재학생충원율" in frame.columns
    assert "재학생충원율_확보상태" in frame.columns
    assert frame["재학생충원율"].isna().all()
    assert frame["재학생충원율_확보상태"].str.contains("StudentService API").all()
