from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from utils.config import DATA_UPDATED


_STATUS_LABELS = {
    "verified": "검증 완료",
    "partial": "부분 검증",
    "needs_source_check": "출처 확인 필요",
    "legacy_schema_missing": "기존 자료/스키마 보강 필요",
    "validated": "검증 완료",
    "processed": "가공 검증 완료",
    "legacy": "기존 자료",
    "pending": "검증 대기",
    "unverified": "검증 필요",
}
_SCOPE_LABELS = {
    "seoul_subset_legacy": "서울 subset legacy CSV",
    "national_raw": "전국 원자료",
    "national_processed": "전국 원자료/가공 CSV",
    "kcue_processed": "평가용 2차 집계자료/가공 CSV",
    "faculty_processed": "평가용 2차 집계자료/가공 CSV",
}

_FACULTY_METRIC_IDS = {
    "adjunct_faculty",
    "fulltime_adjunct_faculty",
    "faculty_securing_reference",
}
_KCUE_METRIC_IDS = {
    "corp_transfer_ratio",
    "staff_per_student",
    "scholarship_ratio",
}


def format_source_caption(metric_or_manifest: object) -> str:
    """Return the source caption text without invoking Streamlit."""

    manifest = _as_manifest(metric_or_manifest)
    source_label = _field_label(
        manifest,
        "source_label",
        "source_name",
        "source_org",
        default=_fallback_source_label(metric_or_manifest),
    )
    scope_label = _field_label(
        manifest,
        "source_data_scope",
        "source_data_scope_label",
        "data_scope",
        "scope",
        default=_fallback_scope_label(metric_or_manifest),
    )
    status_label = _status_label(
        _field_value(
            manifest,
            "verification_status",
            "validation_status",
            "validation_status_label",
            "status",
            "status_label",
        )
        or _fallback_status(metric_or_manifest)
    )
    updated_at = _field_label(
        manifest,
        "updated_at",
        "data_updated",
        "processed_at",
        "downloaded_at",
        default=DATA_UPDATED,
    )

    parts = [
        f"데이터 출처: {source_label}",
        f"자료 범위: {scope_label}",
        f"검증 상태: {status_label}",
    ]
    if updated_at:
        parts.append(f"업데이트: {updated_at}")
    return " | ".join(parts)


def render_source_caption(metric_or_manifest: object) -> None:
    import streamlit as st

    st.caption(format_source_caption(metric_or_manifest))


def _as_manifest(value: object) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value

    resolved = _resolve_dataset_manifest(value)
    if resolved:
        return resolved

    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)

    for attr in ("source_manifest", "manifest", "metadata"):
        nested = getattr(value, attr, None)
        if isinstance(nested, Mapping):
            return nested
    return {}


def _field_value(manifest: Mapping[str, Any], *keys: str) -> object | None:
    for key in keys:
        if key not in manifest:
            continue
        value = manifest[key]
        if value in (None, ""):
            continue
        return value
    return None


def _field_label(manifest: Mapping[str, Any], *keys: str, default: str) -> str:
    value = _field_value(manifest, *keys)
    label = _label_from_value(value, default=default)
    if keys and keys[0] == "source_data_scope":
        return _SCOPE_LABELS.get(label, label)
    return label


def _label_from_value(value: object, *, default: str) -> str:
    if isinstance(value, Mapping):
        label = _field_value(value, "label", "ko", "name", "value")
        return str(label) if label not in (None, "") else default
    if value in (None, ""):
        return default
    return str(value)


def _status_label(value: object) -> str:
    label = _label_from_value(value, default="기존 자료")
    return _STATUS_LABELS.get(label.lower(), label)


def _metric_id(value: object) -> str:
    return str(getattr(value, "id", "") or getattr(value, "dataset_key", "") or "")


def _csv_file(value: object) -> str:
    return str(getattr(value, "csv_file", "") or "")


def _fallback_source_label(value: object) -> str:
    metric_id = _metric_id(value)
    csv_file = _csv_file(value)
    if metric_id in _FACULTY_METRIC_IDS or "faculty_securing_rate" in csv_file:
        return "한국대학평가원 대학통계"
    if metric_id in _KCUE_METRIC_IDS or "kcue_university_indicators" in csv_file:
        return "한국대학평가원 대학현황지표"
    if metric_id == "education_return" or "education_cost_return_rate" in csv_file:
        return "대학재정알리미"
    return "대학알리미"


def _fallback_scope_label(value: object) -> str:
    metric_id = _metric_id(value)
    csv_file = _csv_file(value)
    if (
        metric_id in _FACULTY_METRIC_IDS
        or metric_id in _KCUE_METRIC_IDS
        or "faculty_securing_rate" in csv_file
        or "kcue_university_indicators" in csv_file
    ):
        return "평가용 2차 집계자료/가공 CSV"
    if metric_id == "education_return" or "education_cost_return_rate" in csv_file:
        return "원자료 수동 다운로드/가공 CSV"
    return "로컬 CSV"


def _fallback_status(value: object) -> str:
    metric_id = _metric_id(value)
    csv_file = _csv_file(value)
    if (
        metric_id in _FACULTY_METRIC_IDS
        or metric_id in _KCUE_METRIC_IDS
        or metric_id == "education_return"
        or "processed/" in csv_file
    ):
        return "processed"
    return "legacy"


def _resolve_dataset_manifest(value: object) -> dict[str, Any]:
    metric_id = getattr(value, "id", None)
    dataset_key = getattr(value, "dataset_key", None)
    if not metric_id and not dataset_key:
        return {}

    try:
        if metric_id:
            from registry import get_metric_manifest

            manifest = get_metric_manifest(str(metric_id))
        else:
            from registry import get_dataset_manifest

            manifest = get_dataset_manifest(str(dataset_key))
    except (KeyError, ValueError, ImportError):
        return {}

    payload = _manifest_to_dict(manifest)
    source_payload = _load_source_metadata(payload.get("metadata_files", {}).get("source"))
    if source_payload:
        payload.setdefault("source_label", source_payload.get("source_name") or source_payload.get("dataset_name_ko"))
        payload.setdefault("source_org", source_payload.get("source_org"))
        payload.setdefault("source_url", source_payload.get("source_url"))
        payload.setdefault("source_section", source_payload.get("source_section"))
        payload.setdefault(
            "updated_at",
            source_payload.get("processed_at")
            or source_payload.get("downloaded_at")
            or source_payload.get("collected_at"),
        )
    return payload


def _manifest_to_dict(manifest: object) -> dict[str, Any]:
    if isinstance(manifest, Mapping):
        return dict(manifest)
    if is_dataclass(manifest) and not isinstance(manifest, type):
        payload = asdict(manifest)
    else:
        payload = {
            name: getattr(manifest, name)
            for name in (
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
            )
            if hasattr(manifest, name)
        }
    payload.pop("manifest_path", None)
    return payload


def _load_source_metadata(relative_path: object) -> dict[str, Any]:
    if not isinstance(relative_path, str) or not relative_path:
        return {}
    project_root = Path(__file__).resolve().parents[1]
    path = project_root / relative_path
    if not path.exists():
        return {}
    try:
        with path.open(encoding="utf-8") as source_file:
            payload = json.load(source_file)
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}
