"""Build a graduate career-outcome candidate asset from raw AcademyInfo XLSX.

The converter keeps the current dashboard CSV untouched. It preserves the
AcademyInfo 공시데이터 추이 school-level XLSX as the source of truth, rebuilds a
national candidate frame, validates the published employment-rate formula, and
checks that the existing dashboard rows still match the raw source.
"""

from __future__ import annotations

import argparse
import json
import warnings
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Sequence

import pandas as pd

from utils.data_pipeline import prepare_jirosung_frame

from scripts.converters.academyinfo_common import (
    PROJECT_ROOT,
    AcademyInfoDatasetConfig,
    combine_mismatch_frames,
    mismatch_frame,
    write_candidate_outputs,
)

DATASET_ID = "jirosung"
RAW_XLSX = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "academyinfo"
    / DATASET_ID
    / "original"
    / "5-다. 졸업생의 취업 현황_대학_졸업생 취업률.xlsx"
)
CURRENT_ASSET = PROJECT_ROOT / "data" / "졸업생_취업률.csv"
GRADUATE_COUNT_COL = "졸업자"
EMPLOYED_COUNT_COL = "취업자"
ADVANCED_COUNT_COL = "진학자"
MILITARY_COUNT_COL = "입대자"
UNEMPLOYABLE_COUNT_COL = "취업불가능자"
FOREIGN_STUDENT_COL = "외국인유학생"
HEALTH_INSURANCE_EXCLUDED_COL = "건강보험직장가입제외대상"
EMPLOYMENT_RATE_COL = "취업률(%)"
CAREER_OUTCOME_COL = "졸업생_진로_성과"
EXPECTED_COLUMNS = (
    "공시연도",
    "대표학교코드",
    "학교코드",
    "학교명",
    "본분교명",
    "대학구분",
    "학교종류",
    "설립유형",
    "설립구분",
    "소재지유형",
    "지역명",
    "학교상태",
    "기준년도",
    "입학정원(학부)",
    "재학생수(학부)",
    "전임교원수(학부+대학원)",
    GRADUATE_COUNT_COL,
    EMPLOYED_COUNT_COL,
    ADVANCED_COUNT_COL,
    MILITARY_COUNT_COL,
    UNEMPLOYABLE_COUNT_COL,
    FOREIGN_STUDENT_COL,
    HEALTH_INSURANCE_EXCLUDED_COL,
    EMPLOYMENT_RATE_COL,
)
NUMERIC_COLUMNS = (
    "공시연도",
    "기준년도",
    "입학정원(학부)",
    "재학생수(학부)",
    "전임교원수(학부+대학원)",
    GRADUATE_COUNT_COL,
    EMPLOYED_COUNT_COL,
    ADVANCED_COUNT_COL,
    MILITARY_COUNT_COL,
    UNEMPLOYABLE_COUNT_COL,
    FOREIGN_STUDENT_COL,
    HEALTH_INSURANCE_EXCLUDED_COL,
    EMPLOYMENT_RATE_COL,
)

CONFIG = AcademyInfoDatasetConfig(
    dataset_id=DATASET_ID,
    dataset_name_ko="졸업생 진로 성과",
    source_section="공시 데이터 다운로드 > 공시데이터 추이 > 5-다. 졸업생의 취업 현황_대학",
    source_processed_path=CURRENT_ASSET,
    expected_raw_files=(RAW_XLSX,),
    source_metadata_path=PROJECT_ROOT / "data" / "metadata" / "jirosung_v1.source.json",
    candidate_filename="jirosung_2008_2024_candidate.csv",
    transform=prepare_jirosung_frame,
    source_input_path=RAW_XLSX,
    source_input_kind="raw_xlsx",
    version="academyinfo_jirosung_raw_xlsx_candidate_v1",
    input_loader=lambda config: load_jirosung_raw_xlsx(config.source_input_path or RAW_XLSX),
    mismatch_builder=lambda source_frame, candidate, config: build_jirosung_mismatches(
        source_frame,
        candidate,
        source_path=config.source_input_path or RAW_XLSX,
        current_asset_path=config.source_processed_path,
    ),
)


def _clean_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", "", regex=False).str.strip(), errors="coerce")


def _decimal_or_none(value: object) -> Decimal | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).replace(",", "").strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def _career_denominator(row: pd.Series) -> Decimal | None:
    graduate = _decimal_or_none(row.get(GRADUATE_COUNT_COL))
    military = _decimal_or_none(row.get(MILITARY_COUNT_COL))
    unemployable = _decimal_or_none(row.get(UNEMPLOYABLE_COUNT_COL))
    foreign_student = _decimal_or_none(row.get(FOREIGN_STUDENT_COL))
    insurance_excluded = _decimal_or_none(row.get(HEALTH_INSURANCE_EXCLUDED_COL))
    parts = (graduate, military, unemployable, foreign_student, insurance_excluded)
    if any(value is None for value in parts):
        return None
    return graduate - military - unemployable - foreign_student - insurance_excluded


def _employment_denominator(row: pd.Series) -> Decimal | None:
    career_denominator = _career_denominator(row)
    advanced = _decimal_or_none(row.get(ADVANCED_COUNT_COL))
    if career_denominator is None or advanced is None:
        return None
    return career_denominator - advanced


