from __future__ import annotations

from pathlib import Path

from scripts.asset_policy_check import (
    detect_text_encoding,
    scan_assets,
    validate_encoding,
    validate_filename,
)


def test_validate_filename_accepts_official_pattern(tmp_path: Path) -> None:
    path = tmp_path / "official-name_01.csv"
    path.write_text("col\nvalue\n", encoding="utf-8")

    assert validate_filename(path) == []


def test_validate_filename_rejects_whitespace_and_non_ascii(tmp_path: Path) -> None:
    path = tmp_path / "전임교원 확보율.csv"
    path.write_text("col\nvalue\n", encoding="utf-8")

    violations = validate_filename(path)

    assert len(violations) == 1
    assert violations[0].kind == "filename"


def test_detect_text_encoding_accepts_utf8_sig(tmp_path: Path) -> None:
    path = tmp_path / "dataset.csv"
    path.write_text("col\nvalue\n", encoding="utf-8-sig")

    assert detect_text_encoding(path) == "utf-8-sig"


def test_validate_encoding_rejects_non_utf8_text_asset(tmp_path: Path) -> None:
    path = tmp_path / "legacy.csv"
    path.write_bytes("name,value\ncaf\xe9,1\n".encode("cp1252"))

    violations = validate_encoding(path)

    assert len(violations) == 1
    assert violations[0].kind == "encoding"


def test_scan_assets_ignores_binary_files_for_encoding_policy(tmp_path: Path) -> None:
    binary_path = tmp_path / "chart.png"
    binary_path.write_bytes(b"\x89PNG\r\n\x1a\n")

    assert scan_assets(tmp_path) == []

