"""Dataset-level metadata manifest loader.

This module is intentionally free of Streamlit dependencies so contracts,
scripts, and non-UI services can inspect dataset provenance.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from .metadata import METRIC_REGISTRY


PROJECT_ROOT: Final = Path(__file__).resolve().parents[1]
MANIFEST_DIR: Final = PROJECT_ROOT / "data" / "metadata" / "datasets"

SOURCE_DATA_SCOPES: Final[frozenset[str]] = frozenset(
    {
        "seoul_subset_legacy",
        "national_raw",
        "national_processed",
        "kcue_processed",
        "faculty_processed",
    }
)
VERIFICATION_STATUSES: Final[frozenset[str]] = frozenset(
    {
        "verified",
        "partial",
        "needs_source_check",
        "legacy_schema_missing",
    }
)
METADATA_FILE_KEYS: Final[tuple[str, ...]] = ("source", "schema", "report", "guide")
REQUIRED_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "dataset_key",
        "metric_ids",
        "title",
        "current_asset",
        "source_data_scope",
        "verification_status",
        "default_analysis_scope",
        "metadata_files",
        "quality_flags",
        "backlog",
    }
)


@dataclass(frozen=True)
class DatasetManifest:
    dataset_key: str
    metric_ids: tuple[str, ...]
    title: str
    current_asset: str
    source_data_scope: str
    verification_status: str
    default_analysis_scope: str
    metadata_files: dict[str, str | None]
    quality_flags: tuple[str, ...]
    backlog: tuple[str, ...]
    manifest_path: Path


def _require_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_string_tuple(value: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{field_name} must be a non-empty list")
    if not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{field_name} must contain non-empty strings")
    return tuple(value)


def _require_nullable_metadata_files(value: Any) -> dict[str, str | None]:
    if not isinstance(value, dict):
        raise ValueError("metadata_files must be an object")
    if set(value) != set(METADATA_FILE_KEYS):
        expected = ", ".join(METADATA_FILE_KEYS)
        raise ValueError(f"metadata_files must contain exactly: {expected}")

    result: dict[str, str | None] = {}
    for key in METADATA_FILE_KEYS:
        path_value = value[key]
        if path_value is not None and not isinstance(path_value, str):
            raise ValueError(f"metadata_files.{key} must be a string or null")
        result[key] = path_value
    return result


def _validate_manifest_paths(manifest: DatasetManifest) -> None:
    if not (PROJECT_ROOT / manifest.current_asset).exists():
        raise ValueError(
            f"{manifest.dataset_key} current_asset does not exist: {manifest.current_asset}"
        )

    for key, relative_path in manifest.metadata_files.items():
        if relative_path is None:
            continue
        if not (PROJECT_ROOT / relative_path).exists():
            raise ValueError(
                f"{manifest.dataset_key} metadata_files.{key} does not exist: {relative_path}"
            )


def _manifest_from_dict(raw: dict[str, Any], manifest_path: Path) -> DatasetManifest:
    missing = REQUIRED_FIELDS - set(raw)
    if missing:
        missing_fields = ", ".join(sorted(missing))
        raise ValueError(f"{manifest_path.name} is missing fields: {missing_fields}")

    source_data_scope = _require_string(raw["source_data_scope"], "source_data_scope")
    if source_data_scope not in SOURCE_DATA_SCOPES:
        raise ValueError(f"Unknown source_data_scope: {source_data_scope}")

    verification_status = _require_string(raw["verification_status"], "verification_status")
    if verification_status not in VERIFICATION_STATUSES:
        raise ValueError(f"Unknown verification_status: {verification_status}")

    manifest = DatasetManifest(
        dataset_key=_require_string(raw["dataset_key"], "dataset_key"),
        metric_ids=_require_string_tuple(raw["metric_ids"], "metric_ids"),
        title=_require_string(raw["title"], "title"),
        current_asset=_require_string(raw["current_asset"], "current_asset"),
        source_data_scope=source_data_scope,
        verification_status=verification_status,
        default_analysis_scope=_require_string(
            raw["default_analysis_scope"], "default_analysis_scope"
        ),
        metadata_files=_require_nullable_metadata_files(raw["metadata_files"]),
        quality_flags=_require_string_tuple(raw["quality_flags"], "quality_flags"),
        backlog=tuple(raw["backlog"]) if isinstance(raw["backlog"], list) else (),
        manifest_path=manifest_path,
    )
    if not isinstance(raw["backlog"], list) or not all(
        isinstance(item, str) for item in raw["backlog"]
    ):
        raise ValueError("backlog must be a list of strings")

    _validate_manifest_paths(manifest)
    return manifest


def _load_manifest_file(manifest_path: Path) -> DatasetManifest:
    with manifest_path.open(encoding="utf-8") as manifest_file:
        raw = json.load(manifest_file)
    if not isinstance(raw, dict):
        raise ValueError(f"{manifest_path.name} must contain a JSON object")
    return _manifest_from_dict(raw, manifest_path)


def list_dataset_manifests() -> list[DatasetManifest]:
    manifests = [_load_manifest_file(path) for path in sorted(MANIFEST_DIR.glob("*.metadata.json"))]
    dataset_keys = [manifest.dataset_key for manifest in manifests]
    if len(dataset_keys) != len(set(dataset_keys)):
        raise ValueError("Duplicate dataset_key values in dataset metadata manifests")
    return manifests


def get_dataset_manifest(dataset_key: str) -> DatasetManifest:
    for manifest in list_dataset_manifests():
        if manifest.dataset_key == dataset_key:
            return manifest
    raise KeyError(dataset_key)


def get_metric_manifest(metric_id: str) -> DatasetManifest:
    metric = METRIC_REGISTRY[metric_id]
    manifest = get_dataset_manifest(metric.dataset_key)
    if metric_id not in manifest.metric_ids:
        raise ValueError(
            f"Metric {metric_id!r} is registered to dataset {metric.dataset_key!r} "
            "but is missing from that dataset manifest"
        )
    return manifest
