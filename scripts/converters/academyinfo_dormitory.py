"""Build a candidate dormitory-accommodation asset from raw AcademyInfo XLSX.

The converter preserves current dashboard assets and writes only candidate,
metadata, processing-report, and mismatch-report artifacts.  It reads the raw
AcademyInfo 공시데이터 추이 XLSX captured under data/raw, maps Korean source
columns to the project's standard dormitory schema, validates the published
rate formula, then reuses the dashboard loader transform for the default
analysis scope.
"""

from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path
from typing import Sequence

import pandas as pd

from utils.data_pipeline import prepare_dormitory_frame

from scripts.converters.academyinfo_common import (
    PROJECT_ROOT,
    AcademyInfoDatasetConfig,
    combine_mismatch_frames,
    mismatch_frame,
    write_candidate_outputs,
)

DATASET_ID = "dormitory_accommodation_status"
RAW_XLSX = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "academyinfo"
    / DATASET_ID
    / "original"
    / "14-마-1. 기숙사 수용 현황_대학_기숙사 수용률.xlsx"
)
RAW_COLUMN_MAP = {
    "공시연도": "disclosure_year",
    "대표학교코드": "representative_school_code",
    "학교코드": "school_code",
    "학교명": "university_name",
    "본분교명": "campus_type",
    "대학구분": "college_type",
    "학교종류": "school_type",
    "설립유형": "founding_type",
    "설립구분": "founding_type_detail",
    "소재지유형": "location_type",
    "지역명": "region_name",
    "학교상태": "school_status",
    "기준년도": "reference_year",
    "재학생수": "enrolled_students",
    "총실수": "total_room_count",
    "수용가능인원": "dormitory_capacity",
    "기숙사지원자수": "dormitory_applicants",
    "입사경쟁률": "dormitory_competition_rate",
    "기숙사수용률": "dormitory_accommodation_rate_pct",
    "입학정원(학부)": "입학정원_학부",
    "졸업생수(학부)": "졸업생수_학부",
    "전임교원수(학부+대학원)": "전임교원수_학부_대학원",
}
STANDARD_COLUMNS = (
    "disclosure_year",
    "reference_year",
    "representative_school_code",
    "school_code",
    "university_name",
    "campus_type",
    "college_type",
    "school_type",
    "founding_type",
    "founding_type_detail",
    "location_type",
    "region_name",
    "school_status",
    "enrolled_students",
    "total_room_count",
    "dormitory_capacity",
    "dormitory_applicants",
    "dormitory_competition_rate",
    "dormitory_accommodation_rate_pct",
    "입학정원_학부",
    "졸업생수_학부",
    "전임교원수_학부_대학원",
)
NUMERIC_COLUMNS = (
    "disclosure_year",
    "reference_year",
    "enrolled_students",
    "total_room_count",
    "dormitory_capacity",
    "dormitory_applicants",
    "dormitory_competition_rate",
    "dormitory_accommodation_rate_pct",
    "입학정원_학부",
    "졸업생수_학부",
    "전임교원수_학부_대학원",
)
CONFIG = AcademyInfoDatasetConfig(
    dataset_id=DATASET_ID,
    dataset_name_ko="기숙사 수용 현황",
    source_section="공시 데이터 다운로드 > 공시데이터 추이 > 14-마-1. 기숙사 수용 현황_대학",
    source_processed_path=(
        PROJECT_ROOT
        / "data"
        / "processed"
        / DATASET_ID
        / "dormitory_accommodation_status_v2_utf8.csv"
    ),
    expected_raw_files=(
        RAW_XLSX,
    ),
    source_metadata_path=PROJECT_ROOT / "data" / "metadata" / "dormitory_accommodation_status_v2.source.json",
    candidate_filename="dormitory_accommodation_status_2025_candidate.csv",
    transform=prepare_dormitory_frame,
    source_input_path=RAW_XLSX,
    source_input_kind="raw_xlsx",
    version="academyinfo_dormitory_raw_xlsx_candidate_v1",
    input_loader=lambda config: load_dormitory_raw_xlsx(config.source_input_path or RAW_XLSX),
    mismatch_builder=lambda source_frame, candidate, config: build_dormitory_mismatches(
        source_frame,
        candidate,
        source_path=config.source_input_path or RAW_XLSX,
        current_processed_path=config.source_processed_path,
    ),
)


def _clean_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", "", regex=False).str.strip(), errors="coerce")


