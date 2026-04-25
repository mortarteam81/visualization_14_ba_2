from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from registry.metadata import METRIC_REGISTRY
from registry.raw_schemas import (
    RAW_SCHEMA_REGISTRY,
    UNREGISTERED_RAW_CSV_ALLOWLIST,
    RawCsvSchema,
)
from scripts.raw_schema_inventory import build_inventory, inspect_registered_schemas


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_registered_schemas_cover_all_implemented_metrics() -> None:
    implemented_metrics = {
        metric.id
        for metric in METRIC_REGISTRY.values()
        if metric.implemented and metric.csv_file
    }

    assert set(RAW_SCHEMA_REGISTRY) == implemented_metrics


def test_registered_schema_files_exist() -> None:
    missing_files = [
        schema.data_relative_path.as_posix()
        for schema in RAW_SCHEMA_REGISTRY.values()
        if not schema.file_path(PROJECT_ROOT).exists()
    ]

    assert missing_files == []


def test_registered_schema_headers_include_required_columns() -> None:
    inventory = build_inventory(PROJECT_ROOT)

    assert inventory.missing_required_columns == ()


def test_unregistered_csvs_match_allowlist() -> None:
    inventory = build_inventory(PROJECT_ROOT)
    expected = {path.as_posix() for path in UNREGISTERED_RAW_CSV_ALLOWLIST}

    assert set(inventory.unregistered) == expected


def test_inventory_detects_declared_encoding_mismatch(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    csv_path = data_dir / "sample.csv"
    csv_path.write_text("기준년도,학교명\n2024,성신여자대학교\n", encoding="utf-8")
    schema = RawCsvSchema(
        metric_id="sample",
        dataset_key="sample",
        csv_file="sample.csv",
        csv_encoding="cp949",
        required_columns=("기준년도", "학교명"),
    )

    _, missing_required_columns, encoding_mismatches = inspect_registered_schemas(
        tmp_path,
        schemas=(schema,),
    )

    assert missing_required_columns == ()
    assert len(encoding_mismatches) == 1
    assert encoding_mismatches[0].metric_id == "sample"
    assert encoding_mismatches[0].detected_encoding in {"utf-8", "utf-8-sig"}


def test_raw_schema_inventory_cli_json_smoke() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/raw_schema_inventory.py",
            "--format",
            "json",
        ],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert set(payload) == {
        "registered",
        "unregistered",
        "missing_required_columns",
        "encoding_mismatches",
    }
    assert len(payload["registered"]) == len(RAW_SCHEMA_REGISTRY)
