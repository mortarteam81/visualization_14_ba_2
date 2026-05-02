"""Convert KASFO settlement raw/processed files into review-only candidates.

This converter does not promote or overwrite current assets.  It writes a raw
candidate parsed from local KASFO XLSX files plus a restated candidate from the
existing processed CSV, then emits comparison/risk reports for manual review.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from scripts.converters.kasfo_common import (
    COMPARISON_SCHOOLS,
    CONVERSION_DIR,
    MISMATCH_REPORT_DIR,
    PROCESSING_REPORT_DIR,
    coverage_report,
    now_iso,
    parse_amount,
    read_csv_any,
    read_kasfo_excel_sheet,
    sha256_file,
    standardize_frame,
    write_csv,
    write_json,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_FINANCE_DIR = PROJECT_ROOT / "data" / "raw" / "pending_manual" / "finance"
RAW_5YR = RAW_FINANCE_DIR / "kasfo_private_university_tuition_nontuition_settlement_db_5yr_20250113.xlsx"
RAW_2024 = RAW_FINANCE_DIR / "kasfo_tuition_nontuition_school_account_settlement_2024.xlsx"
PROCESSED_SETTLEMENT = PROJECT_ROOT / "data" / "결산(22,23,24).csv"

RAW_CANDIDATE = CONVERSION_DIR / "settlement" / "kasfo_settlement_raw_2020_2024_candidate.csv"
PROCESSED_CANDIDATE = CONVERSION_DIR / "settlement" / "kasfo_settlement_processed_2022_2024_restated_candidate.csv"
METADATA = CONVERSION_DIR / "settlement" / "kasfo_settlement_candidate.metadata.json"
PROCESSING_REPORT = PROCESSING_REPORT_DIR / "kasfo_settlement.processing_report.json"
MISMATCH_REPORT = MISMATCH_REPORT_DIR / "kasfo_settlement_processed_vs_raw_sample.csv"
ALIAS_RISK_REPORT = MISMATCH_REPORT_DIR / "kasfo_settlement_alias_risk.csv"

RAW_SHEETS = ["등록금(자금)", "비등록금(자금)"]


def build_raw_candidate() -> pd.DataFrame:
    frames = []
    for sheet in RAW_SHEETS:
        frame = read_kasfo_excel_sheet(RAW_5YR, sheet, source_file_name=RAW_5YR.name)
        frame["source_workbook_kind"] = "tuition_nontuition_5yr"
        frames.append(frame)
    raw = pd.concat(frames, ignore_index=True)
    return standardize_frame(raw)


def build_processed_candidate() -> pd.DataFrame:
    processed = read_csv_any(PROCESSED_SETTLEMENT, dtype=str)
    return standardize_frame(processed)


def normalized_year(value: Any) -> str:
    text = "" if pd.isna(value) else str(value).strip()
    return text.replace("년", "")


def col_or_blank(frame: pd.DataFrame, col: str) -> pd.Series:
    if col in frame.columns:
        return frame[col]
    return pd.Series([""] * len(frame), index=frame.index)


def compare_sample(raw: pd.DataFrame, processed: pd.DataFrame) -> pd.DataFrame:
    """Compare required schools on overlapping key KASFO finance columns.

    Header labels differ between raw and legacy processed for some account codes,
    so this focuses on exact overlapping column names plus known risk account
    names present in each source.
    """
    raw = raw.copy()
    processed = processed.copy()
    raw["_year"] = (col_or_blank(raw, "회계연도") if "회계연도" in raw.columns else col_or_blank(raw, "회계")).map(normalized_year)
    processed["_year"] = col_or_blank(processed, "회계연도").map(normalized_year)
    raw["_key"] = col_or_blank(raw, "학교명").astype(str) + "|" + raw["_year"].astype(str) + "|" + col_or_blank(raw, "회계").astype(str)
    processed["_key"] = col_or_blank(processed, "학교명").astype(str) + "|" + processed["_year"].astype(str) + "|" + col_or_blank(processed, "회계").astype(str)

    exact_cols = sorted(
        c
        for c in set(raw.columns).intersection(processed.columns)
        if c not in {"_key", "_year", "source_file_name", "source_sheet_name", "source_workbook_kind"}
        and c not in {"학교명", "법인명", "설립", "학급", "학종", "지역", "회계", "회계연도"}
    )[:25]
    risk_raw_cols = [c for c in raw.columns if "기타국고지원" in c or "미사용전기이월자금" in c]
    risk_processed_cols = [c for c in processed.columns if "기타국고지원" in c or "미사용전기이월자금" in c]

    rows: list[dict[str, Any]] = []
    schools = set(COMPARISON_SCHOOLS + ["가톨릭대학교", "강서대학교", "건국대학교", "한양대학교"])
    for _, prow in processed[processed["학교명"].isin(schools)].iterrows():
        candidates = raw[(raw["학교명"] == prow["학교명"]) & (raw["_year"] == prow["_year"])]
        if prow.get("회계") and "회계" in candidates.columns:
            candidates = candidates[candidates["회계"] == prow.get("회계")]
        if candidates.empty:
            rows.append({"학교명": prow.get("학교명"), "회계연도": prow.get("회계연도"), "회계": prow.get("회계"), "field": "row", "issue": "raw_candidate_row_missing"})
            continue
        rrow = candidates.iloc[0]
        for col in exact_cols:
            pv = parse_amount(prow.get(col))
            rv = parse_amount(rrow.get(col))
            if pv != rv:
                rows.append({"학교명": prow.get("학교명"), "회계연도": prow.get("회계연도"), "회계": prow.get("회계"), "field": col, "processed_value": pv, "raw_value": rv, "issue": "value_mismatch"})
        rows.append(
            {
                "학교명": prow.get("학교명"),
                "회계연도": prow.get("회계연도"),
                "회계": prow.get("회계"),
                "field": "risk_columns_present",
                "processed_risk_columns": ";".join(risk_processed_cols),
                "raw_risk_columns": ";".join(risk_raw_cols),
                "issue": "known_risk_context",
            }
        )
    return pd.DataFrame(rows)


def alias_risk(processed: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (school, corp), group in processed.groupby(["학교명", "법인명"], dropna=False):
        if pd.isna(school) or not str(school).strip():
            continue
        namesake_count = processed[processed["학교명"] == school]["법인명"].nunique(dropna=True) if "법인명" in processed.columns else 0
        rows.append(
            {
                "학교명": school,
                "법인명": corp,
                "row_count": len(group),
                "years": ",".join(sorted(set(group.get("회계연도", pd.Series(dtype=str)).dropna().astype(str)))),
                "same_school_distinct_corporations": namesake_count,
                "risk": "check_alias_or_corporation_name" if namesake_count > 1 or "(" in str(school) else "",
            }
        )
    return pd.DataFrame(rows).sort_values(["risk", "학교명"], ascending=[False, True])


def run() -> dict[str, Any]:
    raw = build_raw_candidate()
    processed = build_processed_candidate()
    mismatches = compare_sample(raw, processed)
    aliases = alias_risk(processed)

    write_csv(RAW_CANDIDATE, raw)
    write_csv(PROCESSED_CANDIDATE, processed)
    write_csv(MISMATCH_REPORT, mismatches)
    write_csv(ALIAS_RISK_REPORT, aliases)

    report = {
        "dataset": "kasfo_settlement",
        "created_at": now_iso(),
        "inputs": {
            str(RAW_5YR.relative_to(PROJECT_ROOT)): {"sha256": sha256_file(RAW_5YR)},
            str(PROCESSED_SETTLEMENT.relative_to(PROJECT_ROOT)): {"sha256": sha256_file(PROCESSED_SETTLEMENT)},
        },
        "outputs": [str(p.relative_to(PROJECT_ROOT)) for p in [RAW_CANDIDATE, PROCESSED_CANDIDATE, MISMATCH_REPORT, ALIAS_RISK_REPORT, METADATA, PROCESSING_REPORT]],
        "raw_candidate": {"rows": len(raw), "columns": len(raw.columns), "coverage": coverage_report(raw)},
        "processed_candidate": {"rows": len(processed), "columns": len(processed.columns), "coverage": coverage_report(processed)},
        "mismatch_rows": len(mismatches),
        "known_limitations": [
            "Raw 5-year workbook headers differ from legacy data/결산(22,23,24).csv headers, so comparison report is sample/exact-header based, not full semantic mapping.",
            "2022 기타국고지원[1514], 미사용전기/차기 이월자금 sign differences remain flagged for manual audit.",
            "No school code exists in the settlement raw/legacy processed rows; joins must avoid name-only promotion without a separate school-code crosswalk.",
            "KASFO 법인전입금 is a finance account amount and is conceptually separate from KCUE 법인전입금 비율.",
        ],
    }
    metadata = {
        "dataset": "kasfo_settlement",
        "candidate_only": True,
        "do_not_promote_current_asset": True,
        "amount_parse_rule": "trim, comma removal, '-' to null, negative sign preserved",
        "unit": "천원 in KASFO source files unless source states otherwise",
        "source_files": report["inputs"],
    }
    write_json(PROCESSING_REPORT, report)
    write_json(METADATA, metadata)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", help="write candidate outputs")
    args = parser.parse_args()
    if not args.run:
        parser.error("Use --run to generate review-only outputs")
    report = run()
    print(f"wrote kasfo settlement candidates: raw_rows={report['raw_candidate']['rows']} processed_rows={report['processed_candidate']['rows']}")


if __name__ == "__main__":
    main()
