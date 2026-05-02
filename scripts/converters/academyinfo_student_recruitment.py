"""Build a student-recruitment candidate from AcademyInfo raw XLSX files.

This converter is intentionally offline/read-only for raw sources.  It combines
AcademyInfo 2025 disclosure files:
- 4-다. 신입생 충원 현황
- 4-라-1. 재학생 충원율
- 4-마. 재적 학생 현황

The existing 2026 key-indicator candidate remains untouched.  This script writes
a v2 candidate and validation metadata/report files so it can be reviewed before
promotion to a current asset.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "pending_manual" / "academyinfo"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "student_recruitment"
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
REPORT_DIR = PROJECT_ROOT / "data" / "validation" / "processing_reports"
MISMATCH_DIR = PROJECT_ROOT / "data" / "validation" / "mismatch_reports"

FRESHMAN_RAW = RAW_DIR / "academyinfo_2025_27_freshman_fill_school.xlsx"
STUDENT_FILL_RAW = RAW_DIR / "academyinfo_2025_29_student_fill_school.xlsx"
ENROLLED_RAW = RAW_DIR / "academyinfo_2025_31_enrolled_students_school.xlsx"
KEY_INDICATOR_CANDIDATE = PROCESSED_DIR / "student_recruitment_2026_candidate.csv"
DEFAULT_OUTPUT = PROCESSED_DIR / "student_recruitment_2026_candidate_v2.csv"
SOURCE_METADATA = METADATA_DIR / "student_recruitment.source.json"
CANDIDATE_METADATA = METADATA_DIR / "student_recruitment_candidate.metadata.json"
PROCESSING_REPORT = REPORT_DIR / "student_recruitment_2026_v2.processing_report.json"
MISMATCH_REPORT = MISMATCH_DIR / "student_recruitment_2026_v2.mismatch.csv"
DEFAULT_SCOPE_PATH = (
    PROJECT_ROOT
    / "data"
    / "metadata"
    / "analysis_scopes"
    / "seoul_private_four_year_universities.json"
)

COMPARISON_SCHOOLS = (
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
)


@dataclass(frozen=True)
class RawSource:
    metric_part: str
    path: Path
    source_section: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_code(value: Any) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    digits = "".join(ch for ch in text if ch.isdigit())
    return digits.zfill(7) if digits else text


def normalize_period(value: Any) -> str:
    if pd.isna(value):
        return ""
    return " ".join(str(value).strip().split())


def split_raw_school_and_campus(value: Any) -> tuple[str, str]:
    """Split AcademyInfo school names like '가톨릭대학교_제2캠퍼스'."""

    text = "" if pd.isna(value) else str(value).strip()
    if "_" in text:
        school, campus = text.rsplit("_", maxsplit=1)
        return school.strip(), campus.strip()
    return text, "본교"


def to_number(value: Any) -> float | None:
    if pd.isna(value):
        return None
    text = str(value).strip().replace(",", "")
    if text in {"", "-"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def read_freshman_raw(path: Path = FRESHMAN_RAW) -> pd.DataFrame:
    raw = pd.read_excel(path, header=None, skiprows=6, engine="openpyxl")
    rows: list[dict[str, Any]] = []
    current_year: int | None = None
    for _, row in raw.iterrows():
        if pd.notna(row.iloc[0]):
            try:
                current_year = int(float(str(row.iloc[0]).strip()))
            except ValueError:
                current_year = None
        school, campus = split_raw_school_and_campus(row.iloc[5] if len(row) > 5 else None)
        if not school or current_year is None:
            continue
        rows.append(
            {
                "신입생충원율(학부)_기준년도_raw27": current_year,
                "학교종류_raw27": row.iloc[1],
                "설립유형_raw27": row.iloc[2],
                "지역명_raw27": row.iloc[3],
                "학교상태_raw27": row.iloc[4],
                "학교명": school,
                "본분교명": campus,
                "입학정원(학부)_raw27": to_number(row.iloc[6]),
                "신입생충원율(학부)_raw27": to_number(row.iloc[18]),
                "신입생경쟁률(학부)_raw27": to_number(row.iloc[19]),
            }
        )
    return pd.DataFrame(rows)


def read_student_fill_raw(path: Path = STUDENT_FILL_RAW) -> pd.DataFrame:
    raw = pd.read_excel(path, header=None, skiprows=5, engine="openpyxl")
    rows: list[dict[str, Any]] = []
    for _, row in raw.iterrows():
        period = normalize_period(row.iloc[0] if len(row) > 0 else None)
        school, campus = split_raw_school_and_campus(row.iloc[5] if len(row) > 5 else None)
        if not period or not school:
            continue
        rows.append(
            {
                "재학생충원율_기준시점": period,
                "학교종류_raw29": row.iloc[1],
                "설립유형_raw29": row.iloc[2],
                "지역명_raw29": row.iloc[3],
                "학교상태_raw29": row.iloc[4],
                "학교명": school,
                "본분교명": campus,
                "학생정원_raw29": to_number(row.iloc[6]),
                "학생모집정지인원_raw29": to_number(row.iloc[7]),
                "재학생수(학부)_raw29": to_number(row.iloc[8]),
                "정원내재학생수_raw29": to_number(row.iloc[9]),
                "재학생충원율": to_number(row.iloc[11]),
                "정원내재학생충원율": to_number(row.iloc[12]),
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    return frame[frame["재학생충원율_기준시점"] == "2025 년 상반기"].copy()


def read_enrolled_raw(path: Path = ENROLLED_RAW) -> pd.DataFrame:
    raw = pd.read_excel(path, header=None, skiprows=6, engine="openpyxl")
    rows: list[dict[str, Any]] = []
    current_year: int | None = None
    for _, row in raw.iterrows():
        if pd.notna(row.iloc[0]):
            try:
                current_year = int(float(str(row.iloc[0]).strip()))
            except ValueError:
                current_year = None
        school, campus = split_raw_school_and_campus(row.iloc[5] if len(row) > 5 else None)
        if not school or current_year is None:
            continue
        rows.append(
            {
                "재학생수(학부)_기준년도_raw31": current_year,
                "학교종류_raw31": row.iloc[1],
                "설립유형_raw31": row.iloc[2],
                "지역명_raw31": row.iloc[3],
                "학교상태_raw31": row.iloc[4],
                "학교명": school,
                "본분교명": campus,
                "학생정원_raw31": to_number(row.iloc[6]),
                "재학생수(학부)_raw31": to_number(row.iloc[7]),
                "정원내재학생수_raw31": to_number(row.iloc[8]),
                "정원외재학생수_raw31": to_number(row.iloc[9]),
            }
        )
    return pd.DataFrame(rows)


def load_existing_candidate(path: Path = KEY_INDICATOR_CANDIDATE) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype={"대표학교코드": str, "학교코드": str})
    frame["대표학교코드"] = frame["대표학교코드"].map(normalize_code)
    frame["학교코드"] = frame["학교코드"].map(normalize_code)
    frame["학교명"] = frame["학교명"].astype(str).str.strip()
    frame["본분교명"] = frame["본분교명"].fillna("본교").astype(str).str.strip()
    return frame


def default_scope_school_names(path: Path = DEFAULT_SCOPE_PATH) -> set[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {str(school["school_name"]).strip() for school in payload.get("schools", [])}


def build_candidate() -> tuple[pd.DataFrame, dict[str, Any], pd.DataFrame]:
    candidate = load_existing_candidate()
    freshman = read_freshman_raw()
    student_fill = read_student_fill_raw()
    enrolled = read_enrolled_raw()
    default_scope = default_scope_school_names()

    merge_keys = ["학교명", "본분교명"]
    result = candidate.merge(
        student_fill[
            merge_keys
            + [
                "재학생충원율_기준시점",
                "학생정원_raw29",
                "학생모집정지인원_raw29",
                "재학생수(학부)_raw29",
                "정원내재학생수_raw29",
                "재학생충원율",
                "정원내재학생충원율",
            ]
        ],
        on=merge_keys,
        how="left",
        suffixes=("", "_from_raw29"),
    )
    result = result.merge(
        freshman[merge_keys + ["입학정원(학부)_raw27", "신입생충원율(학부)_raw27", "신입생경쟁률(학부)_raw27"]],
        on=merge_keys,
        how="left",
    )
    result = result.merge(
        enrolled[merge_keys + ["재학생수(학부)_raw31", "정원내재학생수_raw31", "정원외재학생수_raw31"]],
        on=merge_keys,
        how="left",
    )

    # Replace the legacy all-null placeholder with raw 29 values.
    if "재학생충원율_from_raw29" in result.columns:
        result["재학생충원율"] = result["재학생충원율_from_raw29"]
        result = result.drop(columns=["재학생충원율_from_raw29"])
    result["재학생충원율_확보상태"] = result["재학생충원율"].map(
        lambda value: "대학알리미 4-라-1 2025년 상반기 원자료 병합" if pd.notna(value) else "원자료 29번 매칭 실패"
    )
    result["재학생충원율_원자료파일"] = STUDENT_FILL_RAW.name
    result["raw_source_url"] = "https://academyinfo.go.kr/main/main0830/main0830.do"

    mismatches: list[dict[str, Any]] = []
    for col, raw_col in (
        ("입학정원(학부)", "입학정원(학부)_raw27"),
        ("신입생충원율(학부)", "신입생충원율(학부)_raw27"),
        ("신입생경쟁률(학부)", "신입생경쟁률(학부)_raw27"),
        ("재학생수(학부)", "재학생수(학부)_raw31"),
    ):
        if col not in result.columns or raw_col not in result.columns:
            continue
        left = pd.to_numeric(result[col], errors="coerce")
        right = pd.to_numeric(result[raw_col], errors="coerce")
        mask = left.notna() & right.notna() & ((left - right).abs() > 0.05)
        for _, row in result.loc[mask, ["학교명", "본분교명", col, raw_col]].iterrows():
            mismatches.append(
                {
                    "severity": "high",
                    "field": col,
                    "school_name": row["학교명"],
                    "campus": row["본분교명"],
                    "processed_value": row[col],
                    "raw_value": row[raw_col],
                    "reason": "existing candidate and raw AcademyInfo value differ",
                }
            )

    missing_student_fill = result["재학생충원율"].isna()
    for _, row in result.loc[missing_student_fill, ["학교명", "본분교명"]].iterrows():
        mismatches.append(
            {
                "severity": "medium",
                "field": "재학생충원율",
                "school_name": row["학교명"],
                "campus": row["본분교명"],
                "processed_value": None,
                "raw_value": None,
                "reason": "raw 29 student-fill row was not matched",
            }
        )

    comparison = result[result["학교명"].isin(COMPARISON_SCHOOLS)].copy()
    default_scope_rows = result[result["학교명"].isin(default_scope) & (result["본분교명"] == "본교")].copy()
    report = {
        "dataset_id": "student_recruitment",
        "version": "v2_candidate",
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "source_files": [
            str(FRESHMAN_RAW.relative_to(PROJECT_ROOT)),
            str(STUDENT_FILL_RAW.relative_to(PROJECT_ROOT)),
            str(ENROLLED_RAW.relative_to(PROJECT_ROOT)),
            str(KEY_INDICATOR_CANDIDATE.relative_to(PROJECT_ROOT)),
        ],
        "output_file": str(DEFAULT_OUTPUT.relative_to(PROJECT_ROOT)),
        "row_counts": {
            "existing_candidate": int(len(candidate)),
            "freshman_raw_2025": int(len(freshman)),
            "student_fill_raw_2025_first_half": int(len(student_fill)),
            "enrolled_raw_2025": int(len(enrolled)),
            "processed_candidate_v2": int(len(result)),
        },
        "coverage": {
            "student_fill_non_null_rows": int(result["재학생충원율"].notna().sum()),
            "student_fill_null_rows": int(result["재학생충원율"].isna().sum()),
            "comparison_11_rows": int(len(comparison)),
            "comparison_11_student_fill_non_null": int(comparison["재학생충원율"].notna().sum()),
            "default_scope_34_rows": int(len(default_scope_rows)),
            "default_scope_34_student_fill_non_null": int(default_scope_rows["재학생충원율"].notna().sum()),
        },
        "mismatch_summary": {
            "total": int(len(mismatches)),
            "high": int(sum(item["severity"] == "high" for item in mismatches)),
            "medium": int(sum(item["severity"] == "medium" for item in mismatches)),
        },
        "comparison_11_student_fill_rates": comparison[["학교명", "본분교명", "재학생충원율"]].to_dict("records"),
        "known_limitations": [
            "This is a candidate asset and does not replace the current student_recruitment file automatically.",
            "AcademyInfo raw XLSX files do not contain school_id; merge uses normalized school name plus campus label against the 2026 key-indicator candidate.",
            "Official site re-download/hash verification was not performed in this converter run.",
        ],
    }
    return result, report, pd.DataFrame(mismatches)


def write_metadata(report: dict[str, Any]) -> None:
    sources = [
        RawSource("freshman_fill", FRESHMAN_RAW, "4-다. 신입생 충원 현황"),
        RawSource("student_fill", STUDENT_FILL_RAW, "4-라-1. 재학생 충원율"),
        RawSource("enrolled_students", ENROLLED_RAW, "4-마. 재적 학생 현황"),
    ]
    source_payload = {
        "dataset_id": "student_recruitment",
        "dataset_name_ko": "학생 충원 성과 후보",
        "source_name": "대학알리미",
        "source_org": "한국대학교육협의회",
        "source_url": "https://academyinfo.go.kr/main/main0830/main0830.do",
        "source_section": "공시 데이터 다운로드 > 공시데이터 추이",
        "processed_at": report["processed_at"],
        "raw_files": [
            {
                "metric_part": source.metric_part,
                "source_section": source.source_section,
                "path": str(source.path.relative_to(PROJECT_ROOT)),
                "sha256": sha256_file(source.path),
            }
            for source in sources
        ],
        "notes": [
            "v2 candidate merges AcademyInfo raw item 29 to fill 재학생충원율.",
            "Raw files are local manually acquired XLSX files; no automatic mass download was performed.",
        ],
    }
    candidate_manifest = {
        "dataset_key": "student_recruitment",
        "metric_ids": ["student_recruitment"],
        "title": "학생 충원 성과 후보",
        "candidate_asset": str(DEFAULT_OUTPUT.relative_to(PROJECT_ROOT)),
        "source_data_scope": "national_processed_candidate",
        "verification_status": "candidate_partial",
        "default_analysis_scope": "candidate national school-level values; promotion requires explicit approval",
        "metadata_files": {
            "source": str(SOURCE_METADATA.relative_to(PROJECT_ROOT)),
            "schema": None,
            "report": str(PROCESSING_REPORT.relative_to(PROJECT_ROOT)),
            "guide": None,
        },
        "quality_flags": [
            "candidate_asset",
            "academyinfo_raw_27_29_31_merged",
            "student_fill_rate_populated_from_raw29",
        ],
        "backlog": [
            "Promote to data/metadata/datasets only when the student_recruitment metric is implemented/current.",
            "Add a full schema document before verified promotion.",
        ],
    }
    SOURCE_METADATA.write_text(json.dumps(source_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    CANDIDATE_METADATA.write_text(json.dumps(candidate_manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def write_outputs(output_path: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    MISMATCH_DIR.mkdir(parents=True, exist_ok=True)
    candidate, report, mismatches = build_candidate()
    candidate.to_csv(output_path, index=False, encoding="utf-8-sig")
    report["output_file"] = str(output_path.relative_to(PROJECT_ROOT))
    PROCESSING_REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    mismatches.to_csv(MISMATCH_REPORT, index=False, encoding="utf-8-sig")
    write_metadata(report)
    return report


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    output = args.output if args.output.is_absolute() else PROJECT_ROOT / args.output
    report = write_outputs(output)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
