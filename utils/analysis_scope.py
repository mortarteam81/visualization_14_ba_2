from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_SCOPE_ID = "seoul_private_four_year_universities"
DEFAULT_SCOPE_DIR = Path(__file__).resolve().parents[1] / "data" / "metadata" / "analysis_scopes"

REGION_COLUMNS = ("지역", "지역명", "region_name", "pbnf_area_nm")
FOUNDING_COLUMNS = ("설립유형", "설립", "설립구분", "founding_type", "founding_type_detail", "schl_estb_div_nm")
SCHOOL_TYPE_COLUMNS = ("학교종류", "school_type", "school_level", "schl_knd_nm", "schl_div_nm")
CAMPUS_COLUMNS = ("본분교명", "campus_type", "psbs_div_nm")
STATUS_COLUMNS = ("학교상태", "school_status", "schl_stat_nm")
SCHOOL_NAME_COLUMNS = ("학교명", "학교", "대학명", "school_name", "lst_kor_schl_nm")

FOUR_YEAR_VALUES = {"4년제 대학", "4년제대학교", "4년제", "대학교", "대학", "일반대학"}
NOT_FOUR_YEAR_MARKERS = ("전문대", "대학원", "사이버", "기능대학", "기술대학", "교육대학", "산업대학", "방송통신")
SEOUL_VALUES = {"서울", "서울특별시"}
REGION_VALUES = {
    "서울",
    "서울특별시",
    "부산",
    "부산광역시",
    "대구",
    "대구광역시",
    "인천",
    "인천광역시",
    "광주",
    "광주광역시",
    "대전",
    "대전광역시",
    "울산",
    "울산광역시",
    "세종",
    "세종특별자치시",
    "경기",
    "경기도",
    "강원",
    "강원특별자치도",
    "충북",
    "충청북도",
    "충남",
    "충청남도",
    "전북",
    "전북특별자치도",
    "전남",
    "전라남도",
    "경북",
    "경상북도",
    "경남",
    "경상남도",
    "제주",
    "제주특별자치도",
}
FOUNDING_VALUES = {"사립", "국립", "공립", "국립대법인"}
CAMPUS_VALUES = {"본교", "분교", "제2캠퍼스", "캠퍼스"}
STATUS_VALUES = {"기존", "신설", "폐교", "폐쇄", "통폐합"}


def load_default_analysis_scope(scope_id: str = DEFAULT_SCOPE_ID) -> dict[str, Any]:
    """Load an analysis-scope manifest from data/metadata/analysis_scopes."""

    path = DEFAULT_SCOPE_DIR / f"{scope_id}.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def annotate_default_analysis_flags(
    df: pd.DataFrame,
    manifest_or_scope: Mapping[str, Any] | str | Path | None = None,
) -> pd.DataFrame:
    """Add default-analysis exclusion columns without mutating the source frame."""

    manifest = _resolve_manifest(manifest_or_scope)
    result = df.copy(deep=True)
    reason_lists = [_exclusion_reasons(row, result.columns, manifest) for _, row in result.iterrows()]
    result["default_analysis_excluded"] = pd.Series(
        [bool(reasons) for reasons in reason_lists],
        index=result.index,
        dtype=object,
    )
    result["exclusion_reasons"] = reason_lists
    return result


def apply_default_analysis_scope(
    df: pd.DataFrame,
    manifest_or_scope: Mapping[str, Any] | str | Path | None = None,
) -> pd.DataFrame:
    """Return only rows included in the default analysis scope."""

    annotated = annotate_default_analysis_flags(df, manifest_or_scope)
    included_mask = ~annotated["default_analysis_excluded"].astype(bool)
    return annotated[included_mask].copy()


def _resolve_manifest(manifest_or_scope: Mapping[str, Any] | str | Path | None) -> dict[str, Any]:
    if manifest_or_scope is None:
        return load_default_analysis_scope()
    if isinstance(manifest_or_scope, Mapping):
        return dict(manifest_or_scope)
    if not isinstance(manifest_or_scope, (str, Path)):
        return load_default_analysis_scope()
    path_or_scope = Path(manifest_or_scope)
    if path_or_scope.suffix == ".json" or path_or_scope.exists():
        with path_or_scope.open(encoding="utf-8") as f:
            return json.load(f)
    return load_default_analysis_scope(str(manifest_or_scope))


