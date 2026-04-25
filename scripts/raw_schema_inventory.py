"""Inventory registered and unregistered raw CSV schema contracts."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from registry.raw_schemas import RAW_SCHEMA_REGISTRY, RawCsvSchema


FALLBACK_ENCODINGS: tuple[str, ...] = ("utf-8-sig", "utf-8", "cp949", "euc-kr")


@dataclass(frozen=True)
class RegisteredSchemaRecord:
    metric_id: str
    dataset_key: str
    path: str
    declared_encoding: str
    required_columns: tuple[str, ...]
    exists: bool
    header_encoding: str | None


@dataclass(frozen=True)
class MissingRequiredColumns:
    metric_id: str
    path: str
    missing_columns: tuple[str, ...]


@dataclass(frozen=True)
class EncodingMismatch:
    metric_id: str
    path: str
    declared_encoding: str
    detected_encoding: str | None
    error: str


@dataclass(frozen=True)
class RawSchemaInventory:
    registered: tuple[RegisteredSchemaRecord, ...]
    unregistered: tuple[str, ...]
    missing_required_columns: tuple[MissingRequiredColumns, ...]
    encoding_mismatches: tuple[EncodingMismatch, ...]


@dataclass(frozen=True)
class HeaderReadResult:
    columns: tuple[str, ...]
    encoding: str | None
    encoding_mismatch: bool
    error: str


def _relative_posix(path: Path, project_root: Path) -> str:
    return path.relative_to(project_root).as_posix()


def _same_encoding(left: str, right: str) -> bool:
    return left.lower().replace("_", "-") == right.lower().replace("_", "-")


def _candidate_encodings(declared_encoding: str) -> tuple[str, ...]:
    encodings = [declared_encoding]
    encodings.extend(
        encoding
        for encoding in FALLBACK_ENCODINGS
        if not _same_encoding(encoding, declared_encoding)
    )
    return tuple(encodings)


def read_csv_header(path: Path, encoding: str) -> tuple[str, ...]:
    with path.open("r", encoding=encoding, newline="") as handle:
        reader = csv.reader(handle)
        try:
            return tuple(column.strip() for column in next(reader))
        except StopIteration:
            return ()


def _contains_required_columns(
    header: Iterable[str],
    required_columns: Iterable[str],
) -> bool:
    header_set = set(header)
    return set(required_columns).issubset(header_set)


def read_header_with_fallback(
    path: Path,
    declared_encoding: str,
    required_columns: Iterable[str] = (),
) -> HeaderReadResult:
    required_tuple = tuple(required_columns)

    try:
        declared_header = read_csv_header(path, declared_encoding)
    except UnicodeDecodeError as exc:
        declared_error = str(exc)
        for encoding in _candidate_encodings(declared_encoding)[1:]:
            try:
                return HeaderReadResult(
                    columns=read_csv_header(path, encoding),
                    encoding=encoding,
                    encoding_mismatch=True,
                    error=declared_error,
                )
            except UnicodeDecodeError:
                continue
        return HeaderReadResult(
            columns=(),
            encoding=None,
            encoding_mismatch=True,
            error=declared_error,
        )

    if _contains_required_columns(declared_header, required_tuple):
        return HeaderReadResult(
            columns=declared_header,
            encoding=declared_encoding,
            encoding_mismatch=False,
            error="",
        )

    for encoding in _candidate_encodings(declared_encoding)[1:]:
        try:
            fallback_header = read_csv_header(path, encoding)
        except UnicodeDecodeError:
            continue
        if _contains_required_columns(fallback_header, required_tuple):
            return HeaderReadResult(
                columns=fallback_header,
                encoding=encoding,
                encoding_mismatch=True,
                error="declared encoding decoded the file but did not expose the required header",
            )

    return HeaderReadResult(
        columns=declared_header,
        encoding=declared_encoding,
        encoding_mismatch=False,
        error="",
    )


def discover_csv_files(project_root: Path) -> tuple[str, ...]:
    candidates = list(project_root.glob("*.csv"))
    data_dir = project_root / "data"
    if data_dir.exists():
        candidates.extend(data_dir.rglob("*.csv"))

    visible_files = {
        _relative_posix(path, project_root)
        for path in candidates
        if path.is_file()
        and not any(part.startswith(".") for part in path.relative_to(project_root).parts)
    }
    return tuple(sorted(visible_files))


def inspect_registered_schemas(
    project_root: Path,
    schemas: Iterable[RawCsvSchema] | None = None,
) -> tuple[
    tuple[RegisteredSchemaRecord, ...],
    tuple[MissingRequiredColumns, ...],
    tuple[EncodingMismatch, ...],
]:
    schema_items = tuple(schemas if schemas is not None else RAW_SCHEMA_REGISTRY.values())
    registered: list[RegisteredSchemaRecord] = []
    missing_required_columns: list[MissingRequiredColumns] = []
    encoding_mismatches: list[EncodingMismatch] = []

    for schema in schema_items:
        path = schema.file_path(project_root)
        relative_path = schema.data_relative_path.as_posix()
        if not path.exists():
            registered.append(
                RegisteredSchemaRecord(
                    metric_id=schema.metric_id,
                    dataset_key=schema.dataset_key,
                    path=relative_path,
                    declared_encoding=schema.csv_encoding,
                    required_columns=schema.required_columns,
                    exists=False,
                    header_encoding=None,
                )
            )
            continue

        header_result = read_header_with_fallback(
            path,
            schema.csv_encoding,
            schema.required_columns,
        )
        registered.append(
            RegisteredSchemaRecord(
                metric_id=schema.metric_id,
                dataset_key=schema.dataset_key,
                path=relative_path,
                declared_encoding=schema.csv_encoding,
                required_columns=schema.required_columns,
                exists=True,
                header_encoding=header_result.encoding,
            )
        )

        if header_result.encoding_mismatch:
            encoding_mismatches.append(
                EncodingMismatch(
                    metric_id=schema.metric_id,
                    path=relative_path,
                    declared_encoding=schema.csv_encoding,
                    detected_encoding=header_result.encoding,
                    error=header_result.error,
                )
            )

        header_columns = set(header_result.columns)
        missing = tuple(
            column
            for column in schema.required_columns
            if column not in header_columns
        )
        if missing:
            missing_required_columns.append(
                MissingRequiredColumns(
                    metric_id=schema.metric_id,
                    path=relative_path,
                    missing_columns=missing,
                )
            )

    return (
        tuple(registered),
        tuple(missing_required_columns),
        tuple(encoding_mismatches),
    )


def build_inventory(
    project_root: Path | None = None,
    schemas: Iterable[RawCsvSchema] | None = None,
) -> RawSchemaInventory:
    root = (project_root or PROJECT_ROOT).resolve()
    schema_items = tuple(schemas if schemas is not None else RAW_SCHEMA_REGISTRY.values())
    registered, missing_required_columns, encoding_mismatches = inspect_registered_schemas(
        root,
        schema_items,
    )
    registered_paths = {schema.data_relative_path.as_posix() for schema in schema_items}
    unregistered = tuple(
        path
        for path in discover_csv_files(root)
        if path not in registered_paths
    )
    return RawSchemaInventory(
        registered=registered,
        unregistered=unregistered,
        missing_required_columns=missing_required_columns,
        encoding_mismatches=encoding_mismatches,
    )


def inventory_to_dict(inventory: RawSchemaInventory) -> dict[str, object]:
    return {
        "registered": [asdict(item) for item in inventory.registered],
        "unregistered": list(inventory.unregistered),
        "missing_required_columns": [
            asdict(item) for item in inventory.missing_required_columns
        ],
        "encoding_mismatches": [
            asdict(item) for item in inventory.encoding_mismatches
        ],
    }


def format_inventory_text(inventory: RawSchemaInventory) -> str:
    payload = inventory_to_dict(inventory)
    lines: list[str] = []
    for section in (
        "registered",
        "unregistered",
        "missing_required_columns",
        "encoding_mismatches",
    ):
        lines.append(f"{section}:")
        values = payload[section]
        if not values:
            lines.append("  - none")
            continue
        for value in values:
            lines.append(f"  - {value}")
    return "\n".join(lines)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=PROJECT_ROOT,
        help="Project root to inspect. Defaults to this repository root.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    inventory = build_inventory(args.project_root)
    if args.format == "json":
        print(json.dumps(inventory_to_dict(inventory), ensure_ascii=False, indent=2))
    else:
        print(format_inventory_text(inventory))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
