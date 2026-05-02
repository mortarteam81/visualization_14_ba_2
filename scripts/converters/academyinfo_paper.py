"""Build a paper-performance candidate asset from raw AcademyInfo XLSX.

The converter keeps the current dashboard CSV untouched.  It preserves the
AcademyInfo 공시데이터 추이 school-level XLSX as the source of truth, rebuilds a
national candidate frame, validates the published per-faculty formulas, and
checks that the existing Seoul-scope dashboard rows still match the raw source.
"""

from __future__ import annotations

import argparse
import json
import warnings
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Sequence

import pandas as pd

from utils.data_pipeline import prepare_paper_frame

from scripts.converters.academyinfo_common import (
    PROJECT_ROOT,
    AcademyInfoDatasetConfig,
    combine_mismatch_frames,
    mismatch_frame,
    write_candidate_outputs,
)

DATASET_ID = "paper"
RAW_XLSX = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "academyinfo"
    / DATASET_ID
    / "original"
    / "7-가. 전임교원의 연구실적_대학_전임교원 1인당 논문 실적(국내, 국제).xlsx"
)
CURRENT_ASSET = PROJECT_ROOT / "data" / "전임교원 논문실적.csv"
FULLTIME_FACULTY_COL = "전임\n교원"
PAPER_DOMESTIC_COL = "전임교원1인당논문실적(국내, 연구재단등재지(후보포함))"
PAPER_SCI_COL = "전임교원1인당논문실적(국제, SCI급/SCOPUS학술지)"
DOMESTIC_NUMERATOR_COL = "논문실적(국내, 연구재단등재지(후보포함))"
SCI_NUMERATOR_COL = "논문실적(국제, SCI급/SCOPUS학술지)"
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
    "졸업생수(학부)",
    FULLTIME_FACULTY_COL,
    "논문실적 총계",
    "논문실적(국내)",
    DOMESTIC_NUMERATOR_COL,
    "논문실적(기타국내발간일반학술지)",
    "논문실적(국제)",
    SCI_NUMERATOR_COL,
    "논문실적(국제, 기타국제발간일반학술지)",
    "전임교원1인당논문실적(국내)",
    "전임교원1인당논문실적(국제)",
    PAPER_DOMESTIC_COL,
    PAPER_SCI_COL,
)
NUMERIC_COLUMNS = (
    "공시연도",
    "기준년도",
    "입학정원(학부)",
    "재학생수(학부)",
    "졸업생수(학부)",
    FULLTIME_FACULTY_COL,
    "논문실적 총계",
    "논문실적(국내)",
    DOMESTIC_NUMERATOR_COL,
    "논문실적(기타국내발간일반학술지)",
    "논문실적(국제)",
    SCI_NUMERATOR_COL,
    "논문실적(국제, 기타국제발간일반학술지)",
    "전임교원1인당논문실적(국내)",
    "전임교원1인당논문실적(국제)",
    PAPER_DOMESTIC_COL,
    PAPER_SCI_COL,
)
METRIC_COLUMNS = (
    PAPER_DOMESTIC_COL,
    PAPER_SCI_COL,
)
FORMULA_SPECS = (
    (DOMESTIC_NUMERATOR_COL, PAPER_DOMESTIC_COL),
    (SCI_NUMERATOR_COL, PAPER_SCI_COL),
)

CONFIG = AcademyInfoDatasetConfig(
    dataset_id=DATASET_ID,
    dataset_name_ko="전임교원 1인당 논문실적",
    source_section="공시 데이터 다운로드 > 공시데이터 추이 > 7-가. 전임교원의 연구실적_대학",
    source_processed_path=CURRENT_ASSET,
    expected_raw_files=(RAW_XLSX,),
    source_metadata_path=PROJECT_ROOT / "data" / "metadata" / "paper_v1.source.json",
    candidate_filename="paper_2007_2024_candidate.csv",
    transform=prepare_paper_frame,
    source_input_path=RAW_XLSX,
    source_input_kind="raw_xlsx",
    version="academyinfo_paper_raw_xlsx_candidate_v1",
    input_loader=lambda config: load_paper_raw_xlsx(config.source_input_path or RAW_XLSX),
    mismatch_builder=lambda source_frame, candidate, config: build_paper_mismatches(
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


def _ratio_half_up(numerator: object, denominator: object) -> float | None:
    n_value = _decimal_or_none(numerator)
    d_value = _decimal_or_none(denominator)
    if n_value is None or d_value is None:
        return None
    if d_value == 0:
        return 0.0 if n_value == 0 else None
    return float((n_value / d_value).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))


def load_paper_raw_xlsx(path: Path = RAW_XLSX) -> pd.DataFrame:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Workbook contains no default style")
        raw = pd.read_excel(path, dtype=str, engine="openpyxl")
    missing = sorted(set(EXPECTED_COLUMNS) - set(raw.columns))
    if missing:
        raise ValueError(f"Missing expected AcademyInfo paper columns: {missing}")

    frame = raw.loc[:, list(EXPECTED_COLUMNS)].copy()
    for column in frame.columns:
        if column not in NUMERIC_COLUMNS:
            frame[column] = frame[column].astype(str).str.strip()
    for column in NUMERIC_COLUMNS:
        frame[column] = _clean_numeric(frame[column])
    return frame


def build_paper_formula_mismatches(source_frame: pd.DataFrame, *, source_path: Path) -> pd.DataFrame:
    rows = []
    source_relpath = str(source_path.relative_to(PROJECT_ROOT))
    for _, row in source_frame.iterrows():
        for numerator_col, value_col in FORMULA_SPECS:
            calculated = _ratio_half_up(row.get(numerator_col), row.get(FULLTIME_FACULTY_COL))
            source_value = _decimal_or_none(row.get(value_col))
            if calculated is None or source_value is None:
                continue
            if abs(calculated - float(source_value)) <= 0.00005:
                continue
            year = row.get("기준년도")
            rows.append(
                {
                    "severity": "high",
                    "field": value_col,
                    "school_name": row.get("학교명"),
                    "year": int(year) if pd.notna(year) else None,
                    "processed_value": calculated,
                    "raw_value": float(source_value),
                    "reason": f"{value_col} does not match numerator / 전임교원 rounded half-up to 4 decimals.",
                    "source_path": source_relpath,
                }
            )
    return mismatch_frame(rows)


def build_paper_current_asset_mismatches(
    candidate: pd.DataFrame,
    *,
    current_asset_path: Path,
) -> pd.DataFrame:
    current_source = pd.read_csv(current_asset_path, encoding="cp949", dtype=str)
    current = prepare_paper_frame(current_source)
    key = ["기준년도", "학교명"]
    merged = current.merge(candidate, on=key, how="left", suffixes=("_current", "_candidate"), indicator=True)

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

        for column in METRIC_COLUMNS:
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
                        "year": int(year) if pd.notna(year) else None,
                        "processed_value": current_value if pd.notna(current_value) else None,
                        "raw_value": candidate_value if pd.notna(candidate_value) else None,
                        "reason": "Current dashboard asset value differs from raw-XLSX candidate value.",
                        "source_path": source_relpath,
                    }
                )
    return mismatch_frame(rows)


def build_paper_mismatches(
    source_frame: pd.DataFrame,
    candidate: pd.DataFrame,
    *,
    source_path: Path,
    current_asset_path: Path,
) -> pd.DataFrame:
    return combine_mismatch_frames(
        [
            build_paper_formula_mismatches(source_frame, source_path=source_path),
            build_paper_current_asset_mismatches(candidate, current_asset_path=current_asset_path),
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
