"""Build tuition/donation ratio candidates from KASFO settlement raw files.

The current dashboard asset remains ``data/결산(22,23,24).csv``.  This
converter preserves the wider official KASFO source path and writes review-only
candidate/validation outputs for 세입 중 등록금 비율 and 세입 중 기부금 비율.
"""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd

from scripts.converters.kasfo_common import (
    CONVERSION_DIR,
    MISMATCH_REPORT_DIR,
    PROCESSING_REPORT_DIR,
    coverage_report,
    make_unique_columns,
    normalize_text,
    now_iso,
    parse_amount,
    read_csv_any,
    read_kasfo_excel_sheet,
    sha256_file,
    standardize_frame,
    write_csv,
    write_json,
)
from utils.data_pipeline import load_gyeolsan_frame
from utils.school_normalization import canonicalize_school_name_column


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "kasfo" / "gyeolsan" / "original"
SOURCE_ACQUISITION = PROJECT_ROOT / "data" / "raw" / "kasfo" / "gyeolsan" / "source_acquisition.json"
OUTPUT_DIR = CONVERSION_DIR / "gyeolsan"
CANDIDATE = OUTPUT_DIR / "kasfo_gyeolsan_2015_2024_candidate.csv"
METADATA = OUTPUT_DIR / "kasfo_gyeolsan_candidate.metadata.json"
PROCESSING_REPORT = PROCESSING_REPORT_DIR / "kasfo_gyeolsan.processing_report.json"
MISMATCH_REPORT = MISMATCH_REPORT_DIR / "kasfo_gyeolsan.mismatch.csv"
SOURCE_METADATA = PROJECT_ROOT / "data" / "metadata" / "gyeolsan_v1.source.json"

OPERATING_REVENUE_COL = "2.운영수입[1086]"
TUITION_REVENUE_COL = "4.등록금수입[1002]"
DONATION_REVENUE_COL = "4.기부금수입[1035]"

RAW_FILES: tuple[dict[str, str], ...] = (
    {
        "year_range": "2015-2020",
        "path": "data/raw/kasfo/gyeolsan/original/2015_2020_corporate_school_account_settlement.zip",
        "page_url": "https://uniarlimi.kasfo.or.kr/knowledge/data2Room/24513?pageIdx=10",
        "download_url": "https://support.kasfo.or.kr/component/file/download.asp?sBrdID=24513&sBrdFileID=5354",
        "post_id": "24513",
        "file_id": "5354",
        "original_file_name": "2015~2020회계연도 사립대학 법인교비 결산.zip",
    },
    {
        "year_range": "2021",
        "path": "data/raw/kasfo/gyeolsan/original/2021_corporate_school_account_settlement.xlsx",
        "page_url": "https://uniarlimi.kasfo.or.kr/knowledge/data2Room/25271?pageIdx=8",
        "download_url": "https://support.kasfo.or.kr/component/file/download.asp?sBrdID=25271&sBrdFileID=5630",
        "post_id": "25271",
        "file_id": "5630",
        "original_file_name": "법인일반 및 교비회계(통합) 결산(2021회계연도).xlsx",
    },
    {
        "year_range": "2022",
        "path": "data/raw/kasfo/gyeolsan/original/2022_corporate_school_account_settlement.xlsx",
        "page_url": "https://uniarlimi.kasfo.or.kr/knowledge/data2Room/28353?pageIdx=6",
        "download_url": "https://support.kasfo.or.kr/component/file/download.asp?sBrdID=28353&sBrdFileID=6971",
        "post_id": "28353",
        "file_id": "6971",
        "original_file_name": "법인일반 및 교비회계(통합) 결산(2022회계연도).xlsx",
    },
    {
        "year_range": "2023",
        "path": "data/raw/kasfo/gyeolsan/original/2023_corporate_school_account_settlement.xlsx",
        "page_url": "https://uniarlimi.kasfo.or.kr/knowledge/data2Room/31474?pageIdx=4",
        "download_url": "https://support.kasfo.or.kr/component/file/download.asp?sBrdID=31474&sBrdFileID=8512",
        "post_id": "31474",
        "file_id": "8512",
        "original_file_name": "법인일반회계 및 교비회계 결산(2023회계연도).xlsx",
    },
    {
        "year_range": "2024",
        "path": "data/raw/kasfo/gyeolsan/original/2024_corporate_school_account_settlement.xlsx",
        "page_url": "https://uniarlimi.kasfo.or.kr/knowledge/data2Room/35283?pageIdx=2",
        "download_url": "https://support.kasfo.or.kr/component/file/download.asp?sBrdID=35283&sBrdFileID=9832",
        "post_id": "35283",
        "file_id": "9832",
        "original_file_name": "법인일반회계 및 교비회계 결산(2024회계연도).xlsx",
    },
)


