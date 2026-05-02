"""Shared helpers for offline AcademyInfo candidate converters.

These helpers keep raw sources read-only and write all generated artifacts under
candidate/validation paths.  They are intentionally conservative: when original
XLSX files are absent, converters report a source-preservation gap and only
re-standardize already processed local assets.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from utils.school_normalization import (
    canonicalize_school_name_column,
    normalize_school_code,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = PROJECT_ROOT / "data" / "conversion_outputs" / "academyinfo"
REPORT_DIR = PROJECT_ROOT / "data" / "validation" / "processing_reports"
MISMATCH_DIR = PROJECT_ROOT / "data" / "validation" / "mismatch_reports"
DEFAULT_SCOPE_PATH = (
    PROJECT_ROOT
    / "data"
    / "metadata"
    / "analysis_scopes"
    / "seoul_private_four_year_universities.json"
)
ACADEMYINFO_URL = "https://academyinfo.go.kr/main/main0830/main0830.do"
MISMATCH_COLUMNS = (
    "severity",
    "field",
    "school_name",
    "year",
    "processed_value",
    "raw_value",
    "reason",
    "source_path",
)

COMPARISON_SCHOOLS = (
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
)


@dataclass(frozen=True)
class AcademyInfoDatasetConfig:
    dataset_id: str
    dataset_name_ko: str
    source_section: str
    source_processed_path: Path
    candidate_filename: str
    transform: Callable[[pd.DataFrame], pd.DataFrame]
    expected_raw_files: tuple[Path, ...] = ()
    source_metadata_path: Path | None = None
    input_encoding: str = "utf-8-sig"
    source_input_path: Path | None = None
    source_input_kind: str = "processed_csv"
    version: str = "academyinfo_candidate_processed_restandardized"
    input_loader: Callable[[Any], pd.DataFrame] | None = None
    mismatch_builder: Callable[[pd.DataFrame, pd.DataFrame, Any], pd.DataFrame] | None = None


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_default_scope() -> dict[str, Any]:
    with DEFAULT_SCOPE_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def default_scope_school_names() -> set[str]:
    return {str(school["school_name"]).strip() for school in load_default_scope().get("schools", [])}


def read_processed_csv(path: Path, *, encoding: str = "utf-8-sig") -> pd.DataFrame:
    return pd.read_csv(path, encoding=encoding, dtype=str)


def mismatch_frame(rows: list[dict[str, Any]] | None = None) -> pd.DataFrame:
    return pd.DataFrame(rows or [], columns=MISMATCH_COLUMNS)


def combine_mismatch_frames(frames: list[pd.DataFrame]) -> pd.DataFrame:
    nonempty = [frame for frame in frames if frame is not None and not frame.empty]
    if not nonempty:
        return mismatch_frame()
    return pd.concat(nonempty, ignore_index=True).reindex(columns=MISMATCH_COLUMNS)


def normalize_identifier_columns(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    for column in ("representative_school_code", "school_code", "대표학교코드", "학교코드"):
        if column in result.columns:
            result[column] = result[column].map(normalize_school_code)
    return result


def canonicalize_university_column(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    if "university_name" in result.columns and "school_name_canonical" not in result.columns:
        tmp = result.rename(columns={"university_name": "학교명"})
        tmp = canonicalize_school_name_column(tmp, school_col="학교명", restrict_to_default_scope=False)
        result["school_name_canonical"] = tmp["학교명"]
    elif "학교명" in result.columns:
        result = canonicalize_school_name_column(result, school_col="학교명", restrict_to_default_scope=False)
    return result


def coverage_summary(candidate: pd.DataFrame, *, school_col: str = "학교명", year_col: str = "기준년도") -> dict[str, Any]:
    scope_names = default_scope_school_names()
    comparison_names = set(COMPARISON_SCHOOLS)
    if candidate.empty or school_col not in candidate.columns:
        years: list[int] = []
        latest_year = None
        present_latest: set[str] = set()
        all_present: set[str] = set()
    else:
        years = sorted(pd.to_numeric(candidate.get(year_col), errors="coerce").dropna().astype(int).unique().tolist()) if year_col in candidate.columns else []
        latest_year = years[-1] if years else None
        all_present = set(candidate[school_col].dropna().astype(str).str.strip())
        if latest_year is not None and year_col in candidate.columns:
            latest_mask = pd.to_numeric(candidate[year_col], errors="coerce") == latest_year
            present_latest = set(candidate.loc[latest_mask, school_col].dropna().astype(str).str.strip())
        else:
            present_latest = all_present

    return {
        "comparison_11_expected": len(COMPARISON_SCHOOLS),
        "comparison_11_present_any_year": len(comparison_names & all_present),
        "comparison_11_missing_any_year": sorted(comparison_names - all_present),
        "default_scope_34_expected": int(load_default_scope().get("school_count", 34)),
        "default_scope_34_present_any_year": len(scope_names & all_present),
        "default_scope_34_missing_any_year": sorted(scope_names - all_present),
        "years": years,
        "latest_year": latest_year,
        "comparison_11_present_latest_year": len(comparison_names & present_latest),
        "comparison_11_missing_latest_year": sorted(comparison_names - present_latest),
        "default_scope_34_present_latest_year": len(scope_names & present_latest),
        "default_scope_34_missing_latest_year": sorted(scope_names - present_latest),
    }


def source_file_inventory(config: AcademyInfoDatasetConfig) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    for path in (config.source_processed_path, *config.expected_raw_files):
        files.append(
            {
                "path": str(path.relative_to(PROJECT_ROOT)),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() and path.is_file() else None,
                "kind": "processed_input" if path == config.source_processed_path else "expected_raw_source",
            }
        )
    if config.source_metadata_path is not None:
        path = config.source_metadata_path
        files.append(
            {
                "path": str(path.relative_to(PROJECT_ROOT)),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() and path.is_file() else None,
                "kind": "source_metadata",
            }
        )
    return files


def build_gap_mismatches(config: AcademyInfoDatasetConfig) -> pd.DataFrame:
    rows = []
    for path in config.expected_raw_files:
        if not path.exists():
            rows.append(
                {
                    "severity": "medium",
                    "field": "raw_source_file",
                    "school_name": None,
                    "year": None,
                    "processed_value": None,
                    "raw_value": None,
                    "reason": "expected original AcademyInfo XLSX is not preserved locally; converter performed processed-to-candidate re-standardization only",
                    "source_path": str(path.relative_to(PROJECT_ROOT)),
                }
            )
    return mismatch_frame(rows)


def load_source_frame(config: AcademyInfoDatasetConfig) -> pd.DataFrame:
    if config.input_loader is not None:
        frame = config.input_loader(config)
    else:
        frame = read_processed_csv(config.source_processed_path, encoding=config.input_encoding)
    return canonicalize_university_column(normalize_identifier_columns(frame))


def write_candidate_outputs(config: AcademyInfoDatasetConfig) -> dict[str, Any]:
    output_dir = OUTPUT_ROOT / config.dataset_id
    output_dir.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    MISMATCH_DIR.mkdir(parents=True, exist_ok=True)

    source_frame = load_source_frame(config)
    candidate = config.transform(source_frame)

    candidate_path = output_dir / config.candidate_filename
    metadata_path = output_dir / f"{config.dataset_id}.source.json"
    local_report_path = output_dir / f"{config.dataset_id}.processing_report.json"
    validation_report_path = REPORT_DIR / f"academyinfo_{config.dataset_id}.processing_report.json"
    mismatch_path = MISMATCH_DIR / f"academyinfo_{config.dataset_id}.mismatch.csv"

    coverage = coverage_summary(candidate)
    mismatch_batches = [build_gap_mismatches(config)]
    if config.mismatch_builder is not None:
        mismatch_batches.append(config.mismatch_builder(source_frame, candidate, config))
    mismatches = combine_mismatch_frames(mismatch_batches)
    source_gap = any(item["kind"] == "expected_raw_source" and not item["exists"] for item in source_file_inventory(config))
    timestamp = now_utc()
    input_path = config.source_input_path or config.source_processed_path

    candidate.to_csv(candidate_path, index=False, encoding="utf-8-sig")
    mismatches.to_csv(mismatch_path, index=False, encoding="utf-8-sig")

    source_payload = {
        "dataset_id": config.dataset_id,
        "dataset_name_ko": config.dataset_name_ko,
        "source_name": "대학알리미",
        "source_org": "한국대학교육협의회",
        "source_url": ACADEMYINFO_URL,
        "source_section": config.source_section,
        "processed_at": timestamp,
        "source_preservation_status": "gap_original_xlsx_missing" if source_gap else "raw_preserved",
        "source_input_kind": config.source_input_kind,
        "source_input_file": str(input_path.relative_to(PROJECT_ROOT)),
        "files": source_file_inventory(config),
        "notes": [
            "No official-site mass download was performed.",
            "Existing processed/current assets were not overwritten or promoted.",
        ],
    }
    metadata_path.write_text(json.dumps(source_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    report = {
        "dataset_id": config.dataset_id,
        "dataset_name_ko": config.dataset_name_ko,
        "version": config.version,
        "processed_at": timestamp,
        "source_url": ACADEMYINFO_URL,
        "source_section": config.source_section,
        "source_preservation_status": source_payload["source_preservation_status"],
        "source_input_kind": config.source_input_kind,
        "input_file": str(input_path.relative_to(PROJECT_ROOT)),
        "output_file": str(candidate_path.relative_to(PROJECT_ROOT)),
        "metadata_file": str(metadata_path.relative_to(PROJECT_ROOT)),
        "mismatch_report": str(mismatch_path.relative_to(PROJECT_ROOT)),
        "row_counts": {
            "source_input_rows": int(len(source_frame)),
            "candidate_rows": int(len(candidate)),
            "mismatch_rows": int(len(mismatches)),
        },
        "coverage": coverage,
        "mismatch_summary": {
            "total": int(len(mismatches)),
            "high": int((mismatches.get("severity") == "high").sum()) if not mismatches.empty else 0,
            "medium": int((mismatches.get("severity") == "medium").sum()) if not mismatches.empty else 0,
        },
        "known_limitations": [
            "Original AcademyInfo XLSX was not available under data/raw for this dataset; source-value parity cannot be declared.",
            "This run only re-standardizes and validates the existing processed local asset into a separate candidate output path.",
            "Promotion to current dashboard assets requires explicit review/approval.",
        ] if source_gap else [
            "This run writes candidate artifacts only and does not promote them to current dashboard assets.",
        ],
    }
    report_json = json.dumps(report, ensure_ascii=False, indent=2)
    local_report_path.write_text(report_json, encoding="utf-8")
    validation_report_path.write_text(report_json, encoding="utf-8")
    return report
