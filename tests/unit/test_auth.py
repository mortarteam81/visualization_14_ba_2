from __future__ import annotations

from utils.app_db import ROLE_ADMIN, ROLE_VIEWER, AppUserRecord, normalize_email, normalize_role
from utils.auth import missing_runtime_dependencies, parse_initial_admin_emails


def test_normalize_email_strips_and_lowercases() -> None:
    assert normalize_email(" Admin@Example.COM ") == "admin@example.com"


def test_normalize_role_defaults_to_viewer() -> None:
    assert normalize_role(ROLE_ADMIN) == ROLE_ADMIN
    assert normalize_role("unknown") == ROLE_VIEWER


def test_parse_initial_admin_emails_accepts_list_and_comma_string() -> None:
    assert parse_initial_admin_emails([" Admin@Example.com ", "admin@example.com"]) == ("admin@example.com",)
    assert parse_initial_admin_emails("one@example.com, two@example.com\nONE@example.com") == (
        "one@example.com",
        "two@example.com",
    )


def test_missing_runtime_dependencies_reports_missing_packages() -> None:
    installed = {"authlib"}

    def fake_find_spec(module_name: str) -> object | None:
        return object() if module_name in installed else None

    assert missing_runtime_dependencies(fake_find_spec) == (
        "sqlalchemy>=2.0.0",
        "psycopg2-binary>=2.9.9",
    )


def test_app_user_record_admin_flag() -> None:
    admin = AppUserRecord(
        email="admin@example.com",
        display_name="Admin",
        role=ROLE_ADMIN,
        is_active=True,
        created_at="",
        updated_at="",
        last_login_at="",
    )
    viewer = AppUserRecord(
        email="viewer@example.com",
        display_name="Viewer",
        role=ROLE_VIEWER,
        is_active=True,
        created_at="",
        updated_at="",
        last_login_at="",
    )

    assert admin.is_admin is True
    assert viewer.is_admin is False
