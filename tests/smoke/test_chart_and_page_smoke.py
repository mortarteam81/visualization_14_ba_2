from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from utils.auth import AuthenticatedUser, ROLE_ADMIN
from utils.chart_utils import add_threshold_hline, create_trend_line_chart


ROOT_DIR = Path(__file__).resolve().parents[2]
PAGE_DIR = ROOT_DIR / "pages"


def _iter_streamlit_entrypoints() -> list[Path]:
    return [ROOT_DIR / "app.py", *sorted(PAGE_DIR.glob("*.py"))]


def _iter_metric_pages() -> list[Path]:
    return sorted(PAGE_DIR.glob("[1-9]*.py"))


def _fake_authenticated_user() -> AuthenticatedUser:
    return AuthenticatedUser(
        email="qa@example.com",
        name="QA",
        role=ROLE_ADMIN,
        is_admin=True,
    )


class TestChartSmoke:
    def test_create_trend_line_chart_returns_figure(self) -> None:
        frame = pd.DataFrame(
            {
                "year": [2023, 2024],
                "value": [1.0, 2.0],
                "school": ["Alpha", "Alpha"],
            }
        )

        figure = create_trend_line_chart(
            frame,
            x="year",
            y="value",
            color="school",
            title="Smoke",
        )

        assert figure.data
        assert figure.layout.title.text == "Smoke"

    def test_create_trend_line_chart_accepts_custom_hovermode(self) -> None:
        frame = pd.DataFrame(
            {
                "year": [2023, 2024],
                "value": [1.0, 2.0],
                "school": ["Alpha", "Alpha"],
            }
        )

        figure = create_trend_line_chart(
            frame,
            x="year",
            y="value",
            color="school",
            title="Hover",
            hovermode="closest",
        )

        assert figure.layout.hovermode == "closest"

    def test_add_threshold_hline_appends_shape(self) -> None:
        frame = pd.DataFrame(
            {
                "year": [2023, 2024],
                "value": [1.0, 2.0],
                "school": ["Alpha", "Alpha"],
            }
        )
        figure = create_trend_line_chart(frame, x="year", y="value", color="school", title="Threshold")

        updated = add_threshold_hline(figure, threshold=1.5, label="Cut line")

        assert len(updated.layout.shapes) == 1
        assert updated.layout.annotations[0].text == "Cut line"


