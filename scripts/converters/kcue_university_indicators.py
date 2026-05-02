"""Build KCUE university-indicator candidate outputs without touching current assets.

This converter wraps the existing KCUE parsing/build logic and redirects all
outputs to review-only candidate/validation paths.  It reads local raw XLSX
files as read-only input, compares the generated candidate to the current
processed wide/long assets, and writes source metadata plus coverage reports for
review before any explicit promotion.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import build_kcue_university_indicators as builder
from utils.data_pipeline import prepare_staff_per_student_frame

DATASET_ID = "kcue_university_indicators"
STAFF_PER_STUDENT_DATASET_ID = "staff_per_student"
VERSION = "v1_candidate"

RAW_DIR = PROJECT_ROOT / "data" / "raw" / DATASET_ID / "original"
OUTPUT_DIR = PROJECT_ROOT / "data" / "conversion_outputs" / "kcue"
VALIDATION_REPORT_DIR = PROJECT_ROOT / "data" / "validation" / "processing_reports"
MISMATCH_REPORT_DIR = PROJECT_ROOT / "data" / "validation" / "mismatch_reports"

CANDIDATE_WIDE = OUTPUT_DIR / "kcue_university_indicators_2015_2025_v1_candidate_utf8.csv"
CANDIDATE_LONG = OUTPUT_DIR / "kcue_university_metric_values_2015_2025_v1_candidate_utf8.csv"
SOURCE_METADATA = OUTPUT_DIR / "kcue_university_indicators_v1_candidate.source.json"
CANDIDATE_METADATA = OUTPUT_DIR / "kcue_university_indicators_v1_candidate.metadata.json"
PROCESSING_REPORT = VALIDATION_REPORT_DIR / "kcue_university_indicators_v1_candidate.processing_report.json"
MISMATCH_REPORT = MISMATCH_REPORT_DIR / "kcue_university_indicators_v1_candidate.mismatch.csv"
STAFF_PER_STUDENT_CANDIDATE = OUTPUT_DIR / "staff_per_student_2015_2025_candidate.csv"
STAFF_PER_STUDENT_PROCESSING_REPORT = VALIDATION_REPORT_DIR / "kcue_staff_per_student.processing_report.json"
STAFF_PER_STUDENT_MISMATCH_REPORT = MISMATCH_REPORT_DIR / "kcue_staff_per_student.mismatch.csv"
STAFF_PER_STUDENT_DOWNLOAD_CROSSCHECK_REPORT = MISMATCH_REPORT_DIR / "kcue_staff_per_student_download_crosscheck.csv"
STAFF_PER_STUDENT_VERIFICATION_RAW_DIR = (
    PROJECT_ROOT / "data" / "raw" / DATASET_ID / "staff_per_student_verification" / "original"
)
STAFF_PER_STUDENT_SOURCE_ACQUISITION = (
    PROJECT_ROOT / "data" / "raw" / DATASET_ID / "staff_per_student_verification" / "source_acquisition.json"
)

CURRENT_WIDE = PROJECT_ROOT / builder.WIDE_OUTPUT
CURRENT_LONG = PROJECT_ROOT / builder.LONG_OUTPUT

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

RISK_SCHOOLS = (
    "가톨릭대학교",
    "건국대학교",
    "건국대학교(글로컬)",
    "고려대학교",
    "고려대학교(세종)",
    "동국대학교",
    "동국대학교(WISE)",
    "연세대학교",
    "연세대학교(미래)",
    "한양대학교",
    "한양대학교(ERICA)",
    "강서대학교",
    "케이씨대학교",
    "그리스도대학교",
    "서울한영대학교",
    "한영신학대학교",
)

OUTLIER_SCHOOLS = (
    "감리교신학대학교",
    "서울기독대학교",
    "대전가톨릭대학교",
    "영산선학대학교",
    "칼빈대학교",
)

MISMATCH_COLUMNS = [
    "asset",
    "severity",
    "key",
    "column",
    "candidate_value",
    "current_value",
    "reason",
]

STAFF_PER_STUDENT_MISMATCH_COLUMNS = [
    "severity",
    "field",
    "school_name",
    "year",
    "processed_value",
    "raw_value",
    "reason",
    "source_path",
]

STAFF_PER_STUDENT_DOWNLOAD_CROSSCHECK_COLUMNS = [
    "severity",
    "school_name",
    "year",
    "downloaded_value",
    "processed_value",
    "display_value",
    "reason",
    "source_path",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def normalize_for_compare(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    for column in normalized.columns:
        if normalized[column].dtype == object:
            normalized[column] = normalized[column].where(normalized[column].notna(), None)
    return normalized


def compare_frames(candidate: pd.DataFrame, current: pd.DataFrame, key_columns: list[str], asset: str) -> pd.DataFrame:
    mismatches: list[dict[str, Any]] = []
    if list(candidate.columns) != list(current.columns):
        mismatches.append(
            {
                "asset": asset,
                "severity": "high",
                "key": "__columns__",
                "column": "__columns__",
                "candidate_value": "|".join(candidate.columns),
                "current_value": "|".join(current.columns),
                "reason": "candidate and current column order/names differ",
            }
        )
        # Compare common columns anyway so the report remains useful.
        common = [col for col in candidate.columns if col in current.columns]
        candidate = candidate[common]
        current = current[common]

    candidate_cmp = normalize_for_compare(candidate).sort_values(key_columns).reset_index(drop=True)
    current_cmp = normalize_for_compare(current).sort_values(key_columns).reset_index(drop=True)

    if len(candidate_cmp) != len(current_cmp):
        mismatches.append(
            {
                "asset": asset,
                "severity": "high",
                "key": "__row_count__",
                "column": "__row_count__",
                "candidate_value": len(candidate_cmp),
                "current_value": len(current_cmp),
                "reason": "candidate and current row counts differ",
            }
        )

    comparable_rows = min(len(candidate_cmp), len(current_cmp))
    compare_columns = [column for column in candidate_cmp.columns if column in current_cmp.columns]
    for idx in range(comparable_rows):
        key = ";".join(f"{column}={candidate_cmp.at[idx, column]}" for column in key_columns)
        for column in compare_columns:
            left = candidate_cmp.at[idx, column]
            right = current_cmp.at[idx, column]
            if pd.isna(left) and pd.isna(right):
                continue
            if pd.api.types.is_number(left) or pd.api.types.is_number(right):
                left_num = pd.to_numeric(left, errors="coerce")
                right_num = pd.to_numeric(right, errors="coerce")
                if pd.isna(left_num) and pd.isna(right_num):
                    continue
                if pd.isna(left_num) != pd.isna(right_num) or abs(float(left_num) - float(right_num)) > 1e-3:
                    mismatches.append(
                        {
                            "asset": asset,
                            "severity": "high",
                            "key": key,
                            "column": column,
                            "candidate_value": left,
                            "current_value": right,
                            "reason": "numeric candidate/current value differ",
                        }
                    )
            elif str(left) != str(right):
                mismatches.append(
                    {
                        "asset": asset,
                        "severity": "high",
                        "key": key,
                        "column": column,
                        "candidate_value": left,
                        "current_value": right,
                        "reason": "candidate/current value differ",
                    }
                )
    return pd.DataFrame(mismatches, columns=MISMATCH_COLUMNS)


def coverage_for(wide: pd.DataFrame, schools: Sequence[str]) -> dict[str, Any]:
    present = sorted(set(wide.loc[wide["university_name"].isin(schools), "university_name"]))
    return {
        "expected_school_count": len(schools),
        "present_school_count": len(present),
        "missing_schools": [school for school in schools if school not in present],
        "rows": int(wide[wide["university_name"].isin(schools)].shape[0]),
        "years_by_school": {
            school: sorted(int(year) for year in years)
            for school, years in wide[wide["university_name"].isin(schools)].groupby("university_name")["reference_year"].unique().items()
        },
    }


def source_value_only_report(long: pd.DataFrame) -> list[dict[str, Any]]:
    cycle4 = long[long["evaluation_cycle"] == 4].copy()
    source_only = cycle4[
        cycle4["value_original"].notna()
        & cycle4["value_recalculated"].isna()
        & cycle4["numerator"].isna()
        & cycle4["denominator"].isna()
    ]
    rows: list[dict[str, Any]] = []
    for metric_id, group in source_only.groupby("metric_id"):
        rows.append(
            {
                "metric_id": metric_id,
                "metric_label_ko": str(group["metric_label_ko"].iloc[0]),
                "reference_years": sorted(int(year) for year in group["reference_year"].unique()),
                "rows": int(len(group)),
                "status": "source_value_only",
                "reason": "4주기 원자료에 분자/분모 또는 재계산값 없이 지표값만 제공됨",
            }
        )
    return rows


def _values_differ(left: object, right: object, *, tolerance: float = 1e-3) -> bool:
    if pd.isna(left) and pd.isna(right):
        return False
    left_num = pd.to_numeric(pd.Series([left]), errors="coerce").iloc[0]
    right_num = pd.to_numeric(pd.Series([right]), errors="coerce").iloc[0]
    if pd.notna(left_num) or pd.notna(right_num):
        if pd.isna(left_num) or pd.isna(right_num):
            return True
        return abs(float(left_num) - float(right_num)) > tolerance
    return str(left) != str(right)


def _truncate_to_one_decimal(value: object) -> float | None:
    if pd.isna(value):
        return None
    return int(float(value) * 10) / 10


def compare_staff_per_student_candidate(candidate: pd.DataFrame, current: pd.DataFrame) -> pd.DataFrame:
    fields = ["직원1인당학생수", "분자", "분모"]
    key_columns = ["기준년도", "학교명"]
    candidate_columns = key_columns + fields + ["원본파일명"]
    current_columns = key_columns + fields
    candidate_cmp = candidate[candidate_columns].copy()
    current_cmp = current[current_columns].copy()
    merged = current_cmp.merge(
        candidate_cmp,
        on=key_columns,
        how="outer",
        suffixes=("_current", "_candidate"),
        indicator=True,
    )

    rows: list[dict[str, Any]] = []
    for _, row in merged.iterrows():
        school_name = row.get("학교명")
        year = row.get("기준년도")
        source_path = row.get("원본파일명")
        if row["_merge"] != "both":
            rows.append(
                {
                    "severity": "high",
                    "field": "__row__",
                    "school_name": school_name,
                    "year": year,
                    "processed_value": "" if row["_merge"] == "right_only" else "present",
                    "raw_value": "present" if row["_merge"] == "right_only" else "",
                    "reason": f"row present in {row['_merge']} only",
                    "source_path": source_path,
                }
            )
            continue
        for field in fields:
            current_value = row.get(f"{field}_current")
            candidate_value = row.get(f"{field}_candidate")
            if _values_differ(candidate_value, current_value):
                rows.append(
                    {
                        "severity": "medium" if field != "직원1인당학생수" else "high",
                        "field": field,
                        "school_name": school_name,
                        "year": year,
                        "processed_value": current_value,
                        "raw_value": candidate_value,
                        "reason": "candidate/current value differ",
                        "source_path": source_path,
                    }
                )
    return pd.DataFrame(rows, columns=STAFF_PER_STUDENT_MISMATCH_COLUMNS)


def build_staff_per_student_download_crosscheck(long: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    files = sorted(STAFF_PER_STUDENT_VERIFICATION_RAW_DIR.glob("*직원*학생수*.xlsx"))
    if not files:
        return (
            pd.DataFrame(columns=STAFF_PER_STUDENT_DOWNLOAD_CROSSCHECK_COLUMNS),
            {
                "status": "not_available",
                "checked_rows": 0,
                "mismatch_rows": 0,
                "verification_file_count": 0,
            },
        )

    downloaded_frames: list[pd.DataFrame] = []
    for path in files:
        raw = pd.read_excel(path, header=None)
        if raw.empty:
            continue
        frame = raw.iloc[1:].copy()
        frame.columns = raw.iloc[0].tolist()
        year_columns = [column for column in frame.columns if str(column).replace(".", "", 1).isdigit()]
        melted = frame.melt(
            id_vars=["대학명"],
            value_vars=year_columns,
            var_name="year",
            value_name="downloaded_value",
        )
        melted["year"] = pd.to_numeric(melted["year"], errors="coerce").astype("Int64")
        melted["downloaded_value"] = pd.to_numeric(melted["downloaded_value"], errors="coerce")
        melted["source_path"] = rel(path)
        downloaded_frames.append(melted.dropna(subset=["대학명", "year", "downloaded_value"]))

    if not downloaded_frames:
        return (
            pd.DataFrame(columns=STAFF_PER_STUDENT_DOWNLOAD_CROSSCHECK_COLUMNS),
            {
                "status": "empty_download",
                "checked_rows": 0,
                "mismatch_rows": 0,
                "verification_file_count": len(files),
            },
        )

    downloaded = pd.concat(downloaded_frames, ignore_index=True)
    staff_source = long[long["metric_id"].astype(str).str.strip() == "students_per_staff"].copy()
    source_values = staff_source[["university_name", "reference_year", "value"]].copy()
    merged = downloaded.merge(
        source_values,
        left_on=["대학명", "year"],
        right_on=["university_name", "reference_year"],
        how="left",
    )

    rows: list[dict[str, Any]] = []
    for _, row in merged.iterrows():
        processed_value = row.get("value")
        display_value = _truncate_to_one_decimal(processed_value)
        downloaded_value = row.get("downloaded_value")
        if pd.isna(processed_value):
            rows.append(
                {
                    "severity": "high",
                    "school_name": row.get("대학명"),
                    "year": int(row.get("year")),
                    "downloaded_value": downloaded_value,
                    "processed_value": "",
                    "display_value": "",
                    "reason": "downloaded row not found in processed KCUE staff source",
                    "source_path": row.get("source_path"),
                }
            )
            continue
        if abs(float(downloaded_value) - float(display_value)) > 1e-9:
            rows.append(
                {
                    "severity": "high",
                    "school_name": row.get("대학명"),
                    "year": int(row.get("year")),
                    "downloaded_value": downloaded_value,
                    "processed_value": processed_value,
                    "display_value": display_value,
                    "reason": "downloaded display value differs from processed value truncated to one decimal",
                    "source_path": row.get("source_path"),
                }
            )

    crosscheck = pd.DataFrame(rows, columns=STAFF_PER_STUDENT_DOWNLOAD_CROSSCHECK_COLUMNS)
    return (
        crosscheck,
        {
            "status": "matched" if crosscheck.empty else "mismatch_found",
            "checked_rows": int(len(merged)),
            "mismatch_rows": int(len(crosscheck)),
            "verification_file_count": len(files),
            "display_value_policy": "KCUE page download displays 직원 1인당 학생수 to one decimal by truncation.",
            "verification_files": [rel(path) for path in files],
            "mismatch_report": rel(STAFF_PER_STUDENT_DOWNLOAD_CROSSCHECK_REPORT),
        },
    )


def write_staff_per_student_source_acquisition(processed_at: str) -> None:
    raw_files: list[dict[str, Any]] = []
    for path in sorted(RAW_DIR.glob("*.xlsx")):
        year, cycle, name = builder.parse_file_info(path)
        raw_files.append(
            {
                "reference_year": year,
                "evaluation_cycle": cycle,
                "file_name": name,
                "path": rel(path),
                "sha256": sha256_file(path),
                "role": "pipeline_source",
            }
        )
    verification_files: list[dict[str, Any]] = []
    for path in sorted(STAFF_PER_STUDENT_VERIFICATION_RAW_DIR.glob("*.xlsx")):
        verification_files.append(
            {
                "file_name": path.name,
                "path": rel(path),
                "sha256": sha256_file(path),
                "role": "official_download_crosscheck",
            }
        )

    payload = {
        "dataset_id": STAFF_PER_STUDENT_DATASET_ID,
        "source_dataset_id": DATASET_ID,
        "source_name": "한국대학평가원 대학통계",
        "source_org": "한국대학교육협의회 병설 한국대학평가원",
        "source_url": "https://aims.kcue.or.kr/EgovPageLink.do?subMenu=5020000",
        "download_method": "KCUE 대학통계 UI에서 주기/연도 선택, 대학명 모두 선택, [3.5] 직원 1인당 학생수 선택, 조회 후 데이터 다운로드",
        "download_purpose": "데이터 분석",
        "processed_at": processed_at,
        "raw_input_directory": rel(RAW_DIR),
        "verification_input_directory": rel(STAFF_PER_STUDENT_VERIFICATION_RAW_DIR),
        "raw_files": raw_files + verification_files,
        "pipeline_raw_files": raw_files,
        "verification_files": verification_files,
        "privacy_note": "로그인 정보, 사용자 이메일, 다운로드 팝업 입력값은 저장하지 않음",
    }
    STAFF_PER_STUDENT_SOURCE_ACQUISITION.parent.mkdir(parents=True, exist_ok=True)
    STAFF_PER_STUDENT_SOURCE_ACQUISITION.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_staff_per_student_outputs(
    long: pd.DataFrame,
    *,
    processed_at: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    staff_source = long[long["metric_id"].astype(str).str.strip() == "students_per_staff"].copy()
    staff_candidate = prepare_staff_per_student_frame(long)
    current_long = pd.read_csv(CURRENT_LONG)
    staff_current = prepare_staff_per_student_frame(current_long)
    staff_mismatches = compare_staff_per_student_candidate(staff_candidate, staff_current)
    download_crosscheck, download_crosscheck_summary = build_staff_per_student_download_crosscheck(long)
    files = sorted(RAW_DIR.glob("*.xlsx"))
    raw_preserved = all(path.exists() for path in files) and bool(files)

    report = {
        "dataset_id": STAFF_PER_STUDENT_DATASET_ID,
        "source_dataset_id": DATASET_ID,
        "version": VERSION,
        "processed_at": processed_at,
        "source_name": "한국대학평가원 대학통계",
        "source_url": "https://aims.kcue.or.kr/EgovPageLink.do?subMenu=5020000",
        "source_preservation_status": "raw_preserved" if raw_preserved else "raw_missing",
        "source_input_kind": "raw_xlsx",
        "raw_input_directory": rel(RAW_DIR),
        "raw_file_count": len(files),
        "candidate_outputs": {
            "candidate": rel(STAFF_PER_STUDENT_CANDIDATE),
            "processing_report": rel(STAFF_PER_STUDENT_PROCESSING_REPORT),
            "mismatch_report": rel(STAFF_PER_STUDENT_MISMATCH_REPORT),
            "download_crosscheck_report": rel(STAFF_PER_STUDENT_DOWNLOAD_CROSSCHECK_REPORT),
            "source_metadata": rel(STAFF_PER_STUDENT_SOURCE_ACQUISITION),
        },
        "current_assets_compared": {
            "long": rel(CURRENT_LONG),
        },
        "row_counts": {
            "source_input_rows": int(len(staff_source)),
            "source_metric_rows": int(len(staff_source)),
            "candidate_rows": int(len(staff_candidate)),
            "current_rows": int(len(staff_current)),
            "mismatch_rows": int(len(staff_mismatches)),
        },
        "year_counts": {
            str(year): int(count)
            for year, count in staff_source.groupby("reference_year")["university_name"].count().items()
        },
        "candidate_scope": "서울 소재 사립 일반대학 화면 표시 범위",
        "formula": "직원 1인당 학생수 = 재학생수 / 직원수",
        "value_policy": "재계산지표값을 우선 사용하고, 재계산값이 없으면 통합지표값을 사용합니다.",
        "mismatch_summary": {
            "total": int(len(staff_mismatches)),
            "high": int((staff_mismatches["severity"] == "high").sum()) if not staff_mismatches.empty else 0,
            "medium": int((staff_mismatches["severity"] == "medium").sum()) if not staff_mismatches.empty else 0,
        },
        "official_download_crosscheck": download_crosscheck_summary,
        "known_limitations": [
            "KCUE XLSX 파일에는 안정적인 학교코드가 없어 학교명 기준으로 검증합니다.",
            "Candidate CSV는 운영 반영용이 아니라 데이터 검증 화면용 산출물입니다.",
            "원자료 다운로드는 KCUE 대학통계 UI에서 수동으로 수행하고, 이 변환기는 보존된 XLSX를 읽기 전용으로 처리합니다.",
        ],
    }
    return staff_candidate, staff_mismatches, download_crosscheck, report


def build_candidate() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    wide = builder.build_wide(PROJECT_ROOT)
    long = builder.build_long(wide)

    current_wide = pd.read_csv(CURRENT_WIDE)
    current_long = pd.read_csv(CURRENT_LONG)
    wide_mismatches = compare_frames(wide, current_wide, ["reference_year", "university_name"], "wide")
    long_mismatches = compare_frames(
        long,
        current_long,
        ["metric_id", "reference_year", "university_name"],
        "long",
    )
    mismatches = pd.concat([wide_mismatches, long_mismatches], ignore_index=True)

    files = sorted(RAW_DIR.glob("*.xlsx"))
    now = datetime.now(timezone.utc).isoformat()
    report = {
        "dataset_id": DATASET_ID,
        "version": VERSION,
        "processed_at": now,
        "raw_input_directory": rel(RAW_DIR),
        "raw_file_count": len(files),
        "candidate_outputs": {
            "wide": rel(CANDIDATE_WIDE),
            "long": rel(CANDIDATE_LONG),
            "staff_per_student": rel(STAFF_PER_STUDENT_CANDIDATE),
            "source_metadata": rel(SOURCE_METADATA),
            "candidate_metadata": rel(CANDIDATE_METADATA),
            "processing_report": rel(PROCESSING_REPORT),
            "mismatch_report": rel(MISMATCH_REPORT),
            "staff_per_student_processing_report": rel(STAFF_PER_STUDENT_PROCESSING_REPORT),
            "staff_per_student_mismatch_report": rel(STAFF_PER_STUDENT_MISMATCH_REPORT),
            "staff_per_student_download_crosscheck_report": rel(STAFF_PER_STUDENT_DOWNLOAD_CROSSCHECK_REPORT),
        },
        "current_assets_compared": {
            "wide": rel(CURRENT_WIDE),
            "long": rel(CURRENT_LONG),
        },
        "row_counts": {
            "wide_candidate": int(len(wide)),
            "long_candidate": int(len(long)),
            "wide_current": int(len(current_wide)),
            "long_current": int(len(current_long)),
        },
        "year_counts": {
            str(year): int(count)
            for year, count in wide.groupby("reference_year")["university_name"].count().items()
        },
        "metric_counts": {
            metric: int(count)
            for metric, count in long.groupby("metric_id")["university_name"].count().items()
        },
        "coverage": {
            "comparison_11": coverage_for(wide, COMPARISON_SCHOOLS),
            "risk_schools": coverage_for(wide, RISK_SCHOOLS),
            "outlier_schools": coverage_for(wide, OUTLIER_SCHOOLS),
        },
        "source_value_only_4th_cycle": source_value_only_report(long),
        "formula_validation": builder.summarize_validation(wide),
        "mismatch_summary": {
            "total": int(len(mismatches)),
            "high": int((mismatches["severity"] == "high").sum()) if not mismatches.empty else 0,
        },
        "known_limitations": [
            "Candidate outputs are review-only and are not promoted to data/processed/current assets by this converter.",
            "KCUE XLSX files do not include stable school IDs; coverage is school-name based.",
            "No official-site re-download was performed; this run verifies local raw XLSX files against existing processed outputs.",
        ],
    }
    return wide, long, mismatches, report


def write_metadata(report: dict[str, Any]) -> None:
    raw_files = []
    for path in sorted(RAW_DIR.glob("*.xlsx")):
        year, cycle, name = builder.parse_file_info(path)
        raw_files.append(
            {
                "reference_year": year,
                "evaluation_cycle": cycle,
                "file_name": name,
                "path": rel(path),
                "sha256": sha256_file(path),
            }
        )

    source_payload = {
        "dataset_id": DATASET_ID,
        "dataset_name_ko": "한국대학평가원 대학현황지표",
        "source_name": "한국대학평가원 대학통계",
        "source_org": "한국대학교육협의회 병설 한국대학평가원",
        "source_url": "https://aims.kcue.or.kr/EgovPageLink.do?subMenu=5020000",
        "download_method": "사용자 수동 다운로드; converter does not crawl/download",
        "raw_input_directory": rel(RAW_DIR),
        "sheet_name": builder.SHEET_NAME,
        "processed_at": report["processed_at"],
        "raw_files": raw_files,
    }
    candidate_payload = {
        "dataset_key": DATASET_ID,
        "version": VERSION,
        "title": "KCUE university indicators candidate conversion",
        "candidate_assets": {
            "wide": rel(CANDIDATE_WIDE),
            "long": rel(CANDIDATE_LONG),
            "staff_per_student": rel(STAFF_PER_STUDENT_CANDIDATE),
        },
        "verification_status": "candidate_verified_against_current" if report["mismatch_summary"]["total"] == 0 else "candidate_mismatch_found",
        "promotion_policy": "Do not promote automatically; current assets remain untouched until explicit approval.",
        "metadata_files": {
            "source": rel(SOURCE_METADATA),
            "processing_report": rel(PROCESSING_REPORT),
            "mismatch_report": rel(MISMATCH_REPORT),
            "staff_per_student_processing_report": rel(STAFF_PER_STUDENT_PROCESSING_REPORT),
            "staff_per_student_mismatch_report": rel(STAFF_PER_STUDENT_MISMATCH_REPORT),
            "staff_per_student_download_crosscheck_report": rel(STAFF_PER_STUDENT_DOWNLOAD_CROSSCHECK_REPORT),
        },
        "quality_flags": [
            "raw_read_only",
            "candidate_output_only",
            "processed_assets_not_modified",
            "compared_to_current_wide_long",
        ],
        "source_value_only_4th_cycle": report["source_value_only_4th_cycle"],
    }
    SOURCE_METADATA.write_text(json.dumps(source_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CANDIDATE_METADATA.write_text(json.dumps(candidate_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_outputs() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATION_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    MISMATCH_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    wide, long, mismatches, report = build_candidate()
    staff_candidate, staff_mismatches, download_crosscheck, staff_report = build_staff_per_student_outputs(
        long,
        processed_at=report["processed_at"],
    )
    wide.to_csv(CANDIDATE_WIDE, index=False, encoding="utf-8-sig")
    long.to_csv(CANDIDATE_LONG, index=False, encoding="utf-8-sig")
    mismatches.to_csv(MISMATCH_REPORT, index=False, encoding="utf-8-sig")
    staff_candidate.to_csv(STAFF_PER_STUDENT_CANDIDATE, index=False, encoding="utf-8-sig")
    staff_mismatches.to_csv(STAFF_PER_STUDENT_MISMATCH_REPORT, index=False, encoding="utf-8-sig")
    download_crosscheck.to_csv(STAFF_PER_STUDENT_DOWNLOAD_CROSSCHECK_REPORT, index=False, encoding="utf-8-sig")
    PROCESSING_REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    STAFF_PER_STUDENT_PROCESSING_REPORT.write_text(
        json.dumps(staff_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_staff_per_student_source_acquisition(report["processed_at"])
    write_metadata(report)
    return report


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT, help="Accepted for interface consistency; must be project root.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.project_root.resolve() != PROJECT_ROOT.resolve():
        raise SystemExit(f"This wrapper is bound to {PROJECT_ROOT}; got {args.project_root}")
    report = write_outputs()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
