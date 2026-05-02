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

DATASET_ID = "kcue_university_indicators"
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
            "source_metadata": rel(SOURCE_METADATA),
            "candidate_metadata": rel(CANDIDATE_METADATA),
            "processing_report": rel(PROCESSING_REPORT),
            "mismatch_report": rel(MISMATCH_REPORT),
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
        },
        "verification_status": "candidate_verified_against_current" if report["mismatch_summary"]["total"] == 0 else "candidate_mismatch_found",
        "promotion_policy": "Do not promote automatically; current assets remain untouched until explicit approval.",
        "metadata_files": {
            "source": rel(SOURCE_METADATA),
            "processing_report": rel(PROCESSING_REPORT),
            "mismatch_report": rel(MISMATCH_REPORT),
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
    wide.to_csv(CANDIDATE_WIDE, index=False, encoding="utf-8-sig")
    long.to_csv(CANDIDATE_LONG, index=False, encoding="utf-8-sig")
    mismatches.to_csv(MISMATCH_REPORT, index=False, encoding="utf-8-sig")
    PROCESSING_REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
