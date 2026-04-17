from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


TEXT_EXTENSIONS = {
    ".csv",
    ".json",
    ".md",
    ".py",
    ".txt",
    ".tsv",
    ".yaml",
    ".yml",
}
ROOT_LEVEL_ASSET_EXTENSIONS = {".csv", ".tsv", ".json"}
ALLOWED_TEXT_ENCODINGS = ("utf-8", "utf-8-sig")
FILENAME_PATTERN = re.compile(r"^[A-Za-z0-9._()-]+$")


@dataclass(frozen=True)
class PolicyViolation:
    path: str
    kind: str
    message: str


def is_text_asset(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS


def validate_filename(path: Path) -> list[PolicyViolation]:
    if FILENAME_PATTERN.fullmatch(path.name):
        return []
    return [
        PolicyViolation(
            path=path.as_posix(),
            kind="filename",
            message="filename must match ^[A-Za-z0-9._()-]+$",
        )
    ]


def detect_text_encoding(path: Path) -> str | None:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        try:
            raw.decode("utf-8-sig")
            return "utf-8-sig"
        except UnicodeDecodeError:
            return None
    for encoding in ALLOWED_TEXT_ENCODINGS:
        try:
            raw.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    return None


def validate_encoding(path: Path) -> list[PolicyViolation]:
    if not is_text_asset(path):
        return []

    encoding = detect_text_encoding(path)
    if encoding is not None:
        return []

    return [
        PolicyViolation(
            path=path.as_posix(),
            kind="encoding",
            message="text asset must decode as utf-8 or utf-8-sig",
        )
    ]


def iter_candidate_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]

    if (root / "data").exists():
        candidates = [
            path
            for path in sorted((root / "data").rglob("*"))
            if path.is_file() and "__pycache__" not in path.parts
        ]
        candidates.extend(
            path
            for path in sorted(root.iterdir())
            if path.is_file() and path.suffix.lower() in ROOT_LEVEL_ASSET_EXTENSIONS
        )
        return candidates

    return [
        path
        for path in sorted(root.rglob("*"))
        if path.is_file() and ".git" not in path.parts and "__pycache__" not in path.parts
    ]


def scan_assets(root: Path) -> list[PolicyViolation]:
    violations: list[PolicyViolation] = []
    for path in iter_candidate_files(root):
        violations.extend(validate_filename(path))
        violations.extend(validate_encoding(path))
    return violations


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check repository asset naming and encoding policy.")
    parser.add_argument("root", nargs="?", default=".", help="Root directory to scan.")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    violations = scan_assets(root)

    if args.as_json:
        print(json.dumps([asdict(item) for item in violations], ensure_ascii=True, indent=2))
    else:
        if violations:
            for item in violations:
                print(f"{item.kind}: {item.path}: {item.message}")
        else:
            print("No asset policy violations found.")

    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
