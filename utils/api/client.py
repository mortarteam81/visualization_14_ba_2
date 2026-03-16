"""
data.go.kr Open API HTTP 클라이언트

공통 기능:
- 인증키(serviceKey) 자동 첨부
- JSON 응답 파싱
- 페이지네이션(perPage / page) 자동 처리
- HTTP 오류 / 타임아웃 예외 전파

사용 예:
    client = DataGoKrClient(api_key="발급받은_인증키")
    items = client.get_all_pages("https://api.odcloud.kr/api/.../v1/uddi:...")
"""

from typing import Dict, List, Optional

import requests


class DataGoKrClient:
    """
    data.go.kr Open API 호출을 위한 HTTP 클라이언트.

    Attributes
    ----------
    api_key : str
        data.go.kr 인증키 (Encoding 또는 Decoding 키 중 하나)
    timeout : int
        단일 요청 타임아웃 (초, 기본값 10)

    Notes
    -----
    - requests.Session을 재사용하여 커넥션 풀을 유지합니다.
    - HTTP 오류(4xx/5xx)는 raise_for_status()로 자동 감지됩니다.
    - 페이지당 최대 요청 건수(perPage)는 _PER_PAGE 클래스 변수로 조정하세요.
    """

    # data.go.kr 응답 JSON에서 데이터 배열 키와 전체 건수 키
    _ITEMS_KEY = "data"
    _TOTAL_COUNT_KEY = "totalCount"

    # 페이지당 최대 요청 건수 (data.go.kr 최대 허용값: 1000)
    _PER_PAGE = 1000

    def __init__(self, api_key: str, timeout: int = 10) -> None:
        # API 키가 비어 있으면 이후 모든 요청이 실패하므로 초기화 시점에 검증
        if not api_key:
            raise ValueError(
                "API 키가 비어 있습니다. DATAGOKR_API_KEY 환경변수를 설정하세요.\n"
                "참고: .env.example 파일을 복사하여 .env를 생성하고 인증키를 입력하세요."
            )
        self.api_key = api_key
        self.timeout = timeout
        # Session을 재사용하면 TCP 연결을 풀링하여 반복 호출 시 성능이 향상됨
        self._session = requests.Session()

    def get(self, url: str, params: Optional[Dict] = None) -> dict:
        """
        단일 GET 요청을 수행하고 JSON 응답을 반환합니다.

        Parameters
        ----------
        url : str
            요청 URL (엔드포인트 전체 URL)
        params : dict, optional
            추가 쿼리 파라미터 (serviceKey, type 은 자동 추가됨)

        Returns
        -------
        dict
            파싱된 JSON 응답

        Raises
        ------
        requests.HTTPError
            HTTP 오류 응답 (4xx, 5xx)
        requests.Timeout
            요청이 timeout 초를 초과한 경우
        requests.ConnectionError
            네트워크 연결 오류
        """
        # serviceKey와 type=json은 모든 요청에 공통으로 첨부
        merged_params: dict = {"serviceKey": self.api_key, "type": "json"}
        if params:
            merged_params.update(params)

        response = self._session.get(url, params=merged_params, timeout=self.timeout)
        # HTTP 오류 응답(4xx/5xx)이면 HTTPError 예외를 발생시킴
        response.raise_for_status()
        return response.json()

    def get_all_pages(self, url: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        페이지네이션을 자동 처리하여 전체 데이터를 수집합니다.

        data.go.kr의 perPage / page 방식 페이지네이션을 따릅니다.
        totalCount에 도달하거나 빈 page가 반환되면 수집을 종료합니다.

        Parameters
        ----------
        url : str
            요청 URL
        params : dict, optional
            추가 쿼리 파라미터 (perPage, page 는 자동 관리됨)

        Returns
        -------
        List[Dict]
            전체 페이지를 합친 데이터 항목 목록
        """
        all_items: List[Dict] = []
        page = 1

        while True:
            # 페이지 파라미터를 병합하여 현재 페이지 요청
            page_params: dict = {"perPage": self._PER_PAGE, "page": page}
            if params:
                page_params.update(params)

            response = self.get(url, params=page_params)
            items: List[Dict] = response.get(self._ITEMS_KEY, [])
            all_items.extend(items)

            total: int = response.get(self._TOTAL_COUNT_KEY, 0)

            # 수집한 건수가 전체 건수에 도달했거나, 빈 페이지이면 종료
            if len(all_items) >= total or not items:
                break

            page += 1

        return all_items
