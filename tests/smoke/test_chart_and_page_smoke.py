from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pandas as pd
import pytest

from utils.chart_utils import add_threshold_hline, create_trend_line_chart


ROOT_DIR = Path(__file__).resolve().parents[2]
PAGE_DIR = ROOT_DIR / "pages"


def _iter_streamlit_entrypoints() -> list[Path]:
    return [ROOT_DIR / "app.py", *sorted(PAGE_DIR.glob("*.py"))]


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
        assert "운영자 기본 비교군" in source
        assert "사용자 관리" in source
        assert "기존 사용자 수정" in source

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
