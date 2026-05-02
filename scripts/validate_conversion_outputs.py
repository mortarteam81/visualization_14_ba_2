from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONVERSION_OUTPUTS_DIR = PROJECT_ROOT / "data" / "conversion_outputs"
VALIDATION_DIR = PROJECT_ROOT / "data" / "validation"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RAW_DIR = PROJECT_ROOT / "data" / "raw"
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
DEFAULT_REPORT_PATH = VALIDATION_DIR / "processing_reports" / "conversion_system_qa_report.json"
DEFAULT_SCOPE_PATH = METADATA_DIR / "analysis_scopes" / "seoul_private_four_year_universities.json"

COMPARISON_11 = [
    "성신여자대학교",
    "숙명여자대학교",
    "덕성여자대학교",
    "서울여자대학교",
    "동덕여자대학교",
    "이화여자대학교",
    "한성대학교",
    "서경대학교",
    "광운대학교",
    "세종대학교",
    "숭실대학교",
]

DATA_FILE_SUFFIXES = {".csv", ".tsv", ".xlsx", ".xls", ".json", ".jsonl", ".parquet"}
TABULAR_SUFFIXES = {".csv", ".tsv", ".xlsx", ".xls", ".parquet"}
CURRENT_MARKERS = ("current", "latest", "production")


@dataclass(frozen=True)
class CandidateBatch:
    dataset_id: str
    root: Path
    files: tuple[Path, ...]


def project_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def load_default_scope_names(scope_path: Path = DEFAULT_SCOPE_PATH) -> list[str]:
    payload = json.loads(scope_path.read_text(encoding="utf-8"))
    names = [str(item["school_name"]).strip() for item in payload.get("schools", [])]
    return [name for name in names if name]


