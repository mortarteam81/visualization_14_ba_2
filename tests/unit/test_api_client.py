"""
DataGoKrClient 단위 테스트

TDD Red 단계에서 작성: 구현 전에 기대 동작을 명세합니다.
requests.Session.get을 mock하여 외부 네트워크 의존성을 완전히 격리합니다.

테스트 분류:
- TestDataGoKrClientInit   : 초기화 검증
- TestDataGoKrClientGet    : 단일 GET 요청 검증
- TestGetAllPages          : 페이지네이션 검증
"""

import pytest
import requests

from utils.api.client import DataGoKrClient

# 테스트용 상수 (실제 API를 호출하지 않음)
_DUMMY_URL = "https://api.odcloud.kr/api/test/v1/data"
_DUMMY_KEY = "test_api_key_1234"


# ── 헬퍼 ─────────────────────────────────────────────────────────────────────

def _make_mock_get(mocker, json_response: dict):
    """requests.Session.get을 mock하고 json_response를 반환하도록 설정합니다."""
    mock = mocker.patch("requests.Session.get")
    mock.return_value.json.return_value = json_response
    mock.return_value.raise_for_status = lambda: None
    return mock


# ── 초기화 테스트 ─────────────────────────────────────────────────────────────

class TestDataGoKrClientInit:
    """DataGoKrClient 생성자 검증"""

    def test_raises_when_api_key_is_empty_string(self):
        """빈 문자열 API 키로 생성 시 ValueError가 발생해야 합니다."""
        with pytest.raises(ValueError, match="API 키"):
            DataGoKrClient(api_key="")

    def test_raises_when_api_key_is_none(self):
        """None API 키로 생성 시 ValueError가 발생해야 합니다."""
        with pytest.raises(ValueError):
            DataGoKrClient(api_key=None)

    def test_creates_with_valid_key(self):
        """유효한 API 키로 정상 생성되어야 합니다."""
        client = DataGoKrClient(api_key=_DUMMY_KEY)
        assert client.api_key == _DUMMY_KEY

    def test_default_timeout_is_10(self):
        """기본 타임아웃은 10초여야 합니다."""
        client = DataGoKrClient(api_key=_DUMMY_KEY)
        assert client.timeout == 10

    def test_custom_timeout(self):
        """커스텀 타임아웃이 적용되어야 합니다."""
        client = DataGoKrClient(api_key=_DUMMY_KEY, timeout=30)
        assert client.timeout == 30


# ── 단일 GET 요청 테스트 ──────────────────────────────────────────────────────

class TestDataGoKrClientGet:
    """DataGoKrClient.get() 메서드 검증"""

    def test_includes_service_key_in_params(self, mocker):
        """요청 파라미터에 serviceKey가 자동으로 포함되어야 합니다."""
        # _make_mock_get이 반환하는 mock 객체를 변수에 저장하여 재사용
        mock = _make_mock_get(mocker, {"data": [], "totalCount": 0})

        client = DataGoKrClient(api_key=_DUMMY_KEY)
        client.get(_DUMMY_URL)

        # 동일한 mock 객체에서 호출 파라미터를 검증
        sent_params = mock.call_args.kwargs["params"]
        assert sent_params["serviceKey"] == _DUMMY_KEY

    def test_includes_json_type_in_params(self, mocker):
        """요청 파라미터에 type=json이 자동으로 포함되어야 합니다."""
        mock = _make_mock_get(mocker, {"data": [], "totalCount": 0})

        client = DataGoKrClient(api_key=_DUMMY_KEY)
        client.get(_DUMMY_URL)

        sent_params = mock.call_args.kwargs["params"]
        assert sent_params["type"] == "json"

    def test_merges_additional_params(self, mocker):
        """추가 파라미터가 기본 파라미터와 합쳐져야 합니다."""
        mock = _make_mock_get(mocker, {"data": [], "totalCount": 0})

        client = DataGoKrClient(api_key=_DUMMY_KEY)
        client.get(_DUMMY_URL, params={"year": 2024})

        sent_params = mock.call_args.kwargs["params"]
        assert sent_params["year"] == 2024
        assert sent_params["serviceKey"] == _DUMMY_KEY

    def test_raises_on_http_error(self, mocker):
        """HTTP 오류 응답(4xx/5xx) 시 HTTPError를 발생시켜야 합니다."""
        mock = mocker.patch("requests.Session.get")
        mock.return_value.raise_for_status.side_effect = requests.HTTPError("404 Not Found")

        client = DataGoKrClient(api_key=_DUMMY_KEY)
        with pytest.raises(requests.HTTPError):
            client.get(_DUMMY_URL)

    def test_raises_on_timeout(self, mocker):
        """타임아웃 발생 시 Timeout 예외가 전파되어야 합니다."""
        mock = mocker.patch("requests.Session.get")
        mock.side_effect = requests.Timeout

        client = DataGoKrClient(api_key=_DUMMY_KEY)
        with pytest.raises(requests.Timeout):
            client.get(_DUMMY_URL)

    def test_raises_on_connection_error(self, mocker):
        """네트워크 연결 오류 시 ConnectionError가 전파되어야 합니다."""
        mock = mocker.patch("requests.Session.get")
        mock.side_effect = requests.ConnectionError

        client = DataGoKrClient(api_key=_DUMMY_KEY)
        with pytest.raises(requests.ConnectionError):
            client.get(_DUMMY_URL)

    def test_returns_parsed_json(self, mocker):
        """성공 응답의 JSON이 파싱된 dict로 반환되어야 합니다."""
        expected = {"data": [{"학교명": "성신여자대학교"}], "totalCount": 1}
        _make_mock_get(mocker, expected)

        client = DataGoKrClient(api_key=_DUMMY_KEY)
        result = client.get(_DUMMY_URL)

        assert result == expected

    def test_uses_timeout_from_instance(self, mocker):
        """인스턴스에 설정된 timeout 값이 요청에 사용되어야 합니다."""
        mock = _make_mock_get(mocker, {"data": [], "totalCount": 0})

        client = DataGoKrClient(api_key=_DUMMY_KEY, timeout=15)
        client.get(_DUMMY_URL)

        assert mock.call_args.kwargs["timeout"] == 15


