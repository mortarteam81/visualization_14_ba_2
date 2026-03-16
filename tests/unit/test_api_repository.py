"""
ApiUniversityRepository 단위 테스트

DataGoKrClient를 Mock으로 대체하여 실제 API 호출 없이 테스트합니다.
"""

import pandas as pd
import pytest
from unittest.mock import MagicMock

from utils.config import GYOWON_COL_JEONGWON, GYOWON_COL_JAEHAK
from utils.repository.api_repository import ApiUniversityRepository


# ── 헬퍼 ─────────────────────────────────────────────────────────────────────

def _make_mock_client(items: list[dict]) -> MagicMock:
    """
    get_all_pages()가 items를 반환하는 Mock 클라이언트를 생성합니다.
    """
    mock_client = MagicMock()
    mock_client.get_all_pages.return_value = items
    return mock_client


# ── 정상 동작 테스트 ─────────────────────────────────────────────────────────

class TestApiRepositoryGetGyowonData:
    """ApiUniversityRepository.get_gyowon_data() 검증"""

    def test_returns_dataframe(self, mock_api_items, monkeypatch):
        """API 응답이 DataFrame으로 반환되어야 합니다."""
        # GYOWON_ENDPOINT가 비어 있으면 ValueError가 발생하므로 임시로 설정
        monkeypatch.setattr(
            "utils.repository.api_repository.GYOWON_ENDPOINT",
            "https://api.example.com/gyowon"
        )
        client = _make_mock_client(mock_api_items)
        repo = ApiUniversityRepository(client=client)
        result = repo.get_gyowon_data()
        assert isinstance(result, pd.DataFrame)

    def test_maps_columns_using_column_map(self, mock_api_items, monkeypatch):
        """
        GYOWON_COLUMN_MAP에 따라 API 컬럼명이 내부 표준 컬럼명으로 변환되어야 합니다.

        예: '본분교구분' → '본분교명', '설립유형구분' → '설립유형'
        """
        monkeypatch.setattr(
            "utils.repository.api_repository.GYOWON_ENDPOINT",
            "https://api.example.com/gyowon"
        )
        # 테스트용 컬럼 매핑 (실제 endpoints.py의 GYOWON_COLUMN_MAP과 동일한 형태)
        test_map = {
            "기준년도":                         "기준년도",
            "학교명":                           "학교명",
            "본분교구분":                        "본분교명",
            "설립유형구분":                      "설립유형",
            "전임교원확보율(학생정원기준)(%)":      GYOWON_COL_JEONGWON,
            "전임교원확보율(재학생기준)(%)":        GYOWON_COL_JAEHAK,
        }
        monkeypatch.setattr(
            "utils.repository.api_repository.GYOWON_COLUMN_MAP",
            test_map
        )
        client = _make_mock_client(mock_api_items)
        repo = ApiUniversityRepository(client=client)
        result = repo.get_gyowon_data()

        # 매핑 후 내부 표준 컬럼명이 존재해야 함
        assert "본분교명" in result.columns
        assert "설립유형" in result.columns
        assert GYOWON_COL_JEONGWON in result.columns
        assert GYOWON_COL_JAEHAK in result.columns

    def test_calls_get_all_pages_with_endpoint(self, mock_api_items, monkeypatch):
        """get_all_pages()가 GYOWON_ENDPOINT URL로 호출되어야 합니다."""
        test_endpoint = "https://api.example.com/gyowon"
        monkeypatch.setattr(
            "utils.repository.api_repository.GYOWON_ENDPOINT",
            test_endpoint
        )
        client = _make_mock_client(mock_api_items)
        repo = ApiUniversityRepository(client=client)
        repo.get_gyowon_data()

        client.get_all_pages.assert_called_once_with(test_endpoint)

    def test_row_count_matches_api_response(self, mock_api_items, monkeypatch):
        """반환 DataFrame의 행 수가 API 응답 항목 수와 일치해야 합니다."""
        monkeypatch.setattr(
            "utils.repository.api_repository.GYOWON_ENDPOINT",
            "https://api.example.com/gyowon"
        )
        client = _make_mock_client(mock_api_items)
        repo = ApiUniversityRepository(client=client)
        result = repo.get_gyowon_data()

        assert len(result) == len(mock_api_items)


# ── 오류 처리 테스트 ─────────────────────────────────────────────────────────

class TestApiRepositoryErrors:
    """ApiUniversityRepository 오류 처리 검증"""

    def test_raises_when_endpoint_not_configured(self):
        """GYOWON_ENDPOINT가 빈 문자열이면 ValueError가 발생해야 합니다."""
        # endpoints.py의 기본값이 "" 이므로 별도 monkeypatch 없이도 테스트됨
        # 단, 다른 테스트에서 monkeypatch가 살아 있을 수 있으므로 명시적으로 확인
        import utils.repository.api_repository as mod
        original = mod.GYOWON_ENDPOINT
        mod.GYOWON_ENDPOINT = ""  # 빈 문자열로 강제 설정
        try:
            client = _make_mock_client([])
            repo = ApiUniversityRepository(client=client)
            with pytest.raises(ValueError, match="엔드포인트"):
                repo.get_gyowon_data()
        finally:
            mod.GYOWON_ENDPOINT = original  # 원복

    def test_raises_when_api_returns_empty(self, monkeypatch):
        """API 응답이 빈 리스트이면 ValueError가 발생해야 합니다."""
        monkeypatch.setattr(
            "utils.repository.api_repository.GYOWON_ENDPOINT",
            "https://api.example.com/gyowon"
        )
        client = _make_mock_client([])  # 빈 응답
        repo = ApiUniversityRepository(client=client)
        with pytest.raises(ValueError, match="데이터가 없습니다"):
            repo.get_gyowon_data()