def _employment_rate_half_up(row: pd.Series) -> float | None:
    employed = _decimal_or_none(row.get(EMPLOYED_COUNT_COL))
    denominator = _employment_denominator(row)
    if employed is None or denominator is None:
        return None
    if denominator == 0:
        return 0.0 if employed == 0 else None
    return float((employed / denominator * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def load_jirosung_raw_xlsx(path: Path = RAW_XLSX) -> pd.DataFrame:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Workbook contains no default style")
        raw = pd.read_excel(path, dtype=str, engine="openpyxl")
    missing = sorted(set(EXPECTED_COLUMNS) - set(raw.columns))
    if missing:
        raise ValueError(f"Missing expected AcademyInfo jirosung columns: {missing}")

    frame = raw.loc[:, list(EXPECTED_COLUMNS)].copy()
    for column in frame.columns:
        if column not in NUMERIC_COLUMNS:
            frame[column] = frame[column].astype(str).str.strip()
    for column in NUMERIC_COLUMNS:
        frame[column] = _clean_numeric(frame[column])
    return frame


def build_jirosung_formula_mismatches(source_frame: pd.DataFrame, *, source_path: Path) -> pd.DataFrame:
    rows = []
    source_relpath = str(source_path.relative_to(PROJECT_ROOT))
    for _, row in source_frame.iterrows():
        calculated = _employment_rate_half_up(row)
        source_value = _decimal_or_none(row.get(EMPLOYMENT_RATE_COL))
        if calculated is None or source_value is None:
            continue
        if abs(calculated - float(source_value)) <= 0.000001:
            continue
        year = row.get("기준년도")
        rows.append(
            {
                "severity": "high",
                "field": EMPLOYMENT_RATE_COL,
                "school_name": row.get("학교명"),
                "year": int(year) if pd.notna(year) else None,
                "processed_value": calculated,
                "raw_value": float(source_value),
                "reason": "취업률(%) does not match 취업자 / 진학자 제외 취업률 분모 * 100 rounded half-up to 1 decimal.",
                "source_path": source_relpath,
            }
        )
    return mismatch_frame(rows)


def build_jirosung_current_asset_mismatches(
    candidate: pd.DataFrame,
    *,
    current_asset_path: Path,
) -> pd.DataFrame:
    current_source = pd.read_csv(current_asset_path, encoding="utf-8-sig", dtype=str)
    current = prepare_jirosung_frame(current_source)
    key = ["기준년도", "학교명", "본분교명"]
    current = _with_duplicate_ordinal(current, key=key, value_col=CAREER_OUTCOME_COL)
    candidate = _with_duplicate_ordinal(candidate, key=key, value_col=CAREER_OUTCOME_COL)
    merged = current.merge(
        candidate,
        on=[*key, "_row_ordinal"],
        how="left",
        suffixes=("_current", "_candidate"),
        indicator=True,
    )

    rows = []
    source_relpath = str(current_asset_path.relative_to(PROJECT_ROOT))
    for _, row in merged.iterrows():
        year = row.get("기준년도")
        if row["_merge"] == "left_only":
            rows.append(
                {
                    "severity": "medium",
                    "field": "row_presence",
                    "school_name": row.get("학교명"),
                    "year": int(year) if pd.notna(year) else None,
                    "processed_value": "current_only",
                    "raw_value": None,
                    "reason": "Current dashboard row was not found in the raw-XLSX candidate.",
                    "source_path": source_relpath,
                }
            )
            continue

        current_value = pd.to_numeric(row.get(f"{CAREER_OUTCOME_COL}_current"), errors="coerce")
        candidate_value = pd.to_numeric(row.get(f"{CAREER_OUTCOME_COL}_candidate"), errors="coerce")
        if pd.isna(current_value) and pd.isna(candidate_value):
            continue
        if pd.isna(current_value) != pd.isna(candidate_value) or abs(current_value - candidate_value) > 0.000001:
            rows.append(
                {
                    "severity": "medium",
                    "field": CAREER_OUTCOME_COL,
                    "school_name": row.get("학교명"),
                    "year": int(year) if pd.notna(year) else None,
                    "processed_value": current_value if pd.notna(current_value) else None,
                    "raw_value": candidate_value if pd.notna(candidate_value) else None,
                    "reason": "Current dashboard asset value differs from raw-XLSX candidate value.",
                    "source_path": source_relpath,
                }
            )
    return mismatch_frame(rows)


def _with_duplicate_ordinal(frame: pd.DataFrame, *, key: list[str], value_col: str) -> pd.DataFrame:
    result = frame.copy()
    result[value_col] = pd.to_numeric(result[value_col], errors="coerce")
    result = result.sort_values([*key, value_col], kind="mergesort").reset_index(drop=True)
    result["_row_ordinal"] = result.groupby(key, dropna=False).cumcount()
    return result


def build_jirosung_mismatches(
    source_frame: pd.DataFrame,
    candidate: pd.DataFrame,
    *,
    source_path: Path,
    current_asset_path: Path,
) -> pd.DataFrame:
    return combine_mismatch_frames(
        [
            build_jirosung_formula_mismatches(source_frame, source_path=source_path),
            build_jirosung_current_asset_mismatches(candidate, current_asset_path=current_asset_path),
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