# ── 페이지네이션 테스트 ───────────────────────────────────────────────────────

class TestGetAllPages:
    """DataGoKrClient.get_all_pages() 페이지네이션 검증"""

    def test_returns_all_items_single_page(self, mocker):
        """1페이지에 모든 데이터가 들어올 때 한 번만 요청해야 합니다."""
        response = {"data": [{"학교명": "성신여자대학교"}], "totalCount": 1}
        mock = _make_mock_get(mocker, response)

        client = DataGoKrClient(api_key=_DUMMY_KEY)
        result = client.get_all_pages(_DUMMY_URL)

        assert len(result) == 1
        assert mock.call_count == 1

    def test_fetches_multiple_pages_when_total_exceeds_per_page(self, mocker):
        """totalCount가 perPage를 초과하면 여러 번 요청해야 합니다."""
        page1 = {"data": [{"학교명": f"학교{i}"} for i in range(3)], "totalCount": 5}
        page2 = {"data": [{"학교명": f"학교{i}"} for i in range(3, 5)], "totalCount": 5}

        mock = mocker.patch("requests.Session.get")
        mock.return_value.raise_for_status = lambda: None
        mock.return_value.json.side_effect = [page1, page2]

        client = DataGoKrClient(api_key=_DUMMY_KEY)
        client._PER_PAGE = 3  # 테스트를 위해 작은 값으로 조정
        result = client.get_all_pages(_DUMMY_URL)

        assert len(result) == 5
        assert mock.call_count == 2

    def test_returns_empty_list_when_no_data(self, mocker):
        """API 응답에 데이터가 없으면 빈 리스트를 반환해야 합니다."""
        response = {"data": [], "totalCount": 0}
        _make_mock_get(mocker, response)

        client = DataGoKrClient(api_key=_DUMMY_KEY)
        result = client.get_all_pages(_DUMMY_URL)

        assert result == []

    def test_stops_when_empty_page_returned(self, mocker):
        """빈 페이지가 반환되면 수집을 즉시 종료해야 합니다."""
        page1 = {"data": [{"학교명": "학교A"}], "totalCount": 999}  # totalCount가 크더라도
        page2 = {"data": [], "totalCount": 999}                     # 빈 페이지이면 종료

        mock = mocker.patch("requests.Session.get")
        mock.return_value.raise_for_status = lambda: None
        mock.return_value.json.side_effect = [page1, page2]

        client = DataGoKrClient(api_key=_DUMMY_KEY)
        client._PER_PAGE = 1
        result = client.get_all_pages(_DUMMY_URL)

        assert len(result) == 1  # page1의 데이터만 포함
        assert mock.call_count == 2

    def test_passes_page_and_per_page_params(self, mocker):
        """각 요청에 page와 perPage 파라미터가 포함되어야 합니다."""
        response = {"data": [{"학교명": "학교A"}], "totalCount": 1}
        mock = _make_mock_get(mocker, response)

        client = DataGoKrClient(api_key=_DUMMY_KEY)
        client.get_all_pages(_DUMMY_URL)

        first_call_params = mock.call_args.kwargs["params"]
        assert "page" in first_call_params
        assert "perPage" in first_call_params
