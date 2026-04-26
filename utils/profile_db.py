"""Neon-backed comparison profile storage."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import json
from typing import Any, Sequence

from utils.app_db import (
    AppDatabaseError,
    SessionScope,
    _execute,
    _fetchone,
    _row_mapping,
    normalize_email,
    streamlit_session_scope,
)
from utils.comparison_profile import (
    ComparisonProfile,
    ComparisonProfileStore,
    DEFAULT_OWNER_ID,
    DEFAULT_OWNER_TYPE,
    DEFAULT_PROFILE_ID,
    DEFAULT_PROFILE_NAME,
    FileComparisonProfileStore,
    comparison_profile_from_dict,
    default_comparison_profile,
    normalize_comparison_profile,
)


USER_OWNER_TYPE = "user"
USER_PROFILE_NAME = "내 비교군"


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _user_profile_id(email: str) -> str:
    return f"user:{normalize_email(email)}:default"


def _loads_json_list(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _bool_value(value: object) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "t", "yes", "y"}
    return bool(value)


def _profile_from_row(row: Any, schools: Sequence[str] | None) -> ComparisonProfile | None:
    columns = (
        "profile_id",
        "profile_name",
        "owner_type",
        "owner_id",
        "base_school",
        "comparison_schools",
        "comparison_groups",
        "is_default",
        "updated_at",
    )
    mapping = _row_mapping(row, columns)
    if not mapping:
        return None
    payload: dict[str, object] = {
        "profile_id": mapping.get("profile_id"),
        "profile_name": mapping.get("profile_name"),
        "owner_type": mapping.get("owner_type"),
        "owner_id": mapping.get("owner_id"),
        "base_school": mapping.get("base_school"),
        "comparison_schools": _loads_json_list(mapping.get("comparison_schools")),
        "comparison_groups": _loads_json_list(mapping.get("comparison_groups")),
        "is_default": _bool_value(mapping.get("is_default")),
        "updated_at": str(mapping.get("updated_at") or ""),
    }
    return normalize_comparison_profile(comparison_profile_from_dict(payload), schools)


class DatabaseComparisonProfileStore:
    def __init__(
        self,
        *,
        session_scope: SessionScope = streamlit_session_scope,
        owner_type: str,
        owner_id: str,
        profile_id: str,
        profile_name: str,
        fallback_store: ComparisonProfileStore | None = None,
        include_system_fallback: bool = True,
    ) -> None:
        self.session_scope = session_scope
        self.owner_type = owner_type
        self.owner_id = owner_id
        self.profile_id = profile_id
        self.profile_name = profile_name
        self.fallback_store = fallback_store or FileComparisonProfileStore()
        self.include_system_fallback = include_system_fallback

    @classmethod
    def for_user(
        cls,
        email: str,
        *,
        session_scope: SessionScope = streamlit_session_scope,
        fallback_store: ComparisonProfileStore | None = None,
    ) -> "DatabaseComparisonProfileStore":
        normalized_email = normalize_email(email)
        return cls(
            session_scope=session_scope,
            owner_type=USER_OWNER_TYPE,
            owner_id=normalized_email,
            profile_id=_user_profile_id(normalized_email),
            profile_name=USER_PROFILE_NAME,
            fallback_store=fallback_store,
            include_system_fallback=True,
        )

    @classmethod
    def for_system(
        cls,
        *,
        session_scope: SessionScope = streamlit_session_scope,
        fallback_store: ComparisonProfileStore | None = None,
    ) -> "DatabaseComparisonProfileStore":
        return cls(
            session_scope=session_scope,
            owner_type=DEFAULT_OWNER_TYPE,
            owner_id=DEFAULT_OWNER_ID,
            profile_id=DEFAULT_PROFILE_ID,
            profile_name=DEFAULT_PROFILE_NAME,
            fallback_store=fallback_store,
            include_system_fallback=False,
        )

    def _load_by_profile_id(self, profile_id: str, schools: Sequence[str] | None) -> ComparisonProfile | None:
        with self.session_scope() as session:
            result = _execute(
                session,
                """
                SELECT
                    profile_id, profile_name, owner_type, owner_id, base_school,
                    comparison_schools, comparison_groups, is_default, updated_at
                FROM comparison_profiles
                WHERE profile_id = :profile_id
                """,
                {"profile_id": profile_id},
            )
            return _profile_from_row(_fetchone(result), schools)

    def load(self, schools: Sequence[str] | None = None) -> ComparisonProfile:
        try:
            profile = self._load_by_profile_id(self.profile_id, schools)
            if profile is not None:
                return profile

            if self.include_system_fallback:
                system_profile = self._load_by_profile_id(DEFAULT_PROFILE_ID, schools)
                if system_profile is not None:
                    return system_profile
        except Exception as exc:
            raise AppDatabaseError("comparison profile load failed") from exc

        try:
            return self.fallback_store.load(schools)
        except Exception:
            return default_comparison_profile(schools)

    def save(self, profile: ComparisonProfile, schools: Sequence[str] | None = None) -> ComparisonProfile:
        updated_at = _utc_timestamp()
        normalized = normalize_comparison_profile(profile, schools, updated_at=updated_at)
        stored = replace(
            normalized,
            profile_id=self.profile_id,
            profile_name=self.profile_name,
            owner_type=self.owner_type,
            owner_id=self.owner_id,
            is_default=True,
        )

        try:
            with self.session_scope() as session:
                _execute(
                    session,
                    """
                    INSERT INTO comparison_profiles (
                        profile_id, owner_type, owner_id, profile_name, base_school,
                        comparison_schools, comparison_groups, is_default, updated_at
                    )
                    VALUES (
                        :profile_id, :owner_type, :owner_id, :profile_name, :base_school,
                        :comparison_schools, :comparison_groups, :is_default, :updated_at
                    )
                    ON CONFLICT(profile_id) DO UPDATE SET
                        owner_type = :owner_type,
                        owner_id = :owner_id,
                        profile_name = :profile_name,
                        base_school = :base_school,
                        comparison_schools = :comparison_schools,
                        comparison_groups = :comparison_groups,
                        is_default = :is_default,
                        updated_at = :updated_at
                    """,
                    {
                        "profile_id": stored.profile_id,
                        "owner_type": stored.owner_type,
                        "owner_id": stored.owner_id,
                        "profile_name": stored.profile_name,
                        "base_school": stored.base_school,
                        "comparison_schools": json.dumps(list(stored.comparison_schools), ensure_ascii=False),
                        "comparison_groups": json.dumps(
                            [group.to_dict() for group in stored.comparison_groups],
                            ensure_ascii=False,
                        ),
                        "is_default": bool(stored.is_default),
                        "updated_at": stored.updated_at,
                    },
                )
                commit = getattr(session, "commit", None)
                if callable(commit):
                    commit()
        except Exception as exc:
            raise AppDatabaseError("comparison profile save failed") from exc
        return stored

    def delete(self) -> None:
        try:
            with self.session_scope() as session:
                _execute(
                    session,
                    "DELETE FROM comparison_profiles WHERE profile_id = :profile_id",
                    {"profile_id": self.profile_id},
                )
                commit = getattr(session, "commit", None)
                if callable(commit):
                    commit()
        except Exception as exc:
            raise AppDatabaseError("comparison profile delete failed") from exc
