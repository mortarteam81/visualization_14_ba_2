from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

from utils.config import GYOWON_COL_JAEHAK, GYOWON_COL_JEONGWON
from utils.repository.api_repository import ApiUniversityRepository
from utils.repository.base import AbstractUniversityRepository
from utils.repository.csv_repository import CsvUniversityRepository


def _make_raw_gyowon_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "기준연도": [2024, 2023],
            "학교명": ["Alpha University", "Beta University"],
            "본분교명": ["본교", "분교"],
            "설립유형": ["사립", "사립"],
            GYOWON_COL_JEONGWON: [81.0, 79.5],
            GYOWON_COL_JAEHAK: [84.0, 82.5],
        }
    )


def _write_gyowon_csv(data_dir: Path, frame: pd.DataFrame) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    csv_path = data_dir / "전임교원_확보율.csv"
    frame.to_csv(csv_path, index=False, encoding="utf-8-sig")


def _make_api_items() -> list[dict]:
    return [
        {
            "기준연도": "2024",
            "학교명": "Alpha University",
            "본분교구분": "본교",
            "설립유형구분": "사립",
            "전임교원 확보율(학생정원 기준)(%)": "81.0",
            "전임교원 확보율(재학생 기준)(%)": "84.0",
        },
        {
            "기준연도": "2023",
            "학교명": "Beta University",
            "본분교구분": "분교",
            "설립유형구분": "사립",
            "전임교원 확보율(학생정원 기준)(%)": "79.5",
            "전임교원 확보율(재학생 기준)(%)": "82.5",
        },
    ]


@pytest.fixture(params=["csv", "api"], ids=["csv_repository", "api_repository"])
def repository_under_test(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    if request.param == "csv":
        frame = _make_raw_gyowon_frame()
        _write_gyowon_csv(tmp_path, frame)
        return CsvUniversityRepository(data_dir=tmp_path)

    monkeypatch.setattr(
        "utils.repository.api_repository.GYOWON_ENDPOINT",
        "https://example.test/gyowon",
    )
    monkeypatch.setattr(
        "utils.repository.api_repository.GYOWON_COLUMN_MAP",
        {
            "기준연도": "기준연도",
            "학교명": "학교명",
            "본분교구분": "본분교명",
            "설립유형구분": "설립유형",
            "전임교원 확보율(학생정원 기준)(%)": GYOWON_COL_JEONGWON,
            "전임교원 확보율(재학생 기준)(%)": GYOWON_COL_JAEHAK,
        },
    )
    client = MagicMock()
    client.get_all_pages.return_value = _make_api_items()
    return ApiUniversityRepository(client=client)


class TestRepositoryContracts:
    def test_implements_shared_repository_contract(self, repository_under_test: AbstractUniversityRepository) -> None:
        assert isinstance(repository_under_test, AbstractUniversityRepository)

    def test_returns_dataframe_with_required_raw_columns(
        self, repository_under_test: AbstractUniversityRepository
    ) -> None:
        result = repository_under_test.get_gyowon_data()

        assert isinstance(result, pd.DataFrame)
        assert {
            "기준년도",
            "학교명",
            "본분교명",
            "설립유형",
            GYOWON_COL_JEONGWON,
            GYOWON_COL_JAEHAK,
        }.issubset(result.columns)

    def test_preserves_raw_rows_without_service_filtering(
        self, repository_under_test: AbstractUniversityRepository
    ) -> None:
        result = repository_under_test.get_gyowon_data()

        assert len(result) == 2
        assert set(result["설립유형"]) == {"사립"}
        assert set(result["본분교명"]) == {"본교", "분교"}
