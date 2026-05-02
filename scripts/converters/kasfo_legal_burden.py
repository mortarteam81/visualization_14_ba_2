"""Restate KASFO legal-burden data as a review-only candidate."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from scripts.converters.kasfo_common import (
    CONVERSION_DIR,
    MISMATCH_REPORT_DIR,
    PROCESSING_REPORT_DIR,
    coverage_report,
    normalize_code,
    now_iso,
    parse_amount,
    read_csv_any,
    sha256_file,
    standardize_frame,
    write_csv,
    write_json,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ROOT_ORIGINAL = PROJECT_ROOT / "14-ba-2.-beobjeongbudamgeum-budam-hyeonhwang_daehag_beobjeongbudamgeum-budamryul-20260309-seoul-sojae-saribdaehag.csv"
PROCESSED = PROJECT_ROOT / "data" / "법정부담금_부담율.csv"

CANDIDATE = CONVERSION_DIR / "legal_burden" / "kasfo_legal_burden_2025_restated_candidate.csv"
METADATA = CONVERSION_DIR / "legal_burden" / "kasfo_legal_burden_candidate.metadata.json"
PROCESSING_REPORT = PROCESSING_REPORT_DIR / "kasfo_legal_burden.processing_report.json"
MISMATCH_REPORT = MISMATCH_REPORT_DIR / "kasfo_legal_burden_original_vs_processed.csv"
CODE_RISK_REPORT = MISMATCH_REPORT_DIR / "kasfo_legal_burden_school_code_risk.csv"

NUMERIC_COLUMNS = ["입학정원(학부)", "재학생수(학부)", "졸업생수(학부)", "전임교원수(학부+대학원)", "법정부담금기준액", "법정부담금부담액", "부담율"]


def load_candidate(path: Path) -> pd.DataFrame:
    frame = read_csv_any(path, dtype=str)
    frame = standardize_frame(frame, amount_columns=NUMERIC_COLUMNS)
    for col in ["대표학교코드", "학교코드"]:
        if col in frame.columns:
            frame[col] = frame[col].map(normalize_code)
    return frame


def compare(original: pd.DataFrame, processed: pd.DataFrame) -> pd.DataFrame:
    key_cols = ["학교명", "기준년도"]
    original = original.copy()
    processed = processed.copy()
    original["_key"] = original["학교명"].astype(str) + "|" + original["기준년도"].astype(str)
    processed["_key"] = processed["학교명"].astype(str) + "|" + processed["기준년도"].astype(str)
    rows: list[dict[str, Any]] = []
    for _, prow in processed.iterrows():
        matches = original[original["_key"] == prow["_key"]]
        if matches.empty:
            rows.append({"학교명": prow.get("학교명"), "기준년도": prow.get("기준년도"), "field": "row", "issue": "original_row_missing"})
            continue
        orow = matches.iloc[0]
        for col in [c for c in NUMERIC_COLUMNS + ["대표학교코드", "학교코드"] if c in processed.columns and c in original.columns]:
            pv = prow.get(col)
            ov = orow.get(col)
            if col in NUMERIC_COLUMNS:
                pv = parse_amount(pv)
                ov = parse_amount(ov)
            if str(pv) != str(ov):
                rows.append({"학교명": prow.get("학교명"), "기준년도": prow.get("기준년도"), "field": col, "processed_value": pv, "original_value": ov, "issue": "value_or_format_mismatch"})
    columns = ["학교명", "기준년도", "field", "processed_value", "original_value", "issue"]
    return pd.DataFrame(rows, columns=columns)


def code_risks(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in frame.iterrows():
        for col in ["대표학교코드", "학교코드"]:
            if col in frame.columns:
                normalized = normalize_code(row.get(col))
                raw_text = "" if pd.isna(row.get(col)) else str(row.get(col)).strip()
                rows.append(
                    {
                        "학교명": row.get("학교명"),
                        "field": col,
                        "raw_value_seen_after_read": raw_text,
                        "normalized_7_digit": normalized,
                        "risk": "leading_zero_was_or_may_have_been_lost" if raw_text != normalized else "",
                    }
                )
    return pd.DataFrame(rows)


def run() -> dict[str, Any]:
    original = load_candidate(ROOT_ORIGINAL)
    processed = load_candidate(PROCESSED)
    mismatches = compare(original, processed)
    risks = code_risks(read_csv_any(PROCESSED, dtype=str))

    write_csv(CANDIDATE, processed)
    write_csv(MISMATCH_REPORT, mismatches)
    write_csv(CODE_RISK_REPORT, risks)

    report = {
        "dataset": "kasfo_legal_burden",
        "created_at": now_iso(),
        "inputs": {
            str(ROOT_ORIGINAL.relative_to(PROJECT_ROOT)): {"sha256": sha256_file(ROOT_ORIGINAL)},
            str(PROCESSED.relative_to(PROJECT_ROOT)): {"sha256": sha256_file(PROCESSED)},
        },
        "outputs": [str(p.relative_to(PROJECT_ROOT)) for p in [CANDIDATE, MISMATCH_REPORT, CODE_RISK_REPORT, METADATA, PROCESSING_REPORT]],
        "candidate": {"rows": len(processed), "columns": len(processed.columns), "coverage": coverage_report(processed)},
        "mismatch_rows": len(mismatches),
        "known_limitations": [
            "Root CSV is treated as local original-like source; no official-site download performed.",
            "Legacy CSV had school-code leading-zero loss risk; candidate normalizes 대표학교코드/학교코드 to 7 digits.",
        ],
    }
    metadata = {
        "dataset": "kasfo_legal_burden",
        "candidate_only": True,
        "school_code_rule": "대표학교코드/학교코드 are zfilled to 7 digits",
        "amount_parse_rule": "trim, comma removal, '-' to null, negative sign preserved",
        "source_files": report["inputs"],
    }
    write_json(PROCESSING_REPORT, report)
    write_json(METADATA, metadata)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if not args.run:
        parser.error("Use --run to generate review-only outputs")
    report = run()
    print(f"wrote kasfo legal-burden candidate: rows={report['candidate']['rows']} mismatches={report['mismatch_rows']}")


if __name__ == "__main__":
    main()
