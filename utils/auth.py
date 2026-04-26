"""Streamlit authentication and authorization helpers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import streamlit as st

from utils.app_db import (
    AppDatabaseError,
    AppUserStore,
    ROLE_ADMIN,
    ROLE_VIEWER,
    bootstrap_app_database,
    normalize_email,
    normalize_role,
    streamlit_session_scope,
)


AUTH_SESSION_KEY = "authenticated_user"
AUTH_EMAIL_SESSION_KEY = "authenticated_user_email"
DB_BOOTSTRAPPED_SESSION_KEY = "app_db_bootstrapped"
LOGIN_RECORDED_SESSION_KEY = "app_login_recorded_email"


@dataclass(frozen=True)
class AuthenticatedUser:
    email: str
    name: str
    role: str
    is_admin: bool


def _role_label(role: str) -> str:
    return "운영자" if role == ROLE_ADMIN else "조회 사용자"


def parse_initial_admin_emails(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        candidates = value.replace("\n", ",").split(",")
    else:
        try:
            candidates = list(value)
        except TypeError:
            candidates = []
    normalized: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        email = normalize_email(candidate)
        if email and email not in seen:
            normalized.append(email)
            seen.add(email)
    return tuple(normalized)


def initial_admin_emails_from_secrets(secrets: Mapping[str, object] | None = None) -> tuple[str, ...]:
    source: object
    if secrets is None:
        try:
            source = st.secrets
        except FileNotFoundError:
            return ()
    else:
        source = secrets

    try:
        app_auth = source.get("app_auth", {})  # type: ignore[attr-defined]
    except AttributeError:
        return ()
    if not _is_gettable(app_auth):
        return ()
    return parse_initial_admin_emails(app_auth.get("initial_admin_emails"))  # type: ignore[attr-defined]


def _is_gettable(value: object) -> bool:
    return callable(getattr(value, "get", None))


def _secret_section(name: str) -> object:
    try:
        section = st.secrets.get(name, {})
    except FileNotFoundError:
        return {}
    return section if _is_gettable(section) else {}


def _has_google_auth_config() -> bool:
    auth = _secret_section("auth")
    required_keys = ("redirect_uri", "cookie_secret", "client_id", "client_secret", "server_metadata_url")
    return all(bool(auth.get(key)) for key in required_keys)  # type: ignore[attr-defined]


def _has_neon_config() -> bool:
    connections = _secret_section("connections")
    neon = connections.get("neon") if _is_gettable(connections) else None  # type: ignore[attr-defined]
    return _is_gettable(neon) and bool(neon.get("url"))  # type: ignore[attr-defined]


def _is_logged_in() -> bool:
    return bool(getattr(getattr(st, "user", None), "is_logged_in", False))


def _user_claims() -> dict[str, object]:
    user = getattr(st, "user", {})
    to_dict = getattr(user, "to_dict", None)
    if callable(to_dict):
        return dict(to_dict())
    try:
        return dict(user)
    except TypeError:
        return {}


def _render_login() -> None:
    st.title("로그인")
    st.caption("지정된 사용자만 접근할 수 있는 대학 경영 인사이트 대시보드입니다.")
    st.button("Google로 로그인", type="primary", on_click=st.login)
    st.stop()


def _render_unauthorized(email: str) -> None:
    st.title("접근 권한이 없습니다")
    st.error("이 계정은 아직 대시보드 사용 권한이 없거나 비활성화되어 있습니다.")
    st.caption(f"로그인 계정: {email}")
    st.button("다른 계정으로 로그인", on_click=st.logout)
    st.stop()


def _render_account_controls(authenticated_user: AuthenticatedUser) -> None:
    with st.sidebar:
        st.divider()
        st.caption("로그인 계정")
        st.write(authenticated_user.email)
        st.caption(f"권한: {_role_label(authenticated_user.role)}")
        st.button("로그아웃", key="auth_logout_button", on_click=st.logout, use_container_width=True)


def _ensure_database_ready() -> tuple[str, ...]:
    if not _has_neon_config():
        st.error("Neon DB 연결 설정이 필요합니다. Streamlit secrets의 [connections.neon] 설정을 확인해 주세요.")
        st.stop()

    initial_admin_emails = initial_admin_emails_from_secrets()
    if not st.session_state.get(DB_BOOTSTRAPPED_SESSION_KEY):
        bootstrap_app_database(streamlit_session_scope, initial_admin_emails)
        st.session_state[DB_BOOTSTRAPPED_SESSION_KEY] = True
    return initial_admin_emails


def require_authenticated_user() -> AuthenticatedUser:
    """Require Google OIDC login and an active DB allowlist record."""

    if not _is_logged_in():
        _render_login()

    claims = _user_claims()
    email = normalize_email(claims.get("email"))
    name = str(claims.get("name") or claims.get("given_name") or email)
    if not email:
        st.error("Google 계정 이메일을 확인할 수 없습니다.")
        st.button("다른 계정으로 로그인", on_click=st.logout)
        st.stop()
    if claims.get("email_verified") is False:
        st.error("이메일 인증이 완료된 Google 계정만 사용할 수 있습니다.")
        st.button("다른 계정으로 로그인", on_click=st.logout)
        st.stop()

    try:
        _ensure_database_ready()
        user_store = AppUserStore(streamlit_session_scope)
        record = user_store.get_user(email)
    except AppDatabaseError:
        st.error("사용자 권한 DB를 초기화하거나 조회하지 못했습니다.")
        st.caption("Neon 연결 문자열과 app_users 테이블 권한을 확인해 주세요.")
        st.stop()

    if record is None or not record.is_active:
        _render_unauthorized(email)

    if st.session_state.get(LOGIN_RECORDED_SESSION_KEY) != email:
        try:
            user_store.record_login(email)
            st.session_state[LOGIN_RECORDED_SESSION_KEY] = email
        except AppDatabaseError:
            pass

    role = normalize_role(record.role)
    authenticated_user = AuthenticatedUser(
        email=email,
        name=record.display_name or name or email,
        role=role,
        is_admin=role == ROLE_ADMIN,
    )
    st.session_state[AUTH_SESSION_KEY] = authenticated_user
    st.session_state[AUTH_EMAIL_SESSION_KEY] = authenticated_user.email
    _render_account_controls(authenticated_user)
    return authenticated_user


__all__ = [
    "AuthenticatedUser",
    "ROLE_ADMIN",
    "ROLE_VIEWER",
    "parse_initial_admin_emails",
    "initial_admin_emails_from_secrets",
    "require_authenticated_user",
]
