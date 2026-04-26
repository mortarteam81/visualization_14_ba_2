from __future__ import annotations

from contextlib import contextmanager
import sqlite3
from typing import Iterator

from utils.app_db import AppUserStore, ROLE_ADMIN, ROLE_VIEWER, bootstrap_app_database
from utils.comparison_profile import ComparisonGroup, ComparisonProfile
from utils.profile_db import DatabaseComparisonProfileStore


SCHOOLS = [
    "성신여자대학교",
    "숙명여자대학교",
    "덕성여자대학교",
    "서울여자대학교",
]


class SqliteSession:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def execute(self, statement: object, params: dict[str, object] | None = None) -> sqlite3.Cursor:
        return self.connection.execute(str(statement), params or {})

    def commit(self) -> None:
        self.connection.commit()


@contextmanager
def sqlite_session_scope(connection: sqlite3.Connection) -> Iterator[SqliteSession]:
    yield SqliteSession(connection)


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    return connection


def _profile(base_school: str, comparisons: tuple[str, ...]) -> ComparisonProfile:
    return ComparisonProfile(
        profile_id="draft",
        profile_name="테스트 비교군",
        owner_type="draft",
        owner_id="draft",
        base_school=base_school,
        comparison_schools=comparisons,
        comparison_groups=(ComparisonGroup("그룹", comparisons),),
        is_default=True,
        updated_at="",
    )


def test_bootstrap_app_database_upserts_initial_admin() -> None:
    connection = _connection()
    scope = lambda: sqlite_session_scope(connection)

    bootstrap_app_database(scope, [" Admin@Example.com "])
    user = AppUserStore(scope).get_user("admin@example.com")

    assert user is not None
    assert user.role == ROLE_ADMIN
    assert user.is_active is True


def test_app_user_store_upserts_viewer_and_inactive_state() -> None:
    connection = _connection()
    scope = lambda: sqlite_session_scope(connection)
    bootstrap_app_database(scope, [])

    user = AppUserStore(scope).upsert_user(
        email="viewer@example.com",
        display_name="Viewer",
        role=ROLE_VIEWER,
        is_active=False,
    )

    assert user.email == "viewer@example.com"
    assert user.role == ROLE_VIEWER
    assert user.is_active is False


def test_database_comparison_profile_store_uses_user_then_system_default() -> None:
    connection = _connection()
    scope = lambda: sqlite_session_scope(connection)
    bootstrap_app_database(scope, [])

    system_store = DatabaseComparisonProfileStore.for_system(session_scope=scope)
    user_store = DatabaseComparisonProfileStore.for_user("viewer@example.com", session_scope=scope)
    system_store.save(_profile("성신여자대학교", ("숙명여자대학교",)), SCHOOLS)

    inherited = user_store.load(SCHOOLS)
    assert inherited.owner_type == "system"
    assert inherited.base_school == "성신여자대학교"
    assert inherited.comparison_schools == ("숙명여자대학교",)

    user_store.save(_profile("숙명여자대학교", ("덕성여자대학교", "서울여자대학교")), SCHOOLS)
    user_profile = user_store.load(SCHOOLS)

    assert user_profile.owner_type == "user"
    assert user_profile.owner_id == "viewer@example.com"
    assert user_profile.base_school == "숙명여자대학교"
    assert user_profile.comparison_schools == ("덕성여자대학교", "서울여자대학교")
