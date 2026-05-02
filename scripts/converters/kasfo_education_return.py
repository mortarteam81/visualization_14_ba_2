"""Build education-return candidates from KASFO settlement raw files.

The current dashboard asset remains the processed CSV under
``data/processed/education_cost_return_rate``.  This converter preserves
official KASFO raw files and writes review-only candidate/validation outputs.
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
    sha256_file,
    standardize_frame,
    write_csv,
    write_json,
)
from utils.data_pipeline import load_education_return_frame
from utils.school_normalization import canonicalize_school_name_column


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "kasfo" / "education_return" / "original"
SOURCE_ACQUISITION = PROJECT_ROOT / "data" / "raw" / "kasfo" / "education_return" / "source_acquisition.json"
OUTPUT_DIR = CONVERSION_DIR / "education_return"
CANDIDATE = OUTPUT_DIR / "kasfo_education_return_2016_2025_candidate.csv"
METADATA = OUTPUT_DIR / "kasfo_education_return_candidate.metadata.json"
PROCESSING_REPORT = PROCESSING_REPORT_DIR / "kasfo_education_return.processing_report.json"
MISMATCH_REPORT = MISMATCH_REPORT_DIR / "kasfo_education_return.mismatch.csv"
FORMULA_GAP_REPORT = MISMATCH_REPORT_DIR / "kasfo_education_return_formula_source_gap.csv"
THEME_ISSUE_CANDIDATE = OUTPUT_DIR / "kasfo_education_return_theme_issue_2020_2025_candidate.csv"
THEME_ISSUE_CROSSCHECK = MISMATCH_REPORT_DIR / "kasfo_education_return_theme_issue_crosscheck.csv"
THEME_ISSUE_SOURCE_ACQUISITION = PROJECT_ROOT / "data" / "raw" / "kasfo" / "education_return" / "theme_issue_source_acquisition.json"
SOURCE_METADATA = PROJECT_ROOT / "data" / "metadata" / "education_cost_return_rate.source.json"

TUITION_FILES: tuple[dict[str, str], ...] = (
    {
        "year_range": "2015-2020",
        "path": "data/raw/kasfo/education_return/original/tuition_2015_2020.zip",
        "page_url": "https://uniarlimi.kasfo.or.kr/knowledge/data2Room/33694?pageIdx=1",
        "download_url": "https://support.kasfo.or.kr/component/file/download.asp?sBrdID=33694&sBrdFileID=9276",
        "post_id": "33694",
        "file_id": "9276",
        "original_file_name": "붙임. 2015~2020회계연도 사립대학 교비(등록금회계 비등록금회계) 결산.zip",
    },
    {
        "year_range": "2021",
        "path": "data/raw/kasfo/education_return/original/tuition_2021.xlsx",
        "page_url": "https://uniarlimi.kasfo.or.kr/knowledge/data2Room/25272?pageIdx=1",
        "download_url": "https://support.kasfo.or.kr/component/file/download.asp?sBrdID=25272&sBrdFileID=5631",
        "post_id": "25272",
        "file_id": "5631",
        "original_file_name": "교비(등록금.비등록금회계)_결산(2021회계연도).xlsx",
    },
    {
        "year_range": "2022",
        "path": "data/raw/kasfo/education_return/original/tuition_2022.xlsx",
        "page_url": "https://uniarlimi.kasfo.or.kr/knowledge/data2Room/28354?pageIdx=1",
        "download_url": "https://support.kasfo.or.kr/component/file/download.asp?sBrdID=28354&sBrdFileID=7028",
        "post_id": "28354",
        "file_id": "7028",
        "original_file_name": "교비회계(등록금비등록금회계) 결산(2022회계연도).xlsx",
    },
    {
        "year_range": "2023",
        "path": "data/raw/kasfo/education_return/original/tuition_2023.xlsx",
        "page_url": "https://uniarlimi.kasfo.or.kr/knowledge/data2Room/31475?pageIdx=1",
        "download_url": "https://support.kasfo.or.kr/component/file/download.asp?sBrdID=31475&sBrdFileID=8511",
        "post_id": "31475",
        "file_id": "8511",
        "original_file_name": "교비회계(등록금.비등록금회계) 결산(2023회계연도).xlsx",
    },
    {
        "year_range": "2024",
        "path": "data/raw/kasfo/education_return/original/tuition_2024.xlsx",
        "page_url": "https://uniarlimi.kasfo.or.kr/knowledge/data2Room/35289?pageIdx=1",
        "download_url": "https://support.kasfo.or.kr/component/file/download.asp?sBrdID=35289&sBrdFileID=9840",
        "post_id": "35289",
        "file_id": "9840",
        "original_file_name": "2024회계연도 등록금 및 비등록금.xlsx",
    },
)

INDUSTRY_FILES: tuple[dict[str, str], ...] = (
    {
        "year_range": "2015-2020",
        "path": "data/raw/kasfo/education_return/original/industry_2015_2020.zip",
        "page_url": "https://uniarlimi.kasfo.or.kr/knowledge/data2Room/24519?pageIdx=1",
        "download_url": "https://support.kasfo.or.kr/component/file/download.asp?sBrdID=24519&sBrdFileID=5360",
        "post_id": "24519",
        "file_id": "5360",
        "original_file_name": "2015~2020회계연도 산학협력단회계 결산 재무제표.zip",
    },
    {
        "year_range": "2021",
        "path": "data/raw/kasfo/education_return/original/industry_2021.xlsx",
        "page_url": "https://uniarlimi.kasfo.or.kr/knowledge/data2Room/25276?pageIdx=1",
        "download_url": "https://support.kasfo.or.kr/component/file/download.asp?sBrdID=25276&sBrdFileID=5634",
        "post_id": "25276",
        "file_id": "5634",
        "original_file_name": "2021회계연도 산학협력단회계 결산 재무제표.xlsx",
    },
    {
        "year_range": "2022",
        "path": "data/raw/kasfo/education_return/original/industry_2022.xlsx",
        "page_url": "https://uniarlimi.kasfo.or.kr/knowledge/data2Room/28372?pageIdx=1",
        "download_url": "https://support.kasfo.or.kr/component/file/download.asp?sBrdID=28372&sBrdFileID=6995",
        "post_id": "28372",
        "file_id": "6995",
        "original_file_name": "2022회계연도 국 공 사립 대학(전문 원격 포함) 산학협력단회계 결산.xlsx",
    },
    {
        "year_range": "2023",
        "path": "data/raw/kasfo/education_return/original/industry_2023.xlsx",
        "page_url": "https://uniarlimi.kasfo.or.kr/knowledge/data2Room/31362?pageIdx=1",
        "download_url": "https://support.kasfo.or.kr/component/file/download.asp?sBrdID=31362&sBrdFileID=8652",
        "post_id": "31362",
        "file_id": "8652",
        "original_file_name": "2023회계연도 국 공 사립 대학 산학협력단회계 결산.xlsx",
    },
    {
        "year_range": "2024",
        "path": "data/raw/kasfo/education_return/original/industry_2024.xlsx",
        "page_url": "https://uniarlimi.kasfo.or.kr/knowledge/data2Room/35278?pageIdx=1",
        "download_url": "https://support.kasfo.or.kr/component/file/download.asp?sBrdID=35278&sBrdFileID=9831",
        "post_id": "35278",
        "file_id": "9831",
        "original_file_name": "2024회계연도 국·공·사립대학 산학협력단 결산.xlsx",
    },
)

RAW_FILES = TUITION_FILES + INDUSTRY_FILES

THEME_ISSUE_FILES: tuple[dict[str, str], ...] = tuple(
    {
        "year_range": str(year),
        "path": f"data/raw/kasfo/education_return/original/theme_issue_education_return_{year}.xlsx",
        "page_url": f"https://uniarlimi.kasfo.or.kr/statistics/themeIssue/view/1?pageIndex=1&putYear={year}&totalCount=0",
        "download_url": f"https://uniarlimi.kasfo.or.kr/statistics/themeIssue/excelDownLoad/1?pageIndex=1&totalCount=0&putYear={year}",
        "issue_id": "1",
        "original_file_name": f"{year}년_교육여건_교육비 환원율.xlsx",
        "source_menu": "통계현황 > 테마·이슈통계",
    }
    for year in range(2020, 2026)
)


def _extract_year(value: str) -> int:
    match = re.search(r"(20\d{2})", value)
    if not match:
        raise ValueError(f"Could not infer settlement year from {value!r}")
    return int(match.group(1))


def _read_excel_sheet_from_bytes(data: bytes, sheet_name: str, *, source_file_name: str) -> pd.DataFrame:
    raw = pd.read_excel(BytesIO(data), sheet_name=sheet_name, header=None, engine="openpyxl")
    return _frame_from_raw_sheet(raw, source_file_name=source_file_name, source_sheet_name=sheet_name)


def _read_excel_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name=sheet_name, header=None, engine="openpyxl")
    return _frame_from_raw_sheet(raw, source_file_name=path.name, source_sheet_name=sheet_name)


def _frame_from_raw_sheet(
    raw: pd.DataFrame,
    *,
    source_file_name: str,
    source_sheet_name: str,
) -> pd.DataFrame:
    header_row = None
    for idx, row in raw.iterrows():
        cells = {normalize_text(v) for v in row.tolist()}
        if "학교명" in cells:
            header_row = idx
            break
    if header_row is None:
        raise ValueError(f"Could not locate header row: {source_file_name} / {source_sheet_name}")

    header = make_unique_columns([normalize_text(c) or f"unnamed_{i}" for i, c in enumerate(raw.iloc[header_row].tolist())])
    frame = raw.iloc[header_row + 1 :].copy()
    frame.columns = header
    frame = frame.dropna(how="all")
    if "학교명" in frame.columns:
        frame = frame[frame["학교명"].notna()].copy()
    frame["source_file_name"] = source_file_name
    frame["source_sheet_name"] = source_sheet_name
    return standardize_frame(frame.reset_index(drop=True))


def _sheet_name(path_or_buffer: Path | BytesIO, candidates: tuple[str, ...]) -> str:
    workbook = pd.ExcelFile(path_or_buffer, engine="openpyxl")
    for candidate in candidates:
        for sheet in workbook.sheet_names:
            if normalize_text(sheet) == candidate:
                return sheet
    raise ValueError(f"Could not locate any of {candidates!r} in {path_or_buffer!r}")


def _sheet_names(path_or_buffer: Path | BytesIO, candidates: tuple[str, ...]) -> list[str]:
    workbook = pd.ExcelFile(path_or_buffer, engine="openpyxl")
    return [sheet for sheet in workbook.sheet_names if normalize_text(sheet) in candidates]


def _read_zip_members(path: Path, *, sheet_candidates: tuple[str, ...], read_all_matching: bool = False) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if not info.filename.lower().endswith(".xlsx"):
                continue
            data = archive.read(info)
            year = _extract_year(info.filename)
            sheet_names = _sheet_names(BytesIO(data), sheet_candidates) if read_all_matching else [_sheet_name(BytesIO(data), sheet_candidates)]
            for sheet_name in sheet_names:
                frame = _read_excel_sheet_from_bytes(data, sheet_name, source_file_name=info.filename).copy()
                frame["회계연도"] = frame.get("회계연도", f"{year}년")
                frame["accounting_year"] = year
                frame["source_archive_name"] = path.name
                frames.append(frame)
    if not frames:
        raise ValueError(f"No XLSX members found: {path}")
    return pd.concat(frames, ignore_index=True)


def _read_tuition_file(item: dict[str, str]) -> pd.DataFrame:
    path = PROJECT_ROOT / item["path"]
    if path.suffix.lower() == ".zip":
        return _read_zip_members(path, sheet_candidates=("자금계산서", "등록금(자금)", "비등록금(자금)"), read_all_matching=True)

    year = _extract_year(item["year_range"])
    sheet_names = _sheet_names(path, ("자금계산서", "등록금(자금)", "비등록금(자금)"))
    if not sheet_names:
        raise ValueError(f"Could not locate tuition cash-flow sheets in {path}")
    frames = []
    for sheet_name in sheet_names:
        frame = _read_excel_sheet(path, sheet_name).copy()
        if "회계연도" not in frame.columns:
            frame["회계연도"] = f"{year}년"
        frame["accounting_year"] = year
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def _read_industry_file(item: dict[str, str]) -> pd.DataFrame:
    path = PROJECT_ROOT / item["path"]
    if path.suffix.lower() == ".zip":
        return _read_zip_members(path, sheet_candidates=("현금흐름표",))

    year = _extract_year(item["year_range"])
    frame = _read_excel_sheet(path, "현금흐름표")
    if "회계연도" not in frame.columns:
        frame["회계연도"] = f"{year}년"
    frame["accounting_year"] = year
    return frame


def load_tuition_raw_frame() -> pd.DataFrame:
    return pd.concat([_read_tuition_file(item) for item in TUITION_FILES], ignore_index=True)


def load_industry_raw_frame() -> pd.DataFrame:
    return pd.concat([_read_industry_file(item) for item in INDUSTRY_FILES], ignore_index=True)


def _read_theme_issue_file(item: dict[str, str]) -> pd.DataFrame:
    path = PROJECT_ROOT / item["path"]
    raw = pd.read_excel(path, sheet_name=0, header=None, engine="openpyxl")
    header_row = None
    for idx, row in raw.iterrows():
        cells = {normalize_text(v) for v in row.tolist()}
        if {"번호", "학교명", "조사연도"}.issubset(cells):
            header_row = idx
            break
    if header_row is None:
        raise ValueError(f"Could not locate theme-issue header row: {path}")

    frame = raw.iloc[header_row + 2 :].copy()
    frame = frame.dropna(how="all")
    frame = frame[frame[1].notna()].copy()
    frame = frame[frame[0].map(lambda value: parse_amount(value) is not None)].copy()
    frame = frame.iloc[:, :19].copy()
    frame.columns = [
        "row_no",
        "university_name",
        "school_level",
        "school_type",
        "region",
        "survey_year",
        "tuition_salary",
        "tuition_admin",
        "tuition_books",
        "tuition_equipment",
        "tuition_research_student",
        "tuition_admissions",
        "industry_project_cost",
        "industry_support_project_cost",
        "industry_indirect_project_cost",
        "industry_general_admin",
        "industry_equipment",
        "tuition_revenue",
        "education_cost_return_rate_original_pct",
    ]
    for col in [
        "row_no",
        "survey_year",
        "tuition_salary",
        "tuition_admin",
        "tuition_books",
        "tuition_equipment",
        "tuition_research_student",
        "tuition_admissions",
        "industry_project_cost",
        "industry_support_project_cost",
        "industry_indirect_project_cost",
        "industry_general_admin",
        "industry_equipment",
        "tuition_revenue",
        "education_cost_return_rate_original_pct",
    ]:
        frame[col] = frame[col].map(parse_amount)
    for col in ["university_name", "school_level", "school_type", "region"]:
        frame[col] = frame[col].map(normalize_text)

    frame["survey_year"] = frame["survey_year"].astype(int)
    frame["tuition_account_total"] = (
        frame["tuition_salary"]
        + frame["tuition_admin"]
        + frame["tuition_research_student"]
        + frame["tuition_books"]
        + frame["tuition_equipment"]
        - frame["tuition_admissions"]
    )
    frame["industry_account_total"] = (
        frame["industry_project_cost"]
        + frame["industry_support_project_cost"]
        + frame["industry_indirect_project_cost"]
        + frame["industry_general_admin"]
        + frame["industry_equipment"]
    )
    denominator = frame["tuition_revenue"].where(frame["tuition_revenue"] > 0)
    frame["education_cost_return_rate_recalculated_pct"] = (
        (frame["tuition_account_total"] + frame["industry_account_total"]) / denominator * 100
    ).round(1)
    frame["source_file_name"] = path.name
    frame["source_page_url"] = item["page_url"]
    return frame.reset_index(drop=True)


def load_theme_issue_frame() -> pd.DataFrame:
    return pd.concat([_read_theme_issue_file(item) for item in THEME_ISSUE_FILES], ignore_index=True)


def _first_col(frame: pd.DataFrame, *prefixes: str) -> str:
    for prefix in prefixes:
        for col in frame.columns:
            if normalize_text(col).startswith(prefix):
                return col
    raise ValueError(f"Could not locate column with prefixes: {prefixes}")


def _sum_amount(group: pd.DataFrame, column: str) -> float:
    return float(group[column].map(parse_amount).fillna(0).sum())


def _join_sources(group: pd.DataFrame) -> str:
    sources: list[str] = []
    for source in group.get("source_file_name", pd.Series(dtype=str)).dropna().astype(str):
        if source not in sources:
            sources.append(source)
    return "; ".join(sources)


def _clean_kasfo_school_name(value: Any) -> str:
    return normalize_text(value).replace("(합산)", "").strip()


def build_tuition_components(raw: pd.DataFrame) -> pd.DataFrame:
    required = {"학교명", "accounting_year"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"Tuition raw source is missing required columns: {sorted(missing)}")

    salary_col = _first_col(raw, "3.보수")
    admin_col = _first_col(raw, "3.관리운영비")
    research_col = _first_col(raw, "3.연구학생경비")
    books_col = _first_col(raw, "5.도서구입비")
    equipment_col = _first_col(raw, "5.기계기구매입비")
    admissions_col = _first_col(raw, "4.입시관리비")
    tuition_revenue_col = _first_col(raw, "4.등록금수입")
    building_col = _first_col(raw, "5.건물매입비")
    construction_col = _first_col(raw, "5.건설가계정")

    frame = raw.copy()
    if "설립" in frame.columns:
        frame = frame[frame["설립"].isna() | frame["설립"].isin(["사립", ""])].copy()
    if "학급" in frame.columns:
        frame = frame[frame["학급"].isna() | frame["학급"].isin(["대학", ""])].copy()
    if "학종" in frame.columns:
        frame = frame[frame["학종"].isna() | frame["학종"].isin(["일반", ""])].copy()
    frame["학교명"] = frame["학교명"].map(_clean_kasfo_school_name)
    frame = canonicalize_school_name_column(frame, restrict_to_default_scope=False)

    rows: list[dict[str, Any]] = []
    group_cols = ["학교명", "accounting_year"]
    for (school, year), group in frame.groupby(group_cols, dropna=False):
        if not school or pd.isna(year):
            continue
        tuition_revenue = _sum_amount(group, tuition_revenue_col)
        salary = _sum_amount(group, salary_col)
        admin = _sum_amount(group, admin_col)
        research = _sum_amount(group, research_col)
        books = _sum_amount(group, books_col)
        equipment = _sum_amount(group, equipment_col)
        admissions = _sum_amount(group, admissions_col)
        building = _sum_amount(group, building_col) + _sum_amount(group, construction_col)
        rows.append(
            {
                "accounting_year": int(year),
                "기준년도": int(year) + 1,
                "학교명": school,
                "학교종류": "일반",
                "지역": normalize_text(group["지역"].dropna().iloc[0]) if "지역" in group.columns and not group["지역"].dropna().empty else "",
                "tuition_salary": salary,
                "tuition_admin": admin,
                "tuition_research_student": research,
                "tuition_books": books,
                "tuition_equipment": equipment,
                "tuition_admissions": admissions,
                "tuition_revenue": tuition_revenue,
                "private_school_account_cost": salary + admin + research - admissions,
                "library_purchase_cost": books,
                "school_equipment_purchase_cost": equipment,
                "school_building_purchase_cost": building,
                "tuition_source_file_name": _join_sources(group),
            }
        )
    return pd.DataFrame(rows)


def build_industry_components(raw: pd.DataFrame) -> pd.DataFrame:
    required = {"학교명", "accounting_year"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"Industry raw source is missing required columns: {sorted(missing)}")

    project_col = _first_col(raw, "3.산학협력비")
    support_col = _first_col(raw, "3.지원금사업비")
    indirect_col = _first_col(raw, "3.간접비사업비")
    general_col = _first_col(raw, "3.일반관리비")
    equipment_col = _first_col(raw, "4.기계기구취득")

    frame = raw.copy()
    if "설립" in frame.columns:
        frame = frame[frame["설립"].isna() | frame["설립"].isin(["사립", ""])].copy()
    if "학급" in frame.columns:
        frame = frame[frame["학급"].isna() | frame["학급"].isin(["대학", ""])].copy()
    if "학종" in frame.columns:
        frame = frame[frame["학종"].isna() | frame["학종"].isin(["일반", ""])].copy()
    frame["학교명"] = frame["학교명"].map(_clean_kasfo_school_name)
    frame = canonicalize_school_name_column(frame, restrict_to_default_scope=False)

    rows: list[dict[str, Any]] = []
    for (school, year), group in frame.groupby(["학교명", "accounting_year"], dropna=False):
        if not school or pd.isna(year):
            continue
        project = _sum_amount(group, project_col)
        support = _sum_amount(group, support_col)
        indirect = _sum_amount(group, indirect_col)
        general = _sum_amount(group, general_col)
        equipment = _sum_amount(group, equipment_col)
        rows.append(
            {
                "accounting_year": int(year),
                "기준년도": int(year) + 1,
                "학교명": school,
                "industry_project_cost": project,
                "industry_support_project_cost": support,
                "industry_indirect_project_cost": indirect,
                "industry_general_admin": general,
                "industry_equipment": equipment,
                "industry_account_total": project + support + indirect + general + equipment,
                "industry_equipment_purchase_cost": equipment,
                "industry_source_file_name": _join_sources(group),
            }
        )
    return pd.DataFrame(rows)


def _rolling_five_year_average(frame: pd.DataFrame, value_col: str, output_col: str) -> pd.Series:
    ordered = frame.sort_values(["학교명", "accounting_year"]).copy()
    return (
        ordered.groupby("학교명")[value_col]
        .transform(lambda series: series.rolling(window=5, min_periods=1).mean())
        .reindex(ordered.index)
    )


def build_candidate(tuition_raw: pd.DataFrame, industry_raw: pd.DataFrame) -> pd.DataFrame:
    tuition = build_tuition_components(tuition_raw)
    industry = build_industry_components(industry_raw)
    candidate = tuition.merge(industry, on=["학교명", "accounting_year", "기준년도"], how="left")
    for col in [
        "industry_project_cost",
        "industry_support_project_cost",
        "industry_indirect_project_cost",
        "industry_general_admin",
        "industry_equipment",
        "industry_account_total",
        "industry_equipment_purchase_cost",
    ]:
        if col in candidate.columns:
            candidate[col] = candidate[col].fillna(0)
    candidate["industry_source_file_name"] = candidate["industry_source_file_name"].fillna("")
    candidate["등록금회계_교육비합계"] = (
        candidate["tuition_salary"]
        + candidate["tuition_admin"]
        + candidate["tuition_research_student"]
        + candidate["tuition_books"]
        + candidate["tuition_equipment"]
        - candidate["tuition_admissions"]
    )
    candidate["산학협력단회계_교육비합계"] = candidate["industry_account_total"]
    candidate["등록금수입"] = candidate["tuition_revenue"]
    tuition_revenue_denominator = candidate["등록금수입"].where(candidate["등록금수입"] > 0)
    candidate["교육비환원율"] = (
        (candidate["등록금회계_교육비합계"] + candidate["산학협력단회계_교육비합계"])
        / tuition_revenue_denominator
        * 100
    ).round(1)

    candidate["equipment_purchase_total"] = candidate["school_equipment_purchase_cost"] + candidate["industry_equipment_purchase_cost"]
    ordered = candidate.sort_values(["학교명", "accounting_year"]).copy()
    ordered["equipment_purchase_recent_5yr_avg"] = ordered.groupby("학교명")["equipment_purchase_total"].transform(
        lambda series: series.rolling(window=5, min_periods=1).mean()
    )
    ordered["school_building_purchase_recent_5yr_avg"] = ordered.groupby("학교명")["school_building_purchase_cost"].transform(
        lambda series: series.rolling(window=5, min_periods=1).mean()
    )
    candidate = ordered

    candidate["building_cost_recent_5yr_avg_2_5pct"] = candidate["school_building_purchase_recent_5yr_avg"] * 0.025
    candidate["national_scholarship_type1_dadak_deduction"] = pd.NA
    candidate["private_accreditation_formula_partial_numerator"] = (
        candidate["private_school_account_cost"]
        + candidate["산학협력단회계_교육비합계"]
        + candidate["library_purchase_cost"]
        + candidate["equipment_purchase_recent_5yr_avg"]
        + candidate["building_cost_recent_5yr_avg_2_5pct"]
    )
    candidate["private_accreditation_formula_partial_rate_pct"] = (
        candidate["private_accreditation_formula_partial_numerator"] / tuition_revenue_denominator * 100
    ).round(1)
    candidate["formula_completeness_status"] = "partial_missing_kosaf_national_scholarship_type1_dadak"
    candidate["source_file_name"] = candidate["tuition_source_file_name"] + "; " + candidate["industry_source_file_name"]
    candidate = canonicalize_school_name_column(candidate, restrict_to_default_scope=False)

    keep_columns = [
        "accounting_year",
        "기준년도",
        "학교명",
        "학교종류",
        "지역",
        "등록금회계_교육비합계",
        "산학협력단회계_교육비합계",
        "등록금수입",
        "교육비환원율",
        "tuition_salary",
        "tuition_admin",
        "tuition_research_student",
        "tuition_books",
        "tuition_equipment",
        "tuition_admissions",
        "industry_project_cost",
        "industry_support_project_cost",
        "industry_indirect_project_cost",
        "industry_general_admin",
        "industry_equipment",
        "private_school_account_cost",
        "library_purchase_cost",
        "equipment_purchase_total",
        "equipment_purchase_recent_5yr_avg",
        "school_building_purchase_cost",
        "school_building_purchase_recent_5yr_avg",
        "building_cost_recent_5yr_avg_2_5pct",
        "national_scholarship_type1_dadak_deduction",
        "private_accreditation_formula_partial_numerator",
        "private_accreditation_formula_partial_rate_pct",
        "formula_completeness_status",
        "source_file_name",
    ]
    return candidate[keep_columns].sort_values(["기준년도", "학교명"]).reset_index(drop=True)


def _default_scope(frame: pd.DataFrame) -> pd.DataFrame:
    return canonicalize_school_name_column(frame, restrict_to_default_scope=True).copy()


def build_mismatch_report(candidate: pd.DataFrame) -> pd.DataFrame:
    current = load_education_return_frame()
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
        ("등록금회계_교육비합계", 5.0),
        ("산학협력단회계_교육비합계", 5.0),
        ("등록금수입", 5.0),
        ("교육비환원율", 0.05),
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
            rows.append(
                {
                    "severity": "high" if field == "교육비환원율" and diff > 0.1 else "medium",
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


def _current_processed_raw_frame() -> pd.DataFrame:
    current_asset = PROJECT_ROOT / "data" / "processed" / "education_cost_return_rate" / "education_cost_return_rate_2020_2025_v2_schema_utf8.csv"
    return pd.read_csv(current_asset, encoding="utf-8-sig")


def _comparison_frame(frame: pd.DataFrame, *, school_col: str, year_col: str) -> pd.DataFrame:
    out = canonicalize_school_name_column(frame, school_col=school_col, restrict_to_default_scope=False)
    out = out.copy()
    out["_school"] = out[school_col].map(normalize_text)
    out["_year"] = pd.to_numeric(out[year_col], errors="coerce")
    out = out.dropna(subset=["_school", "_year"])
    out["_year"] = out["_year"].astype(int)
    return out


def _compare_theme_issue_values(
    *,
    official: pd.DataFrame,
    comparison: pd.DataFrame,
    comparison_target: str,
    comparison_school_col: str,
    comparison_year_col: str,
    value_specs: tuple[tuple[str, str, str, float], ...],
) -> pd.DataFrame:
    official_keyed = _comparison_frame(official, school_col="university_name", year_col="survey_year")
    comparison_keyed = _comparison_frame(comparison, school_col=comparison_school_col, year_col=comparison_year_col)
    merged = official_keyed.merge(
        comparison_keyed,
        on=["_school", "_year"],
        how="outer",
        suffixes=("_official", "_comparison"),
        indicator=True,
    )

    rows: list[dict[str, Any]] = []
    for _, row in merged.iterrows():
        school = row.get("_school")
        year = row.get("_year")
        if row["_merge"] != "both":
            rows.append(
                {
                    "comparison_target": comparison_target,
                    "severity": "high",
                    "field": "row",
                    "school_name": school,
                    "year": int(year) if pd.notna(year) else None,
                    "theme_issue_value": None if row["_merge"] == "right_only" else "present",
                    "comparison_value": None if row["_merge"] == "left_only" else "present",
                    "difference": None,
                    "reason": f"row_{row['_merge']}",
                }
            )
            continue
        for field, official_col, comparison_col, tolerance in value_specs:
            official_value = row.get(f"{official_col}_official")
            comparison_value = row.get(f"{comparison_col}_comparison")
            try:
                official_number = float(official_value)
                comparison_number = float(comparison_value)
            except (TypeError, ValueError):
                continue
            if pd.isna(official_number) or pd.isna(comparison_number):
                continue
            difference = official_number - comparison_number
            if abs(difference) <= tolerance:
                continue
            rows.append(
                {
                    "comparison_target": comparison_target,
                    "severity": "high" if field.endswith("rate_pct") and abs(difference) > 0.1 else "medium",
                    "field": field,
                    "school_name": school,
                    "year": int(year) if pd.notna(year) else None,
                    "theme_issue_value": round(official_number, 6),
                    "comparison_value": round(comparison_number, 6),
                    "difference": round(difference, 6),
                    "reason": f"absolute_difference_gt_{tolerance}",
                }
            )
    return pd.DataFrame(
        rows,
        columns=[
            "comparison_target",
            "severity",
            "field",
            "school_name",
            "year",
            "theme_issue_value",
            "comparison_value",
            "difference",
            "reason",
        ],
    )


def build_theme_issue_crosscheck(theme_issue: pd.DataFrame, candidate: pd.DataFrame) -> pd.DataFrame:
    operating_specs = (
        ("tuition_account_total", "tuition_account_total", "tuition_account_total", 0.5),
        ("industry_account_total", "industry_account_total", "industry_account_total", 0.5),
        ("tuition_revenue", "tuition_revenue", "tuition_revenue", 0.5),
        (
            "education_cost_return_rate_pct",
            "education_cost_return_rate_recalculated_pct",
            "education_cost_return_rate_recalculated_pct",
            0.05,
        ),
    )
    raw_candidate_specs = (
        ("tuition_account_total", "tuition_account_total", "등록금회계_교육비합계", 0.5),
        ("industry_account_total", "industry_account_total", "산학협력단회계_교육비합계", 0.5),
        ("tuition_revenue", "tuition_revenue", "등록금수입", 0.5),
        ("education_cost_return_rate_pct", "education_cost_return_rate_recalculated_pct", "교육비환원율", 0.05),
    )
    operating_mismatches = _compare_theme_issue_values(
        official=theme_issue,
        comparison=_current_processed_raw_frame(),
        comparison_target="operating_csv",
        comparison_school_col="university_name",
        comparison_year_col="survey_year",
        value_specs=operating_specs,
    )
    candidate_years = set(pd.to_numeric(candidate["기준년도"], errors="coerce").dropna().astype(int))
    theme_for_raw_candidate = theme_issue[
        theme_issue["survey_year"].isin(candidate_years)
        & (theme_issue["school_level"].astype(str).str.strip() == "대학")
        & (theme_issue["school_type"].astype(str).str.strip() == "일반")
    ].copy()
    candidate_for_theme_years = candidate[candidate["기준년도"].isin(set(theme_for_raw_candidate["survey_year"]))].copy()
    raw_candidate_mismatches = _compare_theme_issue_values(
        official=theme_for_raw_candidate,
        comparison=candidate_for_theme_years,
        comparison_target="raw_financial_candidate",
        comparison_school_col="학교명",
        comparison_year_col="기준년도",
        value_specs=raw_candidate_specs,
    )
    return pd.concat([operating_mismatches, raw_candidate_mismatches], ignore_index=True)


def build_formula_gap_report() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "dataset_id": "education_return",
                "formula_component": "국가장학금 I유형 및 다자녀 국가장학금",
                "required_by": "2026 대학기관평가인증 편람 양식 1.3-6 사립대 교육비 환원율",
                "available_in_kasfo_data2room": False,
                "source_needed": "한국장학재단 결산자료 또는 평가원 요청자료",
                "impact": "KASFO 원자료만으로 편람 산식 전체값은 확정할 수 없으며, dashboard 운영값 검증용 산식과 KASFO 가용 구성요소를 분리 보존한다.",
            }
        ]
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


def _theme_issue_download_records() -> list[dict[str, Any]]:
    if THEME_ISSUE_SOURCE_ACQUISITION.exists():
        payload = json.loads(THEME_ISSUE_SOURCE_ACQUISITION.read_text(encoding="utf-8"))
        records = payload.get("records", [])
        if isinstance(records, list):
            return [record for record in records if isinstance(record, dict)]
    return []


def _theme_issue_file_records() -> list[dict[str, Any]]:
    downloaded = {str(item.get("path")): item for item in _theme_issue_download_records()}
    records = []
    for item in THEME_ISSUE_FILES:
        path = PROJECT_ROOT / item["path"]
        download_record = downloaded.get(item["path"], {})
        records.append(
            {
                **item,
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else None,
                "file_size_bytes": path.stat().st_size if path.exists() else None,
                "download_record": download_record or None,
            }
        )
    return records


def run() -> dict[str, Any]:
    tuition_raw = load_tuition_raw_frame()
    industry_raw = load_industry_raw_frame()
    candidate = build_candidate(tuition_raw, industry_raw)
    mismatches = build_mismatch_report(candidate)
    formula_gaps = build_formula_gap_report()
    theme_issue = load_theme_issue_frame()
    theme_issue_crosscheck = build_theme_issue_crosscheck(theme_issue, candidate)
    raw_files = _source_file_records()
    theme_issue_files = _theme_issue_file_records()
    timestamp = now_iso()

    write_csv(CANDIDATE, candidate)
    write_csv(THEME_ISSUE_CANDIDATE, theme_issue)
    write_csv(MISMATCH_REPORT, mismatches)
    write_csv(FORMULA_GAP_REPORT, formula_gaps)
    write_csv(THEME_ISSUE_CROSSCHECK, theme_issue_crosscheck)

    source_payload = {
        "dataset_id": "education_return",
        "dataset_name_ko": "교육비 환원율",
        "metric_ids": ["education_return"],
        "source_name": "사학재정알리미",
        "source_org": "한국사학진흥재단",
        "source_url": "https://uniarlimi.kasfo.or.kr/knowledge/data2Room",
        "source_menu": "대학재정데이터",
        "supplementary_source_url": "https://uniarlimi.kasfo.or.kr/statistics/themeIssue/view/1",
        "supplementary_source_menu": "통계현황 > 테마·이슈통계 > 교육비 환원율",
        "downloaded_at": timestamp,
        "source_preservation_status": "raw_preserved",
        "source_input_kind": "raw_xlsx_zip",
        "supplementary_source_input_kind": "theme_issue_official_xlsx",
        "raw_files": [*raw_files, *theme_issue_files],
        "primary_raw_files": raw_files,
        "supplementary_official_theme_issue_files": theme_issue_files,
        "formula": {
            "dashboard_current_verification": "(교비회계 보수 + 관리운영비 + 연구학생경비 + 도서구입비 + 기계기구매입비 - 입시관리비 + 산학협력단 기계기구취득 포함 비용) / 등록금수입 * 100",
            "private_accreditation_partial": "교비회계 + 산학협력단회계 + 도서구입비 + 최근5년 기계기구매입/취득비 평균 + 최근5년 건축비 평균의 2.5% - 국가장학금 I유형/다자녀",
            "amount_unit": "천원",
        },
        "notes": [
            "현재 운영 화면의 교육비 환원율 검증용 산식은 KASFO 교비회계 및 산학협력단회계 원자료로 재현했다.",
            "KASFO 테마·이슈통계 교육비 환원율 공식 엑셀을 별도 보존하고 운영 CSV와 교차검증했다.",
            "편람 산식의 국가장학금 I유형 및 다자녀 국가장학금은 KASFO 대학재정데이터만으로 확정할 수 없어 source gap으로 분리했다.",
            "운영 CSV는 이 converter에서 자동 교체하지 않는다.",
        ],
    }
    write_json(SOURCE_ACQUISITION, source_payload)
    write_json(SOURCE_METADATA, source_payload)

    report = {
        "dataset_id": "education_return",
        "dataset_name_ko": "교육비 환원율",
        "metric_ids": ["education_return"],
        "version": "kasfo_education_return_raw_xlsx_zip_candidate_v2_theme_issue_crosscheck",
        "processed_at": timestamp,
        "source_preservation_status": "raw_preserved",
        "source_input_kind": "raw_xlsx_zip",
        "supplementary_source_input_kind": "theme_issue_official_xlsx",
        "input_files": raw_files,
        "supplementary_official_theme_issue_files": theme_issue_files,
        "output_file": str(CANDIDATE.relative_to(PROJECT_ROOT)),
        "official_theme_issue_candidate_file": str(THEME_ISSUE_CANDIDATE.relative_to(PROJECT_ROOT)),
        "metadata_file": str(METADATA.relative_to(PROJECT_ROOT)),
        "source_metadata_file": str(SOURCE_METADATA.relative_to(PROJECT_ROOT)),
        "source_acquisition_file": str(SOURCE_ACQUISITION.relative_to(PROJECT_ROOT)),
        "theme_issue_source_acquisition_file": str(THEME_ISSUE_SOURCE_ACQUISITION.relative_to(PROJECT_ROOT)),
        "mismatch_report": str(MISMATCH_REPORT.relative_to(PROJECT_ROOT)),
        "formula_gap_report": str(FORMULA_GAP_REPORT.relative_to(PROJECT_ROOT)),
        "official_theme_issue_crosscheck_report": str(THEME_ISSUE_CROSSCHECK.relative_to(PROJECT_ROOT)),
        "row_counts": {
            "source_input_rows": int(len(tuition_raw) + len(industry_raw)),
            "tuition_raw_rows": int(len(tuition_raw)),
            "industry_raw_rows": int(len(industry_raw)),
            "candidate_rows": int(len(candidate)),
            "candidate_default_scope_rows": int(len(_default_scope(candidate))),
            "mismatch_rows": int(len(mismatches)),
            "theme_issue_source_rows": int(len(theme_issue)),
            "theme_issue_candidate_rows": int(len(theme_issue)),
            "theme_issue_crosscheck_rows": int(len(theme_issue_crosscheck)),
            "theme_issue_operating_mismatch_rows": int(
                (theme_issue_crosscheck.get("comparison_target") == "operating_csv").sum()
            )
            if not theme_issue_crosscheck.empty
            else 0,
            "theme_issue_raw_financial_candidate_mismatch_rows": int(
                (theme_issue_crosscheck.get("comparison_target") == "raw_financial_candidate").sum()
            )
            if not theme_issue_crosscheck.empty
            else 0,
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
        "official_theme_issue_crosscheck_summary": {
            "total": int(len(theme_issue_crosscheck)),
            "operating_csv": int((theme_issue_crosscheck.get("comparison_target") == "operating_csv").sum())
            if not theme_issue_crosscheck.empty
            else 0,
            "raw_financial_candidate": int(
                (theme_issue_crosscheck.get("comparison_target") == "raw_financial_candidate").sum()
            )
            if not theme_issue_crosscheck.empty
            else 0,
        },
        "known_limitations": formula_gaps.to_dict("records"),
    }
    metadata = {
        "dataset": "kasfo_education_return",
        "candidate_only": True,
        "do_not_promote_current_asset": True,
        "unit": "천원 for source amounts; percent for rate columns",
        "source_files": {item["path"]: {"sha256": item["sha256"]} for item in [*raw_files, *theme_issue_files]},
        "outputs": {
            "candidate": str(CANDIDATE.relative_to(PROJECT_ROOT)),
            "official_theme_issue_candidate": str(THEME_ISSUE_CANDIDATE.relative_to(PROJECT_ROOT)),
            "processing_report": str(PROCESSING_REPORT.relative_to(PROJECT_ROOT)),
            "mismatch_report": str(MISMATCH_REPORT.relative_to(PROJECT_ROOT)),
            "formula_gap_report": str(FORMULA_GAP_REPORT.relative_to(PROJECT_ROOT)),
            "official_theme_issue_crosscheck_report": str(THEME_ISSUE_CROSSCHECK.relative_to(PROJECT_ROOT)),
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
        "wrote kasfo education-return candidate: "
        f"rows={report['row_counts']['candidate_rows']} mismatches={report['row_counts']['mismatch_rows']}"
    )


if __name__ == "__main__":
    main()