def _extract_year(value: str) -> int:
    match = re.search(r"(20\d{2})", value)
    if not match:
        raise ValueError(f"Could not infer settlement year from {value!r}")
    return int(match.group(1))


def _funding_sheet_name(path_or_buffer: Path | BytesIO) -> str:
    workbook = pd.ExcelFile(path_or_buffer, engine="openpyxl")
    for sheet in workbook.sheet_names:
        if "자금" in normalize_text(sheet) or "자금계산서" in normalize_text(sheet):
            return sheet
    raise ValueError(f"Could not locate funding sheet in {path_or_buffer!r}")


def _read_sheet_from_bytes(data: bytes, sheet_name: str, *, source_file_name: str) -> pd.DataFrame:
    raw = pd.read_excel(BytesIO(data), sheet_name=sheet_name, header=None, engine="openpyxl")
    header_row = None
    for idx, row in raw.iterrows():
        cells = {normalize_text(v) for v in row.tolist()}
        if "학교명" in cells and ("법인명" in cells or "회계" in cells or "회계연도" in cells):
            header_row = idx
            break
    if header_row is None:
        raise ValueError(f"Could not locate header row in {source_file_name} / {sheet_name}")

    header = make_unique_columns([normalize_text(c) or f"unnamed_{i}" for i, c in enumerate(raw.iloc[header_row].tolist())])
    frame = raw.iloc[header_row + 1 :].copy()
    frame.columns = header
    frame = frame.dropna(how="all")
    if "학교명" in frame.columns:
        frame = frame[frame["학교명"].notna()].copy()
    frame["source_file_name"] = source_file_name
    frame["source_sheet_name"] = sheet_name
    return frame.reset_index(drop=True)


def _prepare_raw_frame(frame: pd.DataFrame, *, year: int, source_file_name: str) -> pd.DataFrame:
    prepared = frame.copy()
    if "지역" not in prepared.columns and "소지역" in prepared.columns:
        prepared = prepared.rename(columns={"소지역": "지역"})
    if "회계연도" not in prepared.columns:
        prepared["회계연도"] = f"{year}년"
    if "설립" not in prepared.columns:
        prepared["설립"] = "사립"
    if "source_file_name" not in prepared.columns:
        prepared["source_file_name"] = source_file_name
    return standardize_frame(prepared)


def _load_xlsx(path: Path, *, year: int) -> pd.DataFrame:
    sheet_name = _funding_sheet_name(path)
    return _prepare_raw_frame(
        read_kasfo_excel_sheet(path, sheet_name, source_file_name=path.name),
        year=year,
        source_file_name=path.name,
    )


def _load_zip(path: Path) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if not info.filename.lower().endswith(".xlsx"):
                continue
            data = archive.read(info)
            year = _extract_year(info.filename)
            sheet_name = _funding_sheet_name(BytesIO(data))
            frame = _read_sheet_from_bytes(data, sheet_name, source_file_name=info.filename)
            frames.append(_prepare_raw_frame(frame, year=year, source_file_name=info.filename))
    if not frames:
        raise ValueError(f"No XLSX files found in {path}")
    frames = [frame.dropna(axis=1, how="all") for frame in frames]
    return pd.concat(frames, ignore_index=True)


def load_raw_source_frame() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for item in RAW_FILES:
        path = PROJECT_ROOT / item["path"]
        if path.suffix.lower() == ".zip":
            frames.append(_load_zip(path))
        else:
            frames.append(_load_xlsx(path, year=_extract_year(item["year_range"])))
    frames = [frame.dropna(axis=1, how="all") for frame in frames]
    return pd.concat(frames, ignore_index=True)


