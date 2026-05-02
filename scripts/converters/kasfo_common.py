"""Shared helpers for offline KASFO source converters.

Raw source files are treated read-only.  Converter outputs must be written under
``data/conversion_outputs/kasfo`` and validation report directories only.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONVERSION_DIR = PROJECT_ROOT / "data" / "conversion_outputs" / "kasfo"
PROCESSING_REPORT_DIR = PROJECT_ROOT / "data" / "validation" / "processing_reports"
MISMATCH_REPORT_DIR = PROJECT_ROOT / "data" / "validation" / "mismatch_reports"
SCOPE_PATH = PROJECT_ROOT / "data" / "metadata" / "analysis_scopes" / "seoul_private_four_year_universities.json"

COMPARISON_SCHOOLS = [
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
]

RISK_SCHOOLS = [
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
]

KEY_COLUMNS = {
    "No.",
    "No",
    "공시연도",
    "대표학교코드",
    "학교코드",
    "학교명",
    "법인명",
    "본분교명",
    "대학구분",
    "학교종류",
    "학교상태",
    "설립",
    "설립유형",
    "설립구분",
    "학급",
    "학종",
    "소재지유형",
    "지역",
    "지역명",
    "회계",
    "회계연도",
    "기준년도",
    "survey_year",
    "university_name",
    "school_level",
    "school_type",
    "region",
    "row_no",
    "source_file_name",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_code(value: Any) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    digits = "".join(ch for ch in text if ch.isdigit())
    return digits.zfill(7) if digits else text


def parse_amount(value: Any) -> float | None:
    """Parse KASFO amount strings: trim, comma removal, '-' as missing, keep negatives."""
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "")
    if text in {"", "-", "–", "—"}:
        return None
    # Parenthesized negatives are not common in KASFO files but safe to support.
    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1]
    try:
        parsed = float(text)
    except ValueError:
        return None
    return -parsed if negative else parsed


def normalize_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return " ".join(str(value).strip().split())


def is_amount_column(column: str) -> bool:
    col = str(column)
    if col in KEY_COLUMNS:
        return False
    return bool(re.match(r"^\d+\.", col) or "금액" in col or "수입" in col or "지출" in col or "부담" in col or "자금" in col or "비용" in col or "수익" in col or "보수" in col)


def standardize_frame(frame: pd.DataFrame, *, amount_columns: list[str] | None = None) -> pd.DataFrame:
    out = frame.copy()
    out.columns = [normalize_text(c) for c in out.columns]
    for col in ["대표학교코드", "학교코드"]:
        if col in out.columns:
            out[col] = out[col].map(normalize_code)
    for col in ["학교명", "법인명", "본분교명", "지역", "지역명", "회계", "회계연도", "기준년도", "university_name"]:
        if col in out.columns:
            out[col] = out[col].map(normalize_text)
    if amount_columns is None:
        amount_columns = [c for c in out.columns if is_amount_column(c)]
    for col in amount_columns:
        if col in out.columns:
            out[col] = out[col].map(parse_amount)
    return out


def read_csv_any(path: Path, **kwargs: Any) -> pd.DataFrame:
    last_error: Exception | None = None
    for enc in ("utf-8-sig", "utf-8", "cp949", "euc-kr"):
        try:
            return pd.read_csv(path, encoding=enc, **kwargs)
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error:
        raise last_error
    return pd.read_csv(path, **kwargs)


def make_unique_columns(columns: list[str]) -> list[str]:
    counts: dict[str, int] = {}
    out: list[str] = []
    for col in columns:
        base = col or "unnamed"
        counts[base] = counts.get(base, 0) + 1
        out.append(base if counts[base] == 1 else f"{base}__dup{counts[base]}")
    return out


def read_kasfo_excel_sheet(path: Path, sheet_name: str, *, source_file_name: str | None = None) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name=sheet_name, header=None, engine="openpyxl")
    header_row = None
    for idx, row in raw.iterrows():
        cells = {normalize_text(v) for v in row.tolist()}
        if "학교명" in cells and ("법인명" in cells or "회계" in cells or "회계연도" in cells):
            header_row = idx
            break
    if header_row is None:
        raise ValueError(f"Could not locate header row: {path.name} / {sheet_name}")
    header = make_unique_columns([normalize_text(c) or f"unnamed_{i}" for i, c in enumerate(raw.iloc[header_row].tolist())])
    frame = raw.iloc[header_row + 1 :].copy()
    frame.columns = header
    frame = frame.dropna(how="all")
    if "학교명" in frame.columns:
        frame = frame[frame["학교명"].notna()].copy()
    if source_file_name:
        frame["source_file_name"] = source_file_name
    frame["source_sheet_name"] = sheet_name
    return frame.reset_index(drop=True)


def coverage_report(frame: pd.DataFrame, *, school_col: str = "학교명") -> dict[str, Any]:
    schools = set(frame.get(school_col, pd.Series(dtype=str)).dropna().map(normalize_text))
    return {
        "comparison_11": {
            "expected_count": len(COMPARISON_SCHOOLS),
            "present_count": sum(s in schools for s in COMPARISON_SCHOOLS),
            "missing": [s for s in COMPARISON_SCHOOLS if s not in schools],
        },
        "risk_school_sample": {
            "expected_count": len(RISK_SCHOOLS),
            "present_count": sum(s in schools for s in RISK_SCHOOLS),
            "present": [s for s in RISK_SCHOOLS if s in schools],
            "missing": [s for s in RISK_SCHOOLS if s not in schools],
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8-sig")
