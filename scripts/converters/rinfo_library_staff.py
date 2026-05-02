"""Create RINFO library-staff review candidates from the existing processed CSV.

Raw RINFO XLS/XLSX files are not currently preserved in this repository, so this
script intentionally performs a partial, review-only standardization:
processed CSV -> no-inf candidate -> explicit 34-school scope candidate -> reports.
It never overwrites data/processed assets.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pandas as pd

try:  # supports both `python script.py` and package imports in tests
    from scripts.converters.rinfo_common import (
        MISMATCH_REPORT_DIR,
        OUTPUT_ROOT,
        PROCESSING_REPORT_DIR,
        PROJECT_ROOT,
        RinfoConfig,
        add_common_candidate_fields,
        base_report,
        build_coverage_report,
        load_scope,
        numeric_series,
        parse_args,
        read_processed_csv,
        relative,
        write_candidate_csvs,
        write_json,
    )
except ModuleNotFoundError:  # pragma: no cover
    from rinfo_common import (  # type: ignore
        MISMATCH_REPORT_DIR,
        OUTPUT_ROOT,
        PROCESSING_REPORT_DIR,
        PROJECT_ROOT,
        RinfoConfig,
        add_common_candidate_fields,
        base_report,
        build_coverage_report,
        load_scope,
        numeric_series,
        parse_args,
        read_processed_csv,
        relative,
        write_candidate_csvs,
        write_json,
    )

CONFIG = RinfoConfig(
    dataset_id="library_staff",
    input_path=PROJECT_ROOT / "data" / "processed" / "library_staff_per_1000_students" / "library_staff_per_1000_students_2008_2025_v6_utf8.csv",
    raw_dir=PROJECT_ROOT / "data" / "raw" / "library_staff_per_1000_students",
    output_dir=OUTPUT_ROOT / "library_staff",
    report_path=PROCESSING_REPORT_DIR / "rinfo_library_staff.processing_report.json",
    mismatch_path=MISMATCH_REPORT_DIR / "rinfo_library_staff_formula_mismatch.csv",
    metric_col="library_staff_per_1000_students_recalculated",
    denominator_col="enrolled_students",
    total_col="total_staff_certified",
    output_prefix="library_staff_per_1000_students_2008_2025_candidate",
)


def build_formula_mismatch_report(source: pd.DataFrame, candidate: pd.DataFrame) -> pd.DataFrame:
    """Report rows where RINFO original and existing recalculated values diverge.

    The exact RINFO staff formula cannot be raw-verified without the source XLS/XLSX.
    This report therefore compares the processed `*_original` column with the
    existing processed recalculation, and flags zero-denominator rows separately.
    """

    original = numeric_series(source, "library_staff_per_1000_students_original")
    recalculated = numeric_series(source, CONFIG.metric_col)
    denominator = numeric_series(source, CONFIG.denominator_col)
    diff = (original - recalculated).abs()
    mask = (denominator == 0) | recalculated.isna() | recalculated.isin([math.inf, -math.inf]) | (diff > 0.05)
    report = source.loc[mask, [
        "reference_year",
        "row_no",
        "university_name",
        "school_type",
        "founding_type",
        "region_name",
        "size_group",
        "total_staff_certified",
        "total_staff_not_certified",
        "enrolled_students",
        "library_staff_per_1000_students_original",
        "library_staff_per_1000_students_recalculated",
        "source_file_name",
    ]].copy()
    report["recalc_minus_original_abs"] = diff.loc[report.index]
    report["mismatch_type"] = "original_vs_processed_recalculated_delta_or_zero_denominator"
    report.loc[denominator.loc[report.index] == 0, "mismatch_type"] = "zero_denominator_not_calculable"
    report["candidate_metric_after_no_inf_policy"] = candidate.loc[report.index, CONFIG.metric_col]
    return report


def build_candidate() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    source = read_processed_csv(CONFIG.input_path)
    scope_names, school_id_map = load_scope()
    candidate = add_common_candidate_fields(source, CONFIG, school_id_map)
    mismatch = build_formula_mismatch_report(source, candidate)
    coverage = build_coverage_report(CONFIG, candidate, scope_names)
    outputs = write_candidate_csvs(CONFIG, candidate)
    mismatch.to_csv(CONFIG.mismatch_path, index=False, encoding="utf-8-sig")
    report = base_report(CONFIG, source, candidate, scope_names, outputs, coverage, len(mismatch))
    report["formula_validation"] = {
        "status": "partial_processed_internal_check_only",
        "rule": "compare processed original metric and processed recalculated metric within 0.05; zero denominator is not calculable",
        "raw_verification": "not_performed_source_xls_xlsx_absent",
    }
    write_json(CONFIG.output_dir / "metadata.json", report)
    write_json(CONFIG.report_path, report)
    return candidate, mismatch, coverage, report


def main() -> None:
    args = parse_args(__doc__ or "RINFO library staff candidate standardizer")
    if not args.write:
        raise SystemExit("Use --write to create review-only candidate outputs.")
    _, mismatch, _, report = build_candidate()
    print(f"wrote {relative(CONFIG.output_dir)}")
    print(f"formula/limitation rows: {len(mismatch)}")
    print(f"processing report: {relative(CONFIG.report_path)}")
    print(f"status: {report['status']}")


if __name__ == "__main__":
    main()
