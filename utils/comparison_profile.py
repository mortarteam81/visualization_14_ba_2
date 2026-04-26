"""Comparison school profile storage and validation helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Protocol, Sequence


DEFAULT_PROFILE_ID = "system_default"
DEFAULT_PROFILE_NAME = "운영자 기본 비교군"
DEFAULT_OWNER_TYPE = "system"
DEFAULT_OWNER_ID = "system"
DEFAULT_BASE_SCHOOL = "성신여자대학교"
DEFAULT_COMPARISON_SCHOOLS = (
    "숙명여자대학교",
    "덕성여자대학교",
    "서울여자대학교",
)
MAX_COMPARISON_SCHOOLS = 5
MAX_COMPARISON_GROUPS = 3
ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_PROFILE_PATH = ROOT_DIR / ".streamlit" / "comparison_profile.local.json"


@dataclass(frozen=True)
class ComparisonGroup:
    name: str
    schools: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "schools": list(self.schools)}


@dataclass(frozen=True)
class ComparisonProfile:
    profile_id: str
    profile_name: str
    owner_type: str
    owner_id: str
    base_school: str
    comparison_schools: tuple[str, ...]
    comparison_groups: tuple[ComparisonGroup, ...]
    is_default: bool
    updated_at: str

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["comparison_schools"] = list(self.comparison_schools)
        payload["comparison_groups"] = [group.to_dict() for group in self.comparison_groups]
        return payload


class ComparisonProfileStore(Protocol):
    def load(self, schools: Sequence[str] | None = None) -> ComparisonProfile:
        """Load a profile normalized for the optional school universe."""

    def save(self, profile: ComparisonProfile, schools: Sequence[str] | None = None) -> ComparisonProfile:
        """Persist and return a normalized profile."""


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _clean_school_name(value: object) -> str:
    return str(value).strip() if value is not None else ""


def _valid_school_list(schools: Sequence[str] | None) -> list[str]:
    if schools is None:
        return []
    seen: set[str] = set()
    valid: list[str] = []
    for school in schools:
        name = _clean_school_name(school)
        if name and name not in seen:
            seen.add(name)
            valid.append(name)
    return valid


def _filter_comparison_schools(
    candidates: Sequence[str],
    *,
    base_school: str,
    schools: Sequence[str] | None = None,
    limit: int = MAX_COMPARISON_SCHOOLS,
) -> tuple[str, ...]:
    available = set(_valid_school_list(schools)) if schools is not None else None
    filtered: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        school = _clean_school_name(candidate)
        if not school or school == base_school or school in seen:
            continue
        if available is not None and school not in available:
            continue
        filtered.append(school)
        seen.add(school)
        if len(filtered) >= limit:
            break
    return tuple(filtered)


def _normalize_comparison_groups(
    groups: Sequence[ComparisonGroup],
    schools: Sequence[str] | None = None,
    *,
    limit: int = MAX_COMPARISON_GROUPS,
) -> tuple[ComparisonGroup, ...]:
    normalized_groups: list[ComparisonGroup] = []
    for group in groups:
        name = _clean_school_name(group.name)
        group_schools = _filter_comparison_schools(
            group.schools,
            base_school="",
            schools=schools,
            limit=len(group.schools),
        )
        if not name or not group_schools:
            continue
        normalized_groups.append(ComparisonGroup(name=name, schools=group_schools))
        if len(normalized_groups) >= limit:
            break
    return tuple(normalized_groups)


def _resolve_base_school(candidate: str, schools: Sequence[str] | None = None) -> str:
    valid_schools = _valid_school_list(schools)
    if not valid_schools:
        return candidate or DEFAULT_BASE_SCHOOL
    if candidate in valid_schools:
        return candidate
    if DEFAULT_BASE_SCHOOL in valid_schools:
        return DEFAULT_BASE_SCHOOL
    return valid_schools[0]


def default_comparison_profile(schools: Sequence[str] | None = None) -> ComparisonProfile:
    base_school = _resolve_base_school(DEFAULT_BASE_SCHOOL, schools)
    comparison_schools = _filter_comparison_schools(
        DEFAULT_COMPARISON_SCHOOLS,
        base_school=base_school,
        schools=schools,
    )
    return ComparisonProfile(
        profile_id=DEFAULT_PROFILE_ID,
        profile_name=DEFAULT_PROFILE_NAME,
        owner_type=DEFAULT_OWNER_TYPE,
        owner_id=DEFAULT_OWNER_ID,
        base_school=base_school,
        comparison_schools=comparison_schools,
        comparison_groups=(),
        is_default=True,
        updated_at="",
    )


def _comparison_groups_from_payload(payload: object) -> tuple[ComparisonGroup, ...]:
    if not isinstance(payload, list):
        return ()

    groups: list[ComparisonGroup] = []
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            continue
        name = _clean_school_name(item.get("name")) or f"비교 그룹 {index}"
        schools = item.get("schools", [])
        if isinstance(schools, str):
            schools = [schools]
        try:
            school_values = tuple(_clean_school_name(school) for school in schools)
        except TypeError:
            school_values = ()
        groups.append(ComparisonGroup(name=name, schools=school_values))
    return tuple(groups)


def comparison_profile_from_dict(payload: dict[str, object]) -> ComparisonProfile:
    comparison_schools = payload.get("comparison_schools", DEFAULT_COMPARISON_SCHOOLS)
    if isinstance(comparison_schools, str):
        comparison_schools = [comparison_schools]

    return ComparisonProfile(
        profile_id=_clean_school_name(payload.get("profile_id")) or DEFAULT_PROFILE_ID,
        profile_name=_clean_school_name(payload.get("profile_name")) or DEFAULT_PROFILE_NAME,
        owner_type=_clean_school_name(payload.get("owner_type")) or DEFAULT_OWNER_TYPE,
        owner_id=_clean_school_name(payload.get("owner_id")) or DEFAULT_OWNER_ID,
        base_school=_clean_school_name(payload.get("base_school")) or DEFAULT_BASE_SCHOOL,
        comparison_schools=tuple(_clean_school_name(school) for school in comparison_schools),
        comparison_groups=_comparison_groups_from_payload(payload.get("comparison_groups")),
        is_default=bool(payload.get("is_default", True)),
        updated_at=_clean_school_name(payload.get("updated_at")),
    )


def normalize_comparison_profile(
    profile: ComparisonProfile,
    schools: Sequence[str] | None = None,
    *,
    updated_at: str | None = None,
) -> ComparisonProfile:
    base_school = _resolve_base_school(_clean_school_name(profile.base_school), schools)
    comparison_schools = _filter_comparison_schools(
        profile.comparison_schools,
        base_school=base_school,
        schools=schools,
    )
    comparison_groups = _normalize_comparison_groups(profile.comparison_groups, schools)

    return ComparisonProfile(
        profile_id=profile.profile_id or DEFAULT_PROFILE_ID,
        profile_name=profile.profile_name or DEFAULT_PROFILE_NAME,
        owner_type=profile.owner_type or DEFAULT_OWNER_TYPE,
        owner_id=profile.owner_id or DEFAULT_OWNER_ID,
        base_school=base_school,
        comparison_schools=comparison_schools,
        comparison_groups=comparison_groups,
        is_default=profile.is_default,
        updated_at=updated_at if updated_at is not None else profile.updated_at,
    )


def selected_schools_from_profile(
    profile: ComparisonProfile,
    schools: Sequence[str] | None = None,
) -> list[str]:
    normalized = normalize_comparison_profile(profile, schools)
    selected = [normalized.base_school, *normalized.comparison_schools]
    valid_schools = set(_valid_school_list(schools)) if schools is not None else None
    if valid_schools is None:
        return selected
    return [school for school in selected if school in valid_schools]


def default_selected_schools(
    schools: Sequence[str],
    *,
    fallback: Sequence[str] | None = None,
    store: ComparisonProfileStore | None = None,
) -> list[str]:
    try:
        profile = (store or FileComparisonProfileStore()).load(schools)
        selected = selected_schools_from_profile(profile, schools)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        selected = []

    if selected:
        return selected

    valid_schools = set(_valid_school_list(schools))
    fallback_selection = [school for school in (fallback or []) if school in valid_schools]
    if fallback_selection:
        return fallback_selection
    return list(schools[:1])


def comparison_group_definitions(
    schools: Sequence[str],
    *,
    store: ComparisonProfileStore | None = None,
) -> dict[str, list[str]]:
    try:
        profile = (store or FileComparisonProfileStore()).load(schools)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return {}

    return {group.name: list(group.schools) for group in profile.comparison_groups}


class FileComparisonProfileStore:
    def __init__(self, path: Path | str = DEFAULT_PROFILE_PATH) -> None:
        self.path = Path(path)

    def load(self, schools: Sequence[str] | None = None) -> ComparisonProfile:
        if not self.path.exists():
            return default_comparison_profile(schools)

        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return default_comparison_profile(schools)
        return normalize_comparison_profile(comparison_profile_from_dict(payload), schools)

    def save(self, profile: ComparisonProfile, schools: Sequence[str] | None = None) -> ComparisonProfile:
        normalized = normalize_comparison_profile(profile, schools, updated_at=_utc_timestamp())
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(normalized.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return normalized
