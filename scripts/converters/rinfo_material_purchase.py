"""Create RINFO material-purchase review candidates from the existing processed CSV.

Raw RINFO XLS/XLSX files are not currently preserved in this repository, so this
script intentionally performs a partial, review-only standardization:
processed CSV -> no-inf/zero-denominator candidate -> explicit 34-school scope
candidate -> reports. It never overwrites data/processed assets.
"""

from __future__ import annotations

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
    dataset_id="material_purchase",
    input_path=PROJECT_ROOT / "data" / "processed" / "library_material_purchase_per_student" / "library_material_purchase_per_student_2008_2025_v2_utf8.csv",
    raw_dir=PROJECT_ROOT / "data" / "raw" / "library_material_purchase_per_student",
    output_dir=OUTPUT_ROOT / "material_purchase",
    report_path=PROCESSING_REPORT_DIR / "rinfo_material_purchase.processing_report.json",
    mismatch_path=MISMATCH_REPORT_DIR / "rinfo_material_purchase_formula_mismatch.csv",
    metric_col="material_purchase_expense_per_student",
    denominator_col="enrolled_students_current_year",
    total_col="total_material_purchase_expense",
    output_prefix="library_material_purchase_per_student_2008_2025_candidate",
)

DETAIL_COLUMNS = [
    "books_purchase_expense",
    "serials_purchase_expense",
    "non_book_purchase_expense",
    "electronic_resources_total",
    "electronic_journals_expense",
    "web_db_expense",
    "subscribed_ebook_expense",
    "other_electronic_resources_expense",
]


def add_material_policy_fields(candidate: pd.DataFrame) -> pd.DataFrame:
    denominator = numeric_series(candidate, CONFIG.denominator_col)
    total = numeric_series(candidate, CONFIG.total_col or "total_material_purchase_expense")
    recalculated = total / denominator
    candidate["material_purchase_expense_per_student_formula_recalculated"] = recalculated.replace([float("inf"), float("-inf")], pd.NA)
    zero_denominator_mask = denominator == 0
    candidate.loc[zero_denominator_mask, CONFIG.metric_col] = pd.NA
    candidate.loc[zero_denominator_mask, "material_purchase_expense_per_student_formula_recalculated"] = pd.NA
    candidate.loc[zero_denominator_mask, "metric_calc_status"] = "not_calculable_zero_denominator"
    return candidate


def build_formula_mismatch_report(source: pd.DataFrame, candidate: pd.DataFrame) -> pd.DataFrame:
    denominator = numeric_series(source, CONFIG.denominator_col)
    total = numeric_series(source, CONFIG.total_col or "total_material_purchase_expense")
    metric = numeric_series(source, CONFIG.metric_col)
    recalculated = total / denominator
    diff = (recalculated - metric).abs()
    mask = ((denominator == 0) & (total != 0)) | ((denominator != 0) & (diff > 0.11))
    report = source.loc[mask, [
        "reference_year",
        "row_no",
        "university_name",
        "school_type",
        "founding_type",
        "region_name",
        "size_group",
        "total_material_purchase_expense",
        "enrolled_students_current_year",
        "material_purchase_expense_per_student",
        "source_file_name",
    ]].copy()
    report["formula_recalculated"] = recalculated.loc[report.index].replace([float("inf"), float("-inf")], pd.NA)
    report["formula_abs_diff"] = diff.loc[report.index]
    report["mismatch_type"] = "processed_metric_vs_total_div_students_delta"
    report.loc[denominator.loc[report.index] == 0, "mismatch_type"] = "zero_denominator_not_calculable"
    report["candidate_metric_after_no_inf_policy"] = candidate.loc[report.index, CONFIG.metric_col]
    return report


def detail_mapping_diagnostics(source: pd.DataFrame) -> dict[str, Any]:
    other_equals_total = bool((source["other_electronic_resources_expense"] == source["total_material_purchase_expense"]).all())
    detail_sum = sum(numeric_series(source, col) for col in DETAIL_COLUMNS)
    total = numeric_series(source, "total_material_purchase_expense")
    return {
        "status": "mapping_suspect" if other_equals_total else "needs_review",
        "other_electronic_resources_expense_equals_total_all_rows": other_equals_total,
        "other_electronic_resources_expense_equals_total_count": int((source["other_electronic_resources_expense"] == source["total_material_purchase_expense"]).sum()),
        "row_count": int(len(source)),
        "detail_sum_equals_total_count": int((detail_sum == total).sum()),
        "limitation": "other_electronic_resources_expense == total_material_purchase_expense for all rows; RINFO detail-column mapping is suspect and requires raw XLS/XLSX re-check.",
    }


def build_candidate() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    source = read_processed_csv(CONFIG.input_path)
    scope_names, school_id_map = load_scope()
    candidate = add_common_candidate_fields(source, CONFIG, school_id_map)
    candidate = add_material_policy_fields(candidate)
    mismatch = build_formula_mismatch_report(source, candidate)
    mapping = detail_mapping_diagnostics(source)
    if mapping["other_electronic_resources_expense_equals_total_all_rows"]:
        limitation_path = MISMATCH_REPORT_DIR / "rinfo_material_purchase_detail_mapping_limitation.csv"
        pd.DataFrame([mapping]).to_csv(limitation_path, index=False, encoding="utf-8-sig")
    coverage = build_coverage_report(CONFIG, candidate, scope_names)
    outputs = write_candidate_csvs(CONFIG, candidate)
    mismatch.to_csv(CONFIG.mismatch_path, index=False, encoding="utf-8-sig")
    report = base_report(
        CONFIG,
        source,
        candidate,
        scope_names,
        outputs,
        coverage,
        len(mismatch),
        extra={
            "detail_column_mapping_diagnostics": mapping,
            "limitations": [
                "RINFO 원본 xls/xlsx 부재로 원자료 직접 대조 불가.",
                mapping["limitation"],
            ],
        },
    )
    report["formula_validation"] = {
        "status": "partial_processed_internal_check_only",
        "rule": "total_material_purchase_expense / enrolled_students_current_year must match processed per-student metric within 0.11 unless denominator is zero",
        "raw_verification": "not_performed_source_xls_xlsx_absent",
    }
    write_json(CONFIG.output_dir / "metadata.json", report)
    write_json(CONFIG.report_path, report)
    return candidate, mismatch, coverage, report


def main() -> None:
    args = parse_args(__doc__ or "RINFO material purchase candidate standardizer")
    if not args.write:
        raise SystemExit("Use --write to create review-only candidate outputs.")
    _, mismatch, _, report = build_candidate()
    print(f"wrote {relative(CONFIG.output_dir)}")
    print(f"formula mismatch rows: {len(mismatch)}")
    print(f"detail mapping status: {report['detail_column_mapping_diagnostics']['status']}")
    print(f"processing report: {relative(CONFIG.report_path)}")
    print(f"status: {report['status']}")


if __name__ == "__main__":
    main()
