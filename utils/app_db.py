"""Database helpers for app users and persisted comparison profiles."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable, Iterator, Sequence


ROLE_ADMIN = "admin"
ROLE_VIEWER = "viewer"
VALID_ROLES = (ROLE_ADMIN, ROLE_VIEWER)


class AppDatabaseError(RuntimeError):
    """Raised when the app database cannot be reached or initialized."""


@dataclass(frozen=True)
class AppUserRecord:
    email: str
    display_name: str
    role: str
    is_active: bool
    created_at: str
    updated_at: str
    last_login_at: str

    @property
    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN


SessionScope = Callable[[], Any]


def normalize_email(value: object) -> str:
    return str(value or "").strip().lower()


def normalize_role(value: object) -> str:
    role = str(value or "").strip().lower()
    return role if role in VALID_ROLES else ROLE_VIEWER


def _statement(sql: str) -> object:
    try:
        from sqlalchemy import text
    except ModuleNotFoundError:
        return sql
    return text(sql)


def _execute(session: Any, sql: str, params: dict[str, Any] | None = None) -> Any:
    return session.execute(_statement(sql), params or {})


def _commit(session: Any) -> None:
    commit = getattr(session, "commit", None)
    if callable(commit):
        commit()


def _row_mapping(row: Any, columns: Sequence[str]) -> dict[str, Any]:
    if row is None:
        return {}
    if hasattr(row, "_mapping"):
        return dict(row._mapping)
    if isinstance(row, dict):
        return row
    try:
        return {column: row[column] for column in columns}
    except (TypeError, KeyError, IndexError):
        return dict(zip(columns, row))


def _fetchone(result: Any) -> Any:
    fetchone = getattr(result, "fetchone", None)
    if callable(fetchone):
        return fetchone()
    first = getattr(result, "first", None)
    if callable(first):
        return first()
    return None


def _fetchall(result: Any) -> list[Any]:
    fetchall = getattr(result, "fetchall", None)
    if callable(fetchall):
        return list(fetchall())
    all_rows = getattr(result, "all", None)
    if callable(all_rows):
        return list(all_rows())
    return []


def _bool_value(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "t", "yes", "y"}
    return bool(value)


def _user_from_row(row: Any) -> AppUserRecord | None:
    columns = (
        "email",
        "display_name",
        "role",
        "is_active",
        "created_at",
        "updated_at",
        "last_login_at",
    )
    mapping = _row_mapping(row, columns)
    if not mapping:
        return None
    return AppUserRecord(
        email=normalize_email(mapping.get("email")),
        display_name=str(mapping.get("display_name") or ""),
        role=normalize_role(mapping.get("role")),
        is_active=_bool_value(mapping.get("is_active")),
        created_at=str(mapping.get("created_at") or ""),
        updated_at=str(mapping.get("updated_at") or ""),
        last_login_at=str(mapping.get("last_login_at") or ""),
    )


@contextmanager
def streamlit_session_scope(connection_name: str = "neon") -> Iterator[Any]:
    import streamlit as st

    connection = st.connection(connection_name, type="sql")
    with connection.session as session:
        yield session


def bootstrap_app_database(session_scope: SessionScope, initial_admin_emails: Sequence[str]) -> None:
    """Create app tables and enforce configured initial admins."""

    try:
        with session_scope() as session:
            _execute(
                session,
                """
                CREATE TABLE IF NOT EXISTS app_users (
                    email TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL DEFAULT '',
                    role TEXT NOT NULL CHECK (role IN ('admin', 'viewer')),
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_login_at TIMESTAMP
                )
                """,
            )
            _execute(
                session,
                """
                CREATE TABLE IF NOT EXISTS comparison_profiles (
                    profile_id TEXT PRIMARY KEY,
                    owner_type TEXT NOT NULL CHECK (owner_type IN ('system', 'user')),
                    owner_id TEXT NOT NULL,
                    profile_name TEXT NOT NULL,
                    base_school TEXT NOT NULL,
                    comparison_schools TEXT NOT NULL,
                    comparison_groups TEXT NOT NULL,
                    is_default BOOLEAN NOT NULL DEFAULT TRUE,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """,
            )
            for email in {normalize_email(email) for email in initial_admin_emails if normalize_email(email)}:
                _execute(
                    session,
                    """
                    INSERT INTO app_users (
                        email, display_name, role, is_active, created_at, updated_at
                    )
                    VALUES (:email, :display_name, 'admin', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT(email) DO UPDATE SET
                        role = 'admin',
                        is_active = TRUE,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    {"email": email, "display_name": email},
                )
            _commit(session)
    except Exception as exc:  # pragma: no cover - message is intentionally sanitized in UI
        raise AppDatabaseError("app database bootstrap failed") from exc


class AppUserStore:
    def __init__(self, session_scope: SessionScope = streamlit_session_scope) -> None:
        self.session_scope = session_scope

    def get_user(self, email: str) -> AppUserRecord | None:
        normalized_email = normalize_email(email)
        if not normalized_email:
            return None
        try:
            with self.session_scope() as session:
                result = _execute(
                    session,
                    """
                    SELECT email, display_name, role, is_active, created_at, updated_at, last_login_at
                    FROM app_users
                    WHERE email = :email
                    """,
                    {"email": normalized_email},
                )
                return _user_from_row(_fetchone(result))
        except Exception as exc:
            raise AppDatabaseError("app user lookup failed") from exc

    def list_users(self) -> list[AppUserRecord]:
        try:
            with self.session_scope() as session:
                result = _execute(
                    session,
                    """
                    SELECT email, display_name, role, is_active, created_at, updated_at, last_login_at
                    FROM app_users
                    ORDER BY CASE role WHEN 'admin' THEN 0 ELSE 1 END, email
                    """,
                )
                return [user for user in (_user_from_row(row) for row in _fetchall(result)) if user is not None]
        except Exception as exc:
            raise AppDatabaseError("app user list failed") from exc

    def upsert_user(
        self,
        *,
        email: str,
        display_name: str = "",
        role: str = ROLE_VIEWER,
        is_active: bool = True,
    ) -> AppUserRecord:
        normalized_email = normalize_email(email)
        if not normalized_email:
            raise ValueError("email is required")
        normalized_role = normalize_role(role)
        try:
            with self.session_scope() as session:
                _execute(
                    session,
                    """
                    INSERT INTO app_users (
                        email, display_name, role, is_active, created_at, updated_at
                    )
                    VALUES (
                        :email, :display_name, :role, :is_active, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                    ON CONFLICT(email) DO UPDATE SET
                        display_name = :display_name,
                        role = :role,
                        is_active = :is_active,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    {
                        "email": normalized_email,
                        "display_name": display_name.strip() or normalized_email,
                        "role": normalized_role,
                        "is_active": bool(is_active),
                    },
                )
                _commit(session)
            record = self.get_user(normalized_email)
            if record is None:
                raise AppDatabaseError("app user upsert did not return a record")
            return record
        except ValueError:
            raise
        except Exception as exc:
            raise AppDatabaseError("app user upsert failed") from exc

    def record_login(self, email: str) -> None:
        normalized_email = normalize_email(email)
        if not normalized_email:
            return
        try:
            with self.session_scope() as session:
                _execute(
                    session,
                    """
                    UPDATE app_users
                    SET last_login_at = CURRENT_TIMESTAMP
                    WHERE email = :email
                    """,
                    {"email": normalized_email},
                )
                _commit(session)
        except Exception as exc:
            raise AppDatabaseError("app user login update failed") from exc