def load_dormitory_raw_xlsx(path: Path = RAW_XLSX) -> pd.DataFrame:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Workbook contains no default style")
        raw = pd.read_excel(path, dtype=str)
    missing = sorted(set(RAW_COLUMN_MAP) - set(raw.columns))
    if missing:
        raise ValueError(f"Missing expected AcademyInfo dormitory columns: {missing}")

    frame = raw.rename(columns=RAW_COLUMN_MAP).loc[:, list(STANDARD_COLUMNS)].copy()
    for column in frame.columns:
        if column not in NUMERIC_COLUMNS:
            frame[column] = frame[column].astype(str).str.strip()
    for column in NUMERIC_COLUMNS:
        frame[column] = _clean_numeric(frame[column])
    return frame


def build_dormitory_formula_mismatches(source_frame: pd.DataFrame, *, source_path: Path) -> pd.DataFrame:
    frame = source_frame.copy()
    denominator = pd.to_numeric(frame["enrolled_students"], errors="coerce")
    numerator = pd.to_numeric(frame["dormitory_capacity"], errors="coerce")
    source_rate = pd.to_numeric(frame["dormitory_accommodation_rate_pct"], errors="coerce")
    calculated = (numerator / denominator * 100).round(1)

    zero_denominator_bad = denominator.fillna(0).eq(0) & source_rate.fillna(0).ne(0)
    comparable = denominator.gt(0) & numerator.notna() & source_rate.notna()
    rate_mismatch = comparable & (calculated - source_rate).abs().gt(0.05)
    invalid = zero_denominator_bad | rate_mismatch

    rows = []
    source_relpath = str(source_path.relative_to(PROJECT_ROOT))
    for _, row in frame.loc[invalid].iterrows():
        year = row.get("reference_year")
        rows.append(
            {
                "severity": "high",
                "field": "dormitory_accommodation_rate_pct",
                "school_name": row.get("university_name"),
                "year": int(year) if pd.notna(year) else None,
                "processed_value": calculated.loc[row.name] if row.name in calculated.index else None,
                "raw_value": row.get("dormitory_accommodation_rate_pct"),
                "reason": "Dormitory accommodation rate does not match capacity / enrolled_students * 100 rounded to 1 decimal.",
                "source_path": source_relpath,
            }
        )
    return mismatch_frame(rows)


def build_dormitory_current_asset_mismatches(
    candidate: pd.DataFrame,
    *,
    current_processed_path: Path,
) -> pd.DataFrame:
    current_source = pd.read_csv(current_processed_path, encoding="utf-8-sig", dtype=str)
    current = prepare_dormitory_frame(current_source)
    key = ["기준년도", "학교명"]
    merged = current.merge(candidate, on=key, how="outer", suffixes=("_current", "_candidate"), indicator=True)

    rows = []
    comparable_columns = (
        "재학생수",
        "기숙사실수",
        "기숙사수용인원",
        "기숙사지원자수",
        "기숙사경쟁률",
        "기숙사수용률",
    )
    source_relpath = str(current_processed_path.relative_to(PROJECT_ROOT))
    for _, row in merged.iterrows():
        if row["_merge"] != "both":
            rows.append(
                {
                    "severity": "medium",
                    "field": "row_presence",
                    "school_name": row.get("학교명"),
                    "year": int(row["기준년도"]) if pd.notna(row.get("기준년도")) else None,
                    "processed_value": row["_merge"],
                    "raw_value": None,
                    "reason": "Current dashboard asset and raw-XLSX candidate have different row presence.",
                    "source_path": source_relpath,
                }
            )
            continue

        for column in comparable_columns:
            current_value = pd.to_numeric(row.get(f"{column}_current"), errors="coerce")
            candidate_value = pd.to_numeric(row.get(f"{column}_candidate"), errors="coerce")
            if pd.isna(current_value) and pd.isna(candidate_value):
                continue
            if pd.isna(current_value) != pd.isna(candidate_value) or abs(current_value - candidate_value) > 0.000001:
                rows.append(
                    {
                        "severity": "medium",
                        "field": column,
                        "school_name": row.get("학교명"),
                        "year": int(row["기준년도"]) if pd.notna(row.get("기준년도")) else None,
                        "processed_value": current_value if pd.notna(current_value) else None,
                        "raw_value": candidate_value if pd.notna(candidate_value) else None,
                        "reason": "Current dashboard asset value differs from raw-XLSX candidate value.",
                        "source_path": source_relpath,
                    }
                )
    return mismatch_frame(rows)


def build_dormitory_mismatches(
    source_frame: pd.DataFrame,
    candidate: pd.DataFrame,
    *,
    source_path: Path,
    current_processed_path: Path,
) -> pd.DataFrame:
    return combine_mismatch_frames(
        [
            build_dormitory_formula_mismatches(source_frame, source_path=source_path),
            build_dormitory_current_asset_mismatches(candidate, current_processed_path=current_processed_path),
        ]
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--print-report", action="store_true", help="Print generated report JSON")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    report = write_candidate_outputs(CONFIG)
    if args.print_report:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(report["output_file"])
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