def build_candidate(raw: pd.DataFrame) -> pd.DataFrame:
    required = {
        "학교명",
        "법인명",
        "설립",
        "학급",
        "학종",
        "지역",
        "회계",
        "회계연도",
        OPERATING_REVENUE_COL,
        TUITION_REVENUE_COL,
        DONATION_REVENUE_COL,
        "source_file_name",
        "source_sheet_name",
    }
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"KASFO raw source is missing required columns: {sorted(missing)}")

    frame = raw[
        (raw["회계"] == "교비")
        & (raw["학급"] == "대학")
        & (raw["학종"] == "일반")
        & (raw["설립"] == "사립")
    ].copy()
    frame["기준년도"] = pd.to_numeric(frame["회계연도"].astype(str).str.replace("년", "", regex=False), errors="coerce")
    frame["운영수입"] = frame[OPERATING_REVENUE_COL].map(parse_amount)
    frame["등록금수입"] = frame[TUITION_REVENUE_COL].map(parse_amount)
    frame["기부금수입"] = frame[DONATION_REVENUE_COL].map(parse_amount)
    frame = frame.dropna(subset=["기준년도", "운영수입", "등록금수입", "기부금수입"])
    frame = frame[frame["운영수입"] > 0].copy()
    frame["기준년도"] = frame["기준년도"].astype(int)
    frame["등록금비율"] = (frame["등록금수입"] / frame["운영수입"] * 100).round(2)
    frame["기부금비율"] = (frame["기부금수입"] / frame["운영수입"] * 100).round(2)
    frame = canonicalize_school_name_column(frame, restrict_to_default_scope=False)

    keep_columns = [
        "기준년도",
        "학교명",
        "법인명",
        "설립",
        "학급",
        "학종",
        "지역",
        "회계",
        "운영수입",
        "등록금수입",
        "기부금수입",
        "등록금비율",
        "기부금비율",
        "source_file_name",
        "source_sheet_name",
    ]
    return frame[keep_columns].sort_values(["기준년도", "학교명"]).reset_index(drop=True)


def _default_scope(frame: pd.DataFrame) -> pd.DataFrame:
    return canonicalize_school_name_column(frame, restrict_to_default_scope=True).copy()


def build_mismatch_report(candidate: pd.DataFrame) -> pd.DataFrame:
    current = load_gyeolsan_frame()
    scoped = _default_scope(candidate)
    scoped = scoped[scoped["기준년도"].isin(current["기준년도"].unique())].copy()
    merged = current.merge(
        scoped,
        on=["학교명", "기준년도"],
        how="outer",
        suffixes=("_processed", "_raw"),
        indicator=True,
    )

    rows: list[dict[str, Any]] = []
    fields = (
        ("운영수입", 1.0),
        ("등록금수입", 1.0),
        ("기부금수입", 1.0),
        ("등록금비율", 0.01),
        ("기부금비율", 0.01),
    )
    for _, row in merged.iterrows():
        school = row.get("학교명")
        year = row.get("기준년도")
        if row["_merge"] != "both":
            rows.append(
                {
                    "severity": "high",
                    "field": "row",
                    "school_name": school,
                    "year": year,
                    "processed_value": None if row["_merge"] == "right_only" else "present",
                    "raw_value": None if row["_merge"] == "left_only" else "present",
                    "reason": f"row_{row['_merge']}",
                }
            )
            continue
        for field, tolerance in fields:
            processed = row.get(f"{field}_processed")
            raw = row.get(f"{field}_raw")
            try:
                processed_number = float(processed)
                raw_number = float(raw)
            except (TypeError, ValueError):
                continue
            if pd.isna(processed_number) or pd.isna(raw_number):
                continue
            diff = abs(processed_number - raw_number)
            if diff <= tolerance:
                continue
            is_ratio = field.endswith("비율")
            rows.append(
                {
                    "severity": "high" if is_ratio and diff > 0.1 else "medium",
                    "field": field,
                    "school_name": school,
                    "year": int(year) if pd.notna(year) else None,
                    "processed_value": round(processed_number, 6),
                    "raw_value": round(raw_number, 6),
                    "reason": f"absolute_difference_gt_{tolerance}",
                }
            )
    return pd.DataFrame(
        rows,
        columns=["severity", "field", "school_name", "year", "processed_value", "raw_value", "reason"],
    )


def _source_file_records() -> list[dict[str, Any]]:
    records = []
    for item in RAW_FILES:
        path = PROJECT_ROOT / item["path"]
        records.append(
            {
                **item,
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else None,
                "file_size_bytes": path.stat().st_size if path.exists() else None,
            }
        )
    return records