class TestPageSmoke:
    @pytest.mark.parametrize("path", _iter_streamlit_entrypoints(), ids=lambda path: path.name)
    def test_streamlit_entrypoint_parses(self, path: Path) -> None:
        source = path.read_text(encoding="utf-8")
        ast.parse(source, filename=str(path))

    @pytest.mark.parametrize("path", _iter_streamlit_entrypoints(), ids=lambda path: path.name)
    def test_streamlit_entrypoint_sets_page_config(self, path: Path) -> None:
        module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

        assert any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "set_page_config"
            for node in ast.walk(module)
        ), f"{path.name} should call st.set_page_config()"

    @pytest.mark.parametrize("path", _iter_streamlit_entrypoints(), ids=lambda path: path.name)
    def test_streamlit_entrypoint_requires_authenticated_user(self, path: Path) -> None:
        module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

        assert any(
            isinstance(node, ast.Call)
            and (
                (isinstance(node.func, ast.Name) and node.func.id == "require_authenticated_user")
                or (isinstance(node.func, ast.Attribute) and node.func.attr == "require_authenticated_user")
            )
            for node in ast.walk(module)
        ), f"{path.name} should require an authenticated user"

    def test_comparison_settings_gates_admin_sections(self) -> None:
        source = (PAGE_DIR / "00_비교대학_설정.py").read_text(encoding="utf-8")

        assert "auth_user.is_admin" in source
        assert "기본 비교군 설정" in source
        assert "운영자 기본 비교군" in source
        assert "사용자 관리" in source
        assert "기존 사용자 수정" in source

    def test_metric_pages_key_school_selection_by_metric_id(self) -> None:
        missing_key_prefix: list[str] = []
        for path in PAGE_DIR.glob("*.py"):
            source = path.read_text(encoding="utf-8")
            if "render_school_sidebar(" not in source:
                continue
            module = ast.parse(source, filename=str(path))
            for node in ast.walk(module):
                if not (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "render_school_sidebar"
                ):
                    continue
                if not any(keyword.arg == "key_prefix" for keyword in node.keywords):
                    missing_key_prefix.append(path.name)

        assert missing_key_prefix == []

    def test_authenticated_user_can_logout_from_sidebar(self) -> None:
        source = (ROOT_DIR / "utils" / "auth.py").read_text(encoding="utf-8")

        assert "로그아웃" in source
        assert "st.logout" in source

    @pytest.mark.parametrize(
        "module_name",
        [
            "utils.chart_utils",
            "utils.comparison_charts",
            "utils.comparison_page",
            "utils.comparison_profile",
            "utils.comparison_sidebar",
            "utils.auth",
            "utils.app_db",
            "utils.profile_db",
            "utils.ai_prompts.management",
            "utils.management_ai",
            "utils.management_insights",
            "utils.ui.kpi",
            "utils.ui.renderers",
            "utils.ui.tables",
        ],
    )
    def test_shared_page_modules_import(self, module_name: str) -> None:
        importlib.import_module(module_name)

    @pytest.mark.parametrize("path", [ROOT_DIR / "app.py", PAGE_DIR / "0_경영_인사이트_대시보드.py", *_iter_metric_pages()], ids=lambda path: path.name)
    def test_mobile_compact_pages_run_without_exceptions(self, path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import utils.auth as auth

        monkeypatch.setattr(auth, "require_authenticated_user", _fake_authenticated_user)
        app = AppTest.from_file(str(path), default_timeout=20)
        app.session_state["mobile_compact_mode"] = True

        app.run()

        assert [exception.message for exception in app.exception] == []

    @pytest.mark.parametrize("path", _iter_metric_pages(), ids=lambda path: path.name)
    def test_mobile_compact_metric_pages_hide_comparison_multiselects(
        self,
        path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import utils.auth as auth

        monkeypatch.setattr(auth, "require_authenticated_user", _fake_authenticated_user)
        app = AppTest.from_file(str(path), default_timeout=20)
        app.session_state["mobile_compact_mode"] = True

        app.run()

        assert [exception.message for exception in app.exception] == []
        assert len(app.multiselect) == 0
        assert any("최근연도 비교" in subheader.value for subheader in app.subheader)

    def test_mobile_compact_management_hides_comparison_school_picker(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import utils.auth as auth

        monkeypatch.setattr(auth, "require_authenticated_user", _fake_authenticated_user)
        app = AppTest.from_file(str(PAGE_DIR / "0_경영_인사이트_대시보드.py"), default_timeout=20)
        app.session_state["mobile_compact_mode"] = True

        app.run()

        assert [exception.message for exception in app.exception] == []
        assert [multiselect.label for multiselect in app.multiselect] == ["지표 영역"]

    def test_mobile_compact_management_correlation_uses_table_summary(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import utils.auth as auth

        monkeypatch.setattr(auth, "require_authenticated_user", _fake_authenticated_user)
        app = AppTest.from_file(str(PAGE_DIR / "0_경영_인사이트_대시보드.py"), default_timeout=20)
        app.session_state["mobile_compact_mode"] = True
        app.session_state["management_compact_section"] = "상관관계"

        app.run()

        assert [exception.message for exception in app.exception] == []
        assert any(
            "모바일에서는 히트맵 대신 상관 강도가 큰 지표 조합을 표로 보여줍니다" in caption.value
            for caption in app.caption
        )
        assert len(app.dataframe) >= 1
