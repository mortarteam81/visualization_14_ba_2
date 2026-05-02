"""Restate KASFO education-cost return rate processed data as candidate.

The original XLSX is not present in the repository.  This script therefore does
not claim raw-source verification; it only standardizes the existing processed
file and validates the recalculation formula where components are available.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import pandas as pd

from scripts.converters.kasfo_common import (
    CONVERSION_DIR,
    MISMATCH_REPORT_DIR,
    PROCESSING_REPORT_DIR,
    coverage_report,
    now_iso,
    parse_amount,
    sha256_file,
    standardize_frame,
    write_csv,
    write_json,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED = PROJECT_ROOT / "data" / "processed" / "education_cost_return_rate" / "education_cost_return_rate_2020_2025_v2_schema_utf8.csv"
CANDIDATE = CONVERSION_DIR / "education_return" / "kasfo_education_return_2020_2025_restated_candidate.csv"
METADATA = CONVERSION_DIR / "education_return" / "kasfo_education_return_candidate.metadata.json"
PROCESSING_REPORT = PROCESSING_REPORT_DIR / "kasfo_education_return.processing_report.json"
MISMATCH_REPORT = MISMATCH_REPORT_DIR / "kasfo_education_return_formula_mismatch.csv"
LIMITATION_REPORT = MISMATCH_REPORT_DIR / "kasfo_education_return_raw_limitation.csv"

COMPONENT_COLUMNS = [
    "tuition_salary",
    "tuition_admin",
    "tuition_research_student",
    "tuition_books",
    "tuition_equipment",
    "tuition_scholarship",
    "tuition_admissions",
    "industry_project_cost",
    "industry_support_project_cost",
    "industry_indirect_project_cost",
    "industry_general_admin",
    "industry_equipment",
]


def recalc(row: pd.Series) -> float | None:
    revenue = parse_amount(row.get("tuition_revenue"))
    if revenue in (None, 0):
        return None
    # The processed schema already includes account totals.  Using totals avoids
    # double-counting/including detail columns not used by the original v2
    # calculation and reproduces the existing recalculated_pct field.
    tuition_total = parse_amount(row.get("tuition_account_total")) or 0.0
    industry_total = parse_amount(row.get("industry_account_total")) or 0.0
    return round((tuition_total + industry_total) / revenue * 100, 1)


def run() -> dict[str, Any]:
    frame = pd.read_csv(PROCESSED, dtype=str)
    candidate = standardize_frame(frame, amount_columns=COMPONENT_COLUMNS + ["tuition_account_total", "industry_account_total", "tuition_revenue", "education_cost_return_rate_original_pct", "education_cost_return_rate_recalculated_pct"])
    candidate["education_cost_return_rate_candidate_recalculated_pct"] = candidate.apply(recalc, axis=1)
    candidate["raw_source_limitation"] = "original_xlsx_absent; source_file_name blank in processed rows"

    mismatch_rows: list[dict[str, Any]] = []
    for _, row in candidate.iterrows():
        expected = parse_amount(row.get("education_cost_return_rate_recalculated_pct"))
        actual = row.get("education_cost_return_rate_candidate_recalculated_pct")
        if expected is not None and actual is not None and not math.isclose(float(expected), float(actual), abs_tol=0.05):
            mismatch_rows.append(
                {
                    "survey_year": row.get("survey_year"),
                    "university_name": row.get("university_name"),
                    "processed_recalculated_pct": expected,
                    "candidate_recalculated_pct": actual,
                    "issue": "formula_mismatch",
                }
            )
    mismatches = pd.DataFrame(
        mismatch_rows,
        columns=["survey_year", "university_name", "processed_recalculated_pct", "candidate_recalculated_pct", "issue"],
    )
    limitations = pd.DataFrame(
        [
            {
                "dataset": "kasfo_education_return",
                "limitation": "original XLSX raw source is absent; processed source_file_name is blank/NaN, so direct raw-source equality cannot be declared",
                "allowed_scope": "processed-to-candidate restandardization and formula validation only",
            }
        ]
    )

    write_csv(CANDIDATE, candidate)
    write_csv(MISMATCH_REPORT, mismatches)
    write_csv(LIMITATION_REPORT, limitations)

    report = {
        "dataset": "kasfo_education_return",
        "created_at": now_iso(),
        "inputs": {str(PROCESSED.relative_to(PROJECT_ROOT)): {"sha256": sha256_file(PROCESSED)}},
        "outputs": [str(p.relative_to(PROJECT_ROOT)) for p in [CANDIDATE, MISMATCH_REPORT, LIMITATION_REPORT, METADATA, PROCESSING_REPORT]],
        "candidate": {"rows": len(candidate), "columns": len(candidate.columns), "coverage": coverage_report(candidate, school_col="university_name")},
        "formula_mismatch_rows": len(mismatches),
        "known_limitations": limitations.to_dict("records"),
    }
    metadata = {
        "dataset": "kasfo_education_return",
        "candidate_only": True,
        "raw_verification_status": "blocked_raw_xlsx_absent",
        "formula": "(tuition_account_total + industry_account_total) / tuition_revenue * 100, rounded to 1 decimal",
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
    print(f"wrote kasfo education-return candidate: rows={report['candidate']['rows']} formula_mismatches={report['formula_mismatch_rows']}")


if __name__ == "__main__":
    main()
