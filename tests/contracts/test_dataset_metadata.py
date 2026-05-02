from __future__ import annotations

import json
from pathlib import Path

import pytest

from registry import (
    DatasetManifest,
    METRIC_REGISTRY,
    get_dataset_manifest,
    get_metric_manifest,
    list_dataset_manifests,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_FIELDS = {
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
SOURCE_DATA_SCOPES = {
    "seoul_subset_legacy",
    "national_raw",
    "national_processed",
    "kcue_processed",
    "faculty_processed",
}
VERIFICATION_STATUSES = {
    "verified",
    "partial",
    "needs_source_check",
    "legacy_schema_missing",
}
METADATA_FILE_KEYS = {"source", "schema", "report", "guide"}


@pytest.fixture(scope="module")
def manifests() -> list[DatasetManifest]:
    return list_dataset_manifests()


def test_dataset_manifests_cover_all_implemented_metrics(manifests: list[DatasetManifest]) -> None:
    manifest_metric_ids = {
        metric_id for manifest in manifests for metric_id in manifest.metric_ids
    }
    implemented_metric_ids = {
        metric.id for metric in METRIC_REGISTRY.values() if metric.implemented
    }

    assert manifest_metric_ids == implemented_metric_ids
    assert get_dataset_manifest("gyeolsan").metric_ids == ("tuition", "donation")


def test_dataset_manifest_required_fields_and_enums(
    manifests: list[DatasetManifest],
) -> None:
    for manifest in manifests:
        raw = json.loads(manifest.manifest_path.read_text(encoding="utf-8"))
        assert REQUIRED_FIELDS <= set(raw)
        assert REQUIRED_FIELDS <= set(manifest.__dataclass_fields__)
        assert manifest.dataset_key
        assert manifest.metric_ids
        assert manifest.title
        assert manifest.current_asset
        assert manifest.source_data_scope in SOURCE_DATA_SCOPES
        assert manifest.verification_status in VERIFICATION_STATUSES
        assert manifest.default_analysis_scope
        assert set(manifest.metadata_files) == METADATA_FILE_KEYS
        assert all(value is None or isinstance(value, str) for value in manifest.metadata_files.values())
        assert isinstance(manifest.quality_flags, tuple)
        assert isinstance(manifest.backlog, tuple)


def test_dataset_manifest_status_values_match_known_data_scopes() -> None:
    expected = {
        "budam": ("seoul_subset_legacy", "partial"),
        "gyowon": ("seoul_subset_legacy", "partial"),
        "research": ("seoul_subset_legacy", "partial"),
        "paper": ("seoul_subset_legacy", "partial"),
        "jirosung": ("national_raw", "partial"),
        "gyeolsan": ("national_raw", "legacy_schema_missing"),
        "education_return": ("national_processed", "partial"),
        "dormitory_rate": ("national_processed", "partial"),
        "lecturer_pay": ("national_processed", "partial"),
        "library_material_purchase_per_student": ("national_processed", "partial"),
        "library_staff_per_1000_students": ("national_processed", "partial"),
        "staff_per_student": ("kcue_processed", "verified"),
        "corp_transfer_ratio": ("kcue_processed", "verified"),
        "scholarship_ratio": ("kcue_processed", "partial"),
        "adjunct_faculty": ("faculty_processed", "partial"),
        "fulltime_adjunct_faculty": ("faculty_processed", "partial"),
        "faculty_securing_reference": ("faculty_processed", "partial"),
    }

    actual = {
        manifest.dataset_key: (manifest.source_data_scope, manifest.verification_status)
        for manifest in list_dataset_manifests()
    }
    assert actual == expected


def test_current_assets_and_metadata_file_paths_exist(
    manifests: list[DatasetManifest],
) -> None:
    for manifest in manifests:
        assert (PROJECT_ROOT / manifest.current_asset).exists(), manifest.current_asset

        for metadata_path in manifest.metadata_files.values():
            if metadata_path is None:
                continue
            assert (PROJECT_ROOT / metadata_path).exists(), metadata_path


def test_metric_registry_links_to_dataset_manifest(
    manifests: list[DatasetManifest],
) -> None:
    manifests_by_dataset = {manifest.dataset_key: manifest for manifest in manifests}

    for metric in METRIC_REGISTRY.values():
        if not metric.implemented:
            continue

        manifest = get_metric_manifest(metric.id)
        assert manifests_by_dataset[metric.dataset_key] == manifest
        assert metric.id in manifest.metric_ids
        assert all(
            METRIC_REGISTRY[metric_id].dataset_key == manifest.dataset_key
            for metric_id in manifest.metric_ids
        )