def _exclusion_reasons(row: pd.Series, columns: pd.Index, manifest: Mapping[str, Any]) -> list[str]:
    if _has_usable_filter_columns(row, columns):
        return _column_based_reasons(row, columns)
    return [] if _name_in_scope(row, columns, manifest) else ["not_in_default_scope"]


def _column_based_reasons(row: pd.Series, columns: pd.Index) -> list[str]:
    reasons: list[str] = []

    region = _value(row, columns, REGION_COLUMNS)
    if _is_missing(region):
        reasons.append("missing_region")
    elif _norm(region) not in {_norm(item) for item in SEOUL_VALUES}:
        reasons.append("not_seoul")

    founding = _value(row, columns, FOUNDING_COLUMNS)
    if _is_missing(founding):
        reasons.append("missing_founding_type")
    elif _norm(founding) != "사립":
        reasons.append("not_private")

    school_type = _value(row, columns, SCHOOL_TYPE_COLUMNS)
    if _is_missing(school_type) or not _is_recognized_school_type(school_type):
        reasons.append("ambiguous_school_type")
    elif not _is_four_year_university(school_type):
        reasons.append("not_four_year_university")

    campus = _value(row, columns, CAMPUS_COLUMNS)
    if not _is_missing(campus) and _norm(campus) != "본교":
        reasons.append("branch_campus")

    status = _value(row, columns, STATUS_COLUMNS)
    if not _is_missing(status):
        normalized_status = _norm(status)
        if normalized_status == "신설":
            reasons.append("new_school")
        elif normalized_status != "기존":
            reasons.append("closed")

    return reasons


def _has_usable_filter_columns(row: pd.Series, columns: pd.Index) -> bool:
    required_groups = (REGION_COLUMNS, FOUNDING_COLUMNS, SCHOOL_TYPE_COLUMNS, CAMPUS_COLUMNS, STATUS_COLUMNS)
    if not all(_find_column(columns, group) is not None for group in required_groups):
        return False

    values = [_value(row, columns, group) for group in required_groups]
    if not any(not _is_missing(value) for value in values):
        return False

    region, founding, school_type, campus, status = values
    return (
        _is_missing(region) or _norm(region) in {_norm(item) for item in REGION_VALUES}
    ) and (
        _is_missing(founding) or _norm(founding) in {_norm(item) for item in FOUNDING_VALUES}
    ) and (
        _is_missing(school_type) or _is_recognized_school_type(school_type)
    ) and (
        _is_missing(campus) or _norm(campus) in {_norm(item) for item in CAMPUS_VALUES}
    ) and (
        _is_missing(status) or _norm(status) in {_norm(item) for item in STATUS_VALUES}
    )


def _name_in_scope(row: pd.Series, columns: pd.Index, manifest: Mapping[str, Any]) -> bool:
    name = _value(row, columns, SCHOOL_NAME_COLUMNS)
    if _is_missing(name):
        return False

    scoped_names = {_norm(school["school_name"]) for school in manifest.get("schools", [])}
    for alias_group in manifest.get("alias_groups", []):
        scoped_names.add(_norm(alias_group.get("canonical_school_name")))
        scoped_names.update(_norm(alias) for alias in alias_group.get("aliases", []))
    return _norm(name) in scoped_names


def _find_column(columns: pd.Index, candidates: tuple[str, ...]) -> str | None:
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def _value(row: pd.Series, columns: pd.Index, candidates: tuple[str, ...]) -> Any:
    column = _find_column(columns, candidates)
    if column is None:
        return None
    return row[column]


def _norm(value: Any) -> str:
    if _is_missing(value):
        return ""
    return str(value).strip().replace(" ", "")


def _is_missing(value: Any) -> bool:
    return value is None or pd.isna(value) or str(value).strip() == ""


def _is_recognized_school_type(value: Any) -> bool:
    normalized = _norm(value)
    if normalized in {_norm(item) for item in FOUR_YEAR_VALUES}:
        return True
    return any(marker in normalized for marker in NOT_FOUR_YEAR_MARKERS)


def _is_four_year_university(value: Any) -> bool:
    normalized = _norm(value)
    if any(marker in normalized for marker in NOT_FOUR_YEAR_MARKERS):
        return False
    return normalized in {_norm(item) for item in FOUR_YEAR_VALUES}