def collect_candidate_batches(conversion_outputs_dir: Path = CONVERSION_OUTPUTS_DIR) -> list[CandidateBatch]:
    """Collect candidate output batches without assuming source-specific layouts.

    Supported layouts include both:
    - data/conversion_outputs/<dataset>/*
    - data/conversion_outputs/<source>/<dataset>/*
    """

    if not conversion_outputs_dir.exists():
        return []
    batches: list[CandidateBatch] = []
    seen_roots: set[Path] = set()
    for path in sorted(conversion_outputs_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in DATA_FILE_SUFFIXES:
            continue
        if _is_auxiliary_report_file(path):
            continue
        batch_root = _candidate_batch_root(path, conversion_outputs_dir)
        if batch_root in seen_roots:
            continue
        seen_roots.add(batch_root)
        files = tuple(
            sorted(
                item
                for item in batch_root.rglob("*")
                if item.is_file()
                and item.suffix.lower() in DATA_FILE_SUFFIXES
                and not _is_auxiliary_report_file(item)
            )
        )
        batches.append(CandidateBatch(dataset_id=batch_root.name, root=batch_root, files=files))
    return batches


def _candidate_batch_root(path: Path, conversion_outputs_dir: Path) -> Path:
    rel_parts = path.relative_to(conversion_outputs_dir).parts
    if len(rel_parts) >= 3:
        return conversion_outputs_dir / rel_parts[0] / rel_parts[1]
    if len(rel_parts) >= 2:
        return conversion_outputs_dir / rel_parts[0]
    return path.parent


def _is_auxiliary_report_file(path: Path) -> bool:
    lowered = path.name.lower()
    return any(token in lowered for token in ("metadata", "processing_report", "mismatch", "qa_report", "schema"))


def validate_conversion_outputs(
    *,
    conversion_outputs_dir: Path = CONVERSION_OUTPUTS_DIR,
    validation_dir: Path = VALIDATION_DIR,
    processed_dir: Path = PROCESSED_DIR,
    raw_dir: Path = RAW_DIR,
    metadata_dir: Path = METADATA_DIR,
) -> dict[str, Any]:
    default_scope_names = load_default_scope_names()
    batches = collect_candidate_batches(conversion_outputs_dir)
    checks: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    batch_reports: list[dict[str, Any]] = []

    _record_check(checks, "comparison_11_definition", len(COMPARISON_11) == 11, {"count": len(COMPARISON_11), "schools": COMPARISON_11}, blockers, severity="blocker")
    _record_check(checks, "default_scope_34_definition", len(default_scope_names) == 34, {"count": len(default_scope_names)}, blockers, severity="blocker")
    _record_check(
        checks,
        "comparison_11_subset_of_default_scope_34",
        set(COMPARISON_11).issubset(default_scope_names),
        {"missing_from_scope": sorted(set(COMPARISON_11) - set(default_scope_names))},
        blockers,
        severity="blocker",
    )

    if not conversion_outputs_dir.exists():
        warnings.append({"check": "candidate_outputs_present", "severity": "info", "message": "data/conversion_outputs does not exist yet; candidate-specific checks were skipped."})
    elif not batches:
        warnings.append({"check": "candidate_outputs_present", "severity": "info", "message": "No candidate data files found under data/conversion_outputs; candidate-specific checks were skipped."})

    for batch in batches:
        batch_reports.append(
            _validate_candidate_batch(
                batch,
                conversion_outputs_dir=conversion_outputs_dir,
                validation_dir=validation_dir,
                processed_dir=processed_dir,
                raw_dir=raw_dir,
                metadata_dir=metadata_dir,
                default_scope_names=default_scope_names,
                blockers=blockers,
                warnings=warnings,
            )
        )

    return {
        "report_id": "conversion_system_qa_report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(PROJECT_ROOT),
        "summary": {
            "candidate_batch_count": len(batches),
            "blocker_count": len(blockers),
            "warning_count": len(warnings),
            "comparison_11_count": len(COMPARISON_11),
            "default_scope_34_count": len(default_scope_names),
            "status": "pass" if not blockers else "fail",
        },
        "policy_checks": checks,
        "candidate_batches": batch_reports,
        "blockers": blockers,
        "warnings": warnings,
        "known_limitations": [
            "When no source-agent candidate outputs exist yet, this script validates shared scope/policy definitions and records candidate checks as skipped.",
            "raw-readonly is enforced here by path/symlink isolation checks; filesystem permission hardening is outside this script's scope.",
            "no-current-overwrite is checked by ensuring candidate outputs remain under data/conversion_outputs and do not symlink to data/processed/current-like assets.",
        ],
    }


def _record_check(checks: list[dict[str, Any]], name: str, passed: bool, details: dict[str, Any], blockers: list[dict[str, Any]], *, severity: str) -> None:
    checks.append({"check": name, "passed": passed, "details": details})
    if not passed:
        blockers.append({"check": name, "severity": severity, "details": details})


def _validate_candidate_batch(
    batch: CandidateBatch,
    *,
    conversion_outputs_dir: Path,
    validation_dir: Path,
    processed_dir: Path,
    raw_dir: Path,
    metadata_dir: Path,
    default_scope_names: list[str],
    blockers: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> dict[str, Any]:
    batch_checks: list[dict[str, Any]] = []
    data_files = [path for path in batch.files if path.suffix.lower() in TABULAR_SUFFIXES]
    source_metadata_files = _find_related_files(batch, metadata_dir, ("source",)) or _find_related_files(batch, metadata_dir, ("metadata",))
    processing_reports = _find_related_files(batch, validation_dir / "processing_reports", ("processing_report",))
    mismatch_reports = _find_related_files(batch, validation_dir / "mismatch_reports", ("mismatch",))

    _batch_check(batch_checks, blockers, batch, "candidate_files_under_conversion_outputs", all(_is_under(path, conversion_outputs_dir) for path in batch.files), {"files": [project_relative(path) for path in batch.files]})
    _batch_check(batch_checks, blockers, batch, "candidate_files_not_under_processed", all(not _is_under(path, processed_dir) for path in batch.files), {})
    _batch_check(batch_checks, blockers, batch, "candidate_files_not_under_raw", all(not _is_under(path, raw_dir) for path in batch.files), {})
    _batch_check(batch_checks, blockers, batch, "candidate_files_do_not_symlink_to_raw_or_processed", all(_safe_realpath(path, raw_dir, processed_dir) for path in batch.files), {})
    _batch_check(batch_checks, blockers, batch, "no_current_asset_promotion_marker", all(not _has_current_marker(path) for path in batch.files), {"markers": list(CURRENT_MARKERS)})
    _batch_check(batch_checks, blockers, batch, "source_metadata_exists", bool(source_metadata_files), {"matched_files": [project_relative(path) for path in source_metadata_files]})
    _batch_check(batch_checks, blockers, batch, "processing_report_exists", bool(processing_reports), {"matched_files": [project_relative(path) for path in processing_reports]})
    _batch_check(batch_checks, blockers, batch, "mismatch_report_exists", bool(mismatch_reports), {"matched_files": [project_relative(path) for path in mismatch_reports]})

    no_inf_details = _scan_no_inf(data_files)
    _batch_check(batch_checks, blockers, batch, "no_inf_or_literal_inf", not no_inf_details["findings"], no_inf_details)

    coverage_details = _scan_scope_coverage(data_files, default_scope_names)
    if coverage_details["files_with_school_names"] == 0:
        warnings.append({"check": "scope_coverage", "severity": "info", "dataset_id": batch.dataset_id, "message": "No tabular candidate with a recognizable school-name column was found."})
    else:
        _batch_check(batch_checks, blockers, batch, "comparison_11_coverage", coverage_details["best_comparison_11_count"] == 11, coverage_details)
        _batch_check(batch_checks, blockers, batch, "default_scope_34_coverage", coverage_details["best_default_scope_34_count"] == 34, coverage_details)

    return {"dataset_id": batch.dataset_id, "root": project_relative(batch.root), "file_count": len(batch.files), "checks": batch_checks}


def _batch_check(checks: list[dict[str, Any]], blockers: list[dict[str, Any]], batch: CandidateBatch, name: str, passed: bool, details: dict[str, Any]) -> None:
    checks.append({"check": name, "passed": passed, "details": details})
    if not passed:
        blockers.append({"check": name, "severity": "blocker", "dataset_id": batch.dataset_id, "root": project_relative(batch.root), "details": details})


def _is_under(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _safe_realpath(path: Path, raw_dir: Path, processed_dir: Path) -> bool:
    if not path.is_symlink():
        return True
    resolved = path.resolve()
    return not _is_under(resolved, raw_dir) and not _is_under(resolved, processed_dir)


def _has_current_marker(path: Path) -> bool:
    parts = [part.lower() for part in path.parts]
    return any(marker in part for part in parts for marker in CURRENT_MARKERS)


def _find_related_files(batch: CandidateBatch, external_dir: Path, tokens: tuple[str, ...]) -> list[Path]:
    candidates: list[Path] = []
    search_roots = [batch.root]
    if external_dir.exists():
        search_roots.append(external_dir)
    for root in search_roots:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            lowered = path.name.lower()
            dataset_token = batch.dataset_id.lower()
            if dataset_token in lowered and all(token in lowered for token in tokens):
                candidates.append(path)
            elif root == batch.root and all(token in lowered for token in tokens):
                candidates.append(path)
    return sorted(set(candidates))


def _scan_no_inf(paths: list[Path]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    scanned_files = 0
    for path in paths:
        try:
            frame = _read_table_sample(path)
        except Exception as exc:  # surfaced in report, not hidden
            findings.append({"file": project_relative(path), "error": f"read_failed: {exc}"})
            continue
        scanned_files += 1
        for column in frame.columns:
            series = frame[column]
            literal_mask = series.astype(str).str.strip().str.lower().isin({"inf", "+inf", "-inf", "infinity", "+infinity", "-infinity"})
            numeric = pd.to_numeric(series, errors="coerce")
            numeric_inf_mask = numeric.map(lambda value: isinstance(value, (int, float)) and math.isinf(float(value)))
            count = int((literal_mask | numeric_inf_mask).sum())
            if count:
                findings.append({"file": project_relative(path), "column": str(column), "count": count})
    return {"scanned_files": scanned_files, "findings": findings}


def _scan_scope_coverage(paths: list[Path], default_scope_names: list[str]) -> dict[str, Any]:
    per_file: list[dict[str, Any]] = []
    default_scope = set(default_scope_names)
    comparison = set(COMPARISON_11)
    for path in paths:
        try:
            frame = _read_table_sample(path)
        except Exception:
            continue
        school_column = _find_school_column(frame)
        if school_column is None:
            continue
        schools = set(frame[school_column].dropna().astype(str).str.strip())
        per_file.append(
            {
                "file": project_relative(path),
                "school_column": school_column,
                "comparison_11_count": len(schools & comparison),
                "default_scope_34_count": len(schools & default_scope),
                "missing_comparison_11": sorted(comparison - schools),
                "missing_default_scope_34": sorted(default_scope - schools),
            }
        )
    return {
        "files_with_school_names": len(per_file),
        "best_comparison_11_count": max((item["comparison_11_count"] for item in per_file), default=0),
        "best_default_scope_34_count": max((item["default_scope_34_count"] for item in per_file), default=0),
        "per_file": per_file,
    }


def _read_table_sample(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path, dtype=str, nrows=20000)
    if suffix == ".tsv":
        return pd.read_csv(path, sep="\t", dtype=str, nrows=20000)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path, dtype=str, nrows=20000)
    if suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.DataFrame()


def _find_school_column(frame: pd.DataFrame) -> str | None:
    for column in ("학교명", "학교", "대학명", "school_name", "lst_kor_schl_nm"):
        if column in frame.columns:
            return column
    return None


def write_report(report: dict[str, Any], output_path: Path = DEFAULT_REPORT_PATH) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate raw-source conversion candidate outputs.")
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--strict", action="store_true", help="Return non-zero when blocker checks fail.")
    args = parser.parse_args()

    report = validate_conversion_outputs()
    write_report(report, args.output)
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    return 1 if args.strict and report["summary"]["blocker_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
