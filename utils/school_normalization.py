"""School-name, code, and campus normalization helpers."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCOPE_PATH = (
    PROJECT_ROOT
    / "data"
    / "metadata"
    / "analysis_scopes"
    / "seoul_private_four_year_universities.json"
)
DEFAULT_ALIAS_PATH = PROJECT_ROOT / "data" / "metadata" / "school_aliases.json"


def normalize_school_code(value: Any, *, width: int = 7) -> str:
    """Return school code as a zero-padded string when it is numeric."""

    if _is_missing(value):
        return ""
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    digits = "".join(char for char in text if char.isdigit())
    if not digits:
        return text
    return digits.zfill(width)


def canonical_school_names() -> list[str]:
    """Return canonical school names in the default analysis scope."""

    return list(_alias_index()["canonical_names"])


def resolve_school_name(value: Any) -> str | None:
    """Resolve a raw school name to a canonical default-scope school name.

    The resolver is intentionally conservative:
    exact canonical match -> explicit alias match -> explicit main-campus suffix
    removal. It does not strip parentheses or campus suffixes for branch schools.
    """

    if _is_missing(value):
        return None

    index = _alias_index()
    text = str(value).strip()
    key = _name_key(text)

    if key in index["protected_keys"]:
        return None
    if key in index["name_to_canonical"]:
        return index["name_to_canonical"][key]

    for suffix in index["main_campus_suffixes"]:
        if not text.endswith(suffix):
            continue
        base = text[: -len(suffix)].strip()
        base_key = _name_key(base)
        if base_key in index["protected_keys"]:
            return None
        if base_key in index["name_to_canonical"]:
            return index["name_to_canonical"][base_key]

    return None


def canonicalize_school_name(value: Any, *, default_to_original: bool = True) -> str | None:
    """Return canonical school name, optionally falling back to the original."""

    resolved = resolve_school_name(value)
    if resolved is not None:
        return resolved
    if default_to_original and not _is_missing(value):
        return str(value).strip()
    return None


def canonicalize_school_name_column(
    df: pd.DataFrame,
    *,
    school_col: str = "학교명",
    restrict_to_default_scope: bool = False,
) -> pd.DataFrame:
    """Canonicalize a school-name column without mutating the source frame."""

    if school_col not in df.columns:
        return df.copy()

    frame = df.copy()
    resolved = frame[school_col].map(resolve_school_name)
    if restrict_to_default_scope:
        frame = frame[resolved.notna()].copy()
        resolved = resolved.loc[frame.index]
    frame[school_col] = resolved.combine_first(frame[school_col].astype(str).str.strip())
    return frame


def is_default_scope_school(value: Any) -> bool:
    """Return True when the value resolves to a canonical default-scope school."""

    return resolve_school_name(value) is not None


@lru_cache(maxsize=1)
def _alias_index() -> dict[str, Any]:
    scope = _load_json(DEFAULT_SCOPE_PATH)
    alias_config = _load_json(DEFAULT_ALIAS_PATH)

    name_to_canonical: dict[str, str] = {}
    canonical_names: list[str] = []
    protected_keys = {_name_key(name) for name in alias_config.get("protected_branch_campus_names", [])}

    for school in scope.get("schools", []):
        canonical = str(school.get("school_name", "")).strip()
        if not canonical:
            continue
        canonical_names.append(canonical)
        name_to_canonical[_name_key(canonical)] = canonical

    for group in [*scope.get("alias_groups", []), *alias_config.get("alias_groups", [])]:
        canonical = str(group.get("canonical_school_name", "")).strip()
        if not canonical:
            continue
        canonical_key = _name_key(canonical)
        canonical = name_to_canonical.get(canonical_key, canonical)
        name_to_canonical[canonical_key] = canonical
        for alias in group.get("aliases", []):
            alias_key = _name_key(alias)
            if alias_key and alias_key not in protected_keys:
                name_to_canonical[alias_key] = canonical

    return {
        "canonical_names": tuple(dict.fromkeys(canonical_names)),
        "name_to_canonical": name_to_canonical,
        "protected_keys": protected_keys,
        "main_campus_suffixes": tuple(alias_config.get("main_campus_suffixes", [])),
    }


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _name_key(value: Any) -> str:
    if _is_missing(value):
        return ""
    return "".join(str(value).strip().split())


def _is_missing(value: Any) -> bool:
    return value is None or pd.isna(value) or str(value).strip() == ""