def run() -> dict[str, Any]:
    raw = load_raw_source_frame()
    candidate = build_candidate(raw)
    mismatches = build_mismatch_report(candidate)
    raw_files = _source_file_records()
    timestamp = now_iso()

    write_csv(CANDIDATE, candidate)
    write_csv(MISMATCH_REPORT, mismatches)

    source_payload = {
        "dataset_id": "gyeolsan",
        "dataset_name_ko": "결산 기반 세입 비율",
        "metric_ids": ["tuition", "donation"],
        "source_name": "사학재정알리미",
        "source_org": "한국사학진흥재단",
        "source_url": "https://uniarlimi.kasfo.or.kr/knowledge/data2Room",
        "source_menu": "대학재정데이터",
        "downloaded_at": timestamp,
        "source_preservation_status": "raw_preserved",
        "source_input_kind": "raw_xlsx_zip",
        "raw_files": raw_files,
        "formula": {
            "private_university_tuition_ratio": "등록금수입 / 운영수입 * 100",
            "private_university_donation_ratio": "기부금수입 / 운영수입 * 100",
            "amount_unit": "천원",
        },
        "notes": [
            "사립대 기준 산식을 적용했다.",
            "등록금회계/비등록금회계 분리 파일은 내부 전입 등으로 단순 합산 시 운영수입 이중 반영 위험이 있어 지표 산출 원천으로 사용하지 않았다.",
            "운영 CSV는 이 converter에서 자동 교체하지 않는다.",
        ],
    }
    write_json(SOURCE_ACQUISITION, source_payload)
    write_json(SOURCE_METADATA, source_payload)

    report = {
        "dataset_id": "gyeolsan",
        "dataset_name_ko": "결산 기반 세입 비율",
        "metric_ids": ["tuition", "donation"],
        "version": "kasfo_gyeolsan_raw_xlsx_zip_candidate_v1",
        "processed_at": timestamp,
        "source_preservation_status": "raw_preserved",
        "source_input_kind": "raw_xlsx_zip",
        "input_files": raw_files,
        "output_file": str(CANDIDATE.relative_to(PROJECT_ROOT)),
        "metadata_file": str(METADATA.relative_to(PROJECT_ROOT)),
        "source_metadata_file": str(SOURCE_METADATA.relative_to(PROJECT_ROOT)),
        "source_acquisition_file": str(SOURCE_ACQUISITION.relative_to(PROJECT_ROOT)),
        "mismatch_report": str(MISMATCH_REPORT.relative_to(PROJECT_ROOT)),
        "row_counts": {
            "source_input_rows": int(len(raw)),
            "candidate_rows": int(len(candidate)),
            "candidate_default_scope_rows": int(len(_default_scope(candidate))),
            "mismatch_rows": int(len(mismatches)),
        },
        "coverage": coverage_report(candidate),
        "year_range": {
            "min": int(candidate["기준년도"].min()) if not candidate.empty else None,
            "max": int(candidate["기준년도"].max()) if not candidate.empty else None,
        },
        "school_count": int(candidate["학교명"].nunique()),
        "mismatch_summary": {
            "total": int(len(mismatches)),
            "high": int((mismatches.get("severity") == "high").sum()) if not mismatches.empty else 0,
            "medium": int((mismatches.get("severity") == "medium").sum()) if not mismatches.empty else 0,
        },
        "known_limitations": [
            "국공립대 산식은 이번 candidate에 포함하지 않았다.",
            "2015~2020 ZIP 내부 XLSX는 공식 ZIP에서 읽어 변환하되 ZIP 원본을 보존한다.",
            "현재 운영 CSV와의 비교는 기본 화면 범위인 서울 소재 사립 일반대학 중심으로 수행한다.",
        ],
    }
    metadata = {
        "dataset": "kasfo_gyeolsan",
        "candidate_only": True,
        "do_not_promote_current_asset": True,
        "unit": "천원 for source amounts; percent for ratio columns",
        "source_files": {item["path"]: {"sha256": item["sha256"]} for item in raw_files},
        "outputs": {
            "candidate": str(CANDIDATE.relative_to(PROJECT_ROOT)),
            "processing_report": str(PROCESSING_REPORT.relative_to(PROJECT_ROOT)),
            "mismatch_report": str(MISMATCH_REPORT.relative_to(PROJECT_ROOT)),
        },
    }
    write_json(PROCESSING_REPORT, report)
    write_json(METADATA, metadata)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", help="write review-only candidate outputs")
    args = parser.parse_args()
    if not args.run:
        parser.error("Use --run to generate review-only outputs")
    report = run()
    print(
        "wrote kasfo gyeolsan candidate: "
        f"rows={report['row_counts']['candidate_rows']} mismatches={report['row_counts']['mismatch_rows']}"
    )


if __name__ == "__main__":
    main()
