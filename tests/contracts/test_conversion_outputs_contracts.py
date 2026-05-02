from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from scripts.validate_conversion_outputs import (
    COMPARISON_11,
    CONVERSION_OUTPUTS_DIR,
    DEFAULT_REPORT_PATH,
    PROJECT_ROOT,
    collect_candidate_batches,
    load_default_scope_names,
    validate_conversion_outputs,
    write_report,
)


CONVERSION_OUTPUTS = PROJECT_ROOT / "data" / "conversion_outputs"


def test_conversion_scope_definitions_are_fixed() -> None:
    default_scope = load_default_scope_names()

    assert len(COMPARISON_11) == 11
    assert len(set(COMPARISON_11)) == 11
    assert len(default_scope) == 34
    assert len(set(default_scope)) == 34
    assert set(COMPARISON_11).issubset(default_scope)


def test_conversion_outputs_are_candidate_only_when_present() -> None:
    if not CONVERSION_OUTPUTS.exists() or not collect_candidate_batches(CONVERSION_OUTPUTS):
        pytest.skip("No data/conversion_outputs candidate batches exist yet.")

    report = validate_conversion_outputs()
    assert report["summary"]["candidate_batch_count"] > 0

    # Source-agent batches may be incomplete while the integration work is in progress.
    # Keep this contract focused on the non-negotiable safety boundary: candidates must
    # not live under, or symlink into, raw/processed/current operating assets.
    safety_checks = {
        "candidate_files_under_conversion_outputs",
        "candidate_files_not_under_processed",
        "candidate_files_not_under_raw",
        "candidate_files_do_not_symlink_to_raw_or_processed",
        "no_current_asset_promotion_marker",
    }
    for batch in report["candidate_batches"]:
        checks = {item["check"]: item["passed"] for item in batch["checks"]}
        assert safety_checks.issubset(checks)
        assert all(checks[name] for name in safety_checks), batch


def test_conversion_qa_report_can_be_generated_without_promoting_assets() -> None:
    report = validate_conversion_outputs()
    write_report(report, DEFAULT_REPORT_PATH)

    assert DEFAULT_REPORT_PATH.exists()
    assert DEFAULT_REPORT_PATH.is_file()
    assert DEFAULT_REPORT_PATH.is_relative_to(PROJECT_ROOT / "data" / "validation" / "processing_reports")
    assert report["summary"]["comparison_11_count"] == 11
    assert report["summary"]["default_scope_34_count"] == 34
    assert all("data/processed" not in batch["root"] for batch in report["candidate_batches"])


def test_conversion_validator_flags_inf_and_missing_reports_for_candidate_fixture(tmp_path: Path) -> None:
    conversion_outputs = tmp_path / "data" / "conversion_outputs"
    validation = tmp_path / "data" / "validation"
    processed = tmp_path / "data" / "processed"
    raw = tmp_path / "data" / "raw"
    metadata = tmp_path / "data" / "metadata"
    candidate_dir = conversion_outputs / "fixture_source" / "fixture_dataset"
    candidate_dir.mkdir(parents=True)
    processed.mkdir(parents=True)
    raw.mkdir(parents=True)
    metadata.mkdir(parents=True)
    (validation / "processing_reports").mkdir(parents=True)
    (validation / "mismatch_reports").mkdir(parents=True)

    pd.DataFrame(
        {
            "학교명": COMPARISON_11[:10],
            "metric_value": ["1"] * 9 + ["inf"],
        }
    ).to_csv(candidate_dir / "fixture_dataset_candidate.csv", index=False)

    report = validate_conversion_outputs(
        conversion_outputs_dir=conversion_outputs,
        validation_dir=validation,
        processed_dir=processed,
        raw_dir=raw,
        metadata_dir=metadata,
    )

    failed_checks = {item["check"] for item in report["blockers"]}
    assert "source_metadata_exists" in failed_checks
    assert "processing_report_exists" in failed_checks
    assert "mismatch_report_exists" in failed_checks
    assert "no_inf_or_literal_inf" in failed_checks
    assert "comparison_11_coverage" in failed_checks
    assert "default_scope_34_coverage" in failed_checks


def test_conversion_outputs_directory_is_separate_from_operating_assets() -> None:
    assert CONVERSION_OUTPUTS_DIR != PROJECT_ROOT / "data" / "processed"
    assert CONVERSION_OUTPUTS_DIR != PROJECT_ROOT / "data" / "raw"
    assert CONVERSION_OUTPUTS_DIR.is_relative_to(PROJECT_ROOT / "data")
