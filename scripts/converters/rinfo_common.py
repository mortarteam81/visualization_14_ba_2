"""Shared helpers for RINFO processed-to-candidate standardizers.

The repository currently keeps only README placeholders for the RINFO raw XLS/XLSX
files.  These helpers therefore do **not** claim raw-source verification; they
standardize the existing processed CSVs into review-only candidate outputs,
remove/display-flag infinite metrics, apply the explicit 34-school scope, and
write validation artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCOPE_PATH = PROJECT_ROOT / "data" / "metadata" / "analysis_scopes" / "seoul_private_four_year_universities.json"
OUTPUT_ROOT = PROJECT_ROOT / "data" / "conversion_outputs" / "rinfo"
PROCESSING_REPORT_DIR = PROJECT_ROOT / "data" / "validation" / "processing_reports"
MISMATCH_REPORT_DIR = PROJECT_ROOT / "data" / "validation" / "mismatch_reports"

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

RISK_SCHOOLS = (
    "가톨릭대학교",
    "건국대학교",
    "건국대학교(글로컬)",
    "고려대학교",
    "고려대학교(세종)",
    "동국대학교",
    "동국대학교(WISE)",
    "연세대학교",
    "연세대학교(미래)",
    "한양대학교",
    "한양대학교(ERICA)",
    "강서대학교",
    "케이씨대학교",
    "그리스도대학교",
    "서울한영대학교",
    "한영신학대학교",
)

RAW_GAP_NOTE = (
    "RINFO 원본 xls/xlsx가 repo에 보존되어 있지 않거나 README 수준이므로 "
    "원자료 직접 대조는 수행하지 않았다. 이 산출물은 processed CSV를 입력으로 한 "
    "candidate 재표준화/산식검증/no-inf/scope 검증 결과다."
)


@dataclass(frozen=True)
class RinfoConfig:
    dataset_id: str
    input_path: Path
    raw_dir: Path
    output_dir: Path
    report_path: Path
    mismatch_path: Path
    metric_col: str
    denominator_col: str
    total_col: str | None = None
    output_prefix: str = "candidate"


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return relative(value)
    if pd.isna(value):
        return None
    return value


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=json_default) + "\n",
        encoding="utf-8",
    )


def load_scope(path: Path = SCOPE_PATH) -> tuple[set[str], dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    schools = {str(item["school_name"]).strip() for item in payload.get("schools", [])}
    id_map = {str(item["school_name"]).strip(): str(item.get("school_id", "")).zfill(7) for item in payload.get("schools", [])}
    return schools, id_map


def raw_source_profile(raw_dir: Path) -> dict[str, Any]:
    existing_files = sorted(p for p in raw_dir.glob("**/*") if p.is_file()) if raw_dir.exists() else []
    tabular_raw = [p for p in existing_files if p.suffix.lower() in {".xls", ".xlsx", ".csv"}]
    return {
        "raw_dir": relative(raw_dir),
        "raw_dir_exists": raw_dir.exists(),
        "file_count": len(existing_files),
        "files": [relative(p) for p in existing_files],
        "xls_xlsx_csv_count": len(tabular_raw),
        "xls_xlsx_csv_files": [relative(p) for p in tabular_raw],
        "source_preservation_status": "gap" if not tabular_raw else "present_but_not_used_by_candidate_standardizer",
        "limitation": RAW_GAP_NOTE,
    }


def read_processed_csv(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if "university_name" in frame.columns:
        frame["university_name"] = frame["university_name"].astype(str).str.strip()
    return frame


def numeric_series(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(frame[column].astype(str).str.replace(",", "", regex=False), errors="coerce")


def add_common_candidate_fields(frame: pd.DataFrame, config: RinfoConfig, school_id_map: dict[str, str]) -> pd.DataFrame:
    candidate = frame.copy()
    candidate[config.metric_col] = numeric_series(candidate, config.metric_col).replace([math.inf, -math.inf], pd.NA)
    candidate[config.denominator_col] = numeric_series(candidate, config.denominator_col)
    candidate["metric_calc_status"] = "ok"
    candidate.loc[candidate[config.denominator_col] == 0, "metric_calc_status"] = "not_calculable_zero_denominator"
    candidate.loc[candidate[config.metric_col].isna(), "metric_calc_status"] = "not_calculable_or_missing"
    candidate["metric_value_was_infinite_or_invalid"] = candidate[config.metric_col].isna() & (
        candidate["metric_calc_status"] != "ok"
    )
    candidate["scope_school_id"] = candidate["university_name"].map(school_id_map).fillna("")
    candidate["is_scope34_exact"] = candidate["scope_school_id"] != ""
    candidate["is_comparison11"] = candidate["university_name"].isin(COMPARISON_SCHOOLS)
    candidate["standardization_source"] = "processed_csv_candidate_not_raw_verified"
    return candidate


def write_candidate_csvs(config: RinfoConfig, candidate: pd.DataFrame) -> dict[str, Path]:
    config.output_dir.mkdir(parents=True, exist_ok=True)
    all_path = config.output_dir / f"{config.output_prefix}_all_no_inf.csv"
    scope_path = config.output_dir / f"{config.output_prefix}_scope34_no_inf.csv"
    candidate.to_csv(all_path, index=False, encoding="utf-8-sig")
    candidate[candidate["is_scope34_exact"]].to_csv(scope_path, index=False, encoding="utf-8-sig")
    return {"all_candidate": all_path, "scope34_candidate": scope_path}


def build_coverage_report(config: RinfoConfig, candidate: pd.DataFrame, scope_names: set[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for group_name, names in [
        ("comparison11", COMPARISON_SCHOOLS),
        ("risk_schools", RISK_SCHOOLS),
        ("scope34", tuple(sorted(scope_names))),
    ]:
        for school in names:
            school_rows = candidate[candidate["university_name"] == school]
            years = sorted(pd.to_numeric(school_rows.get("reference_year"), errors="coerce").dropna().astype(int).unique()) if not school_rows.empty else []
            rows.append(
                {
                    "dataset_id": config.dataset_id,
                    "coverage_group": group_name,
                    "school_name": school,
                    "present_in_processed": bool(not school_rows.empty),
                    "present_in_scope34_exact": bool(school in scope_names),
                    "row_count": int(len(school_rows)),
                    "year_min": min(years) if years else pd.NA,
                    "year_max": max(years) if years else pd.NA,
                    "year_count": len(years),
                    "note": "alias/old-name absent in processed" if school_rows.empty and group_name == "risk_schools" else "",
                }
            )
    coverage = pd.DataFrame(rows)
    coverage_path = MISMATCH_REPORT_DIR / f"rinfo_{config.dataset_id}_coverage.csv"
    coverage_path.parent.mkdir(parents=True, exist_ok=True)
    coverage.to_csv(coverage_path, index=False, encoding="utf-8-sig")
    return coverage


def simple_scope_leakage(frame: pd.DataFrame, scope_names: set[str]) -> list[str]:
    simple = frame[
        (frame["region_name"].astype(str).str.strip() == "서울")
        & (frame["founding_type"].astype(str).str.strip() == "사립")
        & (frame["school_type"].astype(str).str.strip() == "대학")
        & (~frame["university_name"].astype(str).str.contains("_", regex=False))
    ]
    return sorted(set(simple["university_name"].dropna().astype(str)) - scope_names)


def base_report(config: RinfoConfig, source: pd.DataFrame, candidate: pd.DataFrame, scope_names: set[str], outputs: dict[str, Path], coverage: pd.DataFrame, mismatch_count: int, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    scope_candidate = candidate[candidate["is_scope34_exact"]]
    report: dict[str, Any] = {
        "dataset_id": config.dataset_id,
        "status": "partial_source_gap_candidate_generated",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input": {
            "processed_csv": relative(config.input_path),
            "processed_sha256": sha256_file(config.input_path),
            "raw_source_profile": raw_source_profile(config.raw_dir),
        },
        "outputs": {key: relative(path) for key, path in outputs.items()},
        "limitations": [RAW_GAP_NOTE],
        "row_counts": {
            "processed_input_rows": int(len(source)),
            "candidate_all_rows": int(len(candidate)),
            "candidate_scope34_rows": int(len(scope_candidate)),
            "candidate_scope34_school_count": int(scope_candidate["university_name"].nunique()),
        },
        "year_range": {
            "min": int(pd.to_numeric(candidate["reference_year"], errors="coerce").min()),
            "max": int(pd.to_numeric(candidate["reference_year"], errors="coerce").max()),
        },
        "no_inf_policy": {
            "metric_column": config.metric_col,
            "zero_or_invalid_denominator_column": config.denominator_col,
            "policy": "replace +/-inf with null metric value and flag metric_calc_status",
            "remaining_inf_count": int(pd.to_numeric(candidate[config.metric_col], errors="coerce").isin([math.inf, -math.inf]).sum()),
            "not_calculable_or_missing_count": int((candidate["metric_calc_status"] != "ok").sum()),
        },
        "scope_validation": {
            "scope_manifest": relative(SCOPE_PATH),
            "scope_manifest_school_count": len(scope_names),
            "scope34_missing_schools": sorted(scope_names - set(scope_candidate["university_name"])),
            "simple_filter_extra_schools_excluded_by_exact_scope": simple_scope_leakage(source, scope_names),
            "comparison11_present_count": int(coverage[(coverage["coverage_group"] == "comparison11") & (coverage["present_in_processed"] == True)].shape[0]),
        },
        "formula_mismatch_count": int(mismatch_count),
        "mismatch_report": relative(config.mismatch_path),
        "coverage_report": relative(MISMATCH_REPORT_DIR / f"rinfo_{config.dataset_id}_coverage.csv"),
    }
    if extra:
        report.update(extra)
    return report


def parse_args(description: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--write", action="store_true", help="write candidate CSV and validation artifacts")
    return parser.parse_args()
