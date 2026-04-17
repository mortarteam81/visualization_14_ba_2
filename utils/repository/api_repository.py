"""
data.go.kr API 기반 대학알리미 데이터 저장소 구현체

DataGoKrClient를 통해 API를 호출하고,
응답 컬럼명을 내부 표준 컬럼명(CSV 기준)으로 정규화합니다.

테스트 지원:
- __init__에서 client를 주입받으므로 테스트 시 Mock 클라이언트를 사용할 수 있습니다.
"""

import pandas as pd

from utils.api.client import DataGoKrClient
from utils.api.endpoints import (
    GYOWON_ENDPOINT,
    GYOWON_COLUMN_MAP,
)
from utils.data_pipeline import COLUMN_ALIASES
from utils.repository.base import AbstractUniversityRepository


class ApiUniversityRepository(AbstractUniversityRepository):
    """
    data.go.kr API를 데이터 원본으로 사용하는 저장소 구현체.

    Parameters
    ----------
    client : DataGoKrClient
        HTTP 클라이언트 인스턴스 (의존성 주입).
        테스트 시에는 Mock 객체를 주입하여 실제 API 호출 없이 테스트합니다.
    """

    def __init__(self, client: DataGoKrClient) -> None:
        # 의존성 주입: 테스트에서 Mock 클라이언트를 주입하여 외부 API 의존성을 격리
        self._client = client

    def get_gyowon_data(self) -> pd.DataFrame:
        """
        data.go.kr API에서 전임교원 확보율 데이터를 수집하고 정규화합니다.

        처리 과정:
        1. GYOWON_ENDPOINT로 전체 페이지 수집 (페이지네이션 자동 처리)
        2. API 응답 컬럼명 → 내부 표준 컬럼명 변환 (GYOWON_COLUMN_MAP 참조)

        Returns
        -------
        pd.DataFrame
            정규화된 원시 DataFrame (비즈니스 로직 미적용 상태)

        Raises
        ------
        ValueError
            엔드포인트가 설정되지 않았거나 API 응답 데이터가 비어 있는 경우
        requests.HTTPError / requests.Timeout / requests.ConnectionError
            API 호출 실패 시 (DataGoKrClient에서 전파)
        """
        # 엔드포인트 URL이 설정되지 않으면 즉시 안내 메시지와 함께 종료
        if not GYOWON_ENDPOINT:
            raise ValueError(
                "전임교원 확보율 API 엔드포인트가 설정되지 않았습니다.\n"
                "utils/api/endpoints.py의 GYOWON_ENDPOINT에 실제 URL을 입력하세요.\n"
                "API 조회 경로: data.go.kr > 데이터찾기 > '대학알리미 전임교원' 검색"
            )

        # 페이지네이션을 처리하며 전체 데이터 수집
        items = self._client.get_all_pages(GYOWON_ENDPOINT)

        if not items:
            raise ValueError(
                "API 응답에 데이터가 없습니다. "
                "엔드포인트 URL과 인증키를 확인하세요."
            )

        df = pd.DataFrame(items)

        # API 응답 컬럼명을 내부 표준 컬럼명으로 변환
        # GYOWON_COLUMN_MAP에 없는 컬럼은 그대로 유지 (추후 DataService가 필요 컬럼만 사용)
        existing_map = {k: v for k, v in GYOWON_COLUMN_MAP.items() if k in df.columns}
        df = df.rename(columns=existing_map)
        aliases = {source: target for source, target in COLUMN_ALIASES.items() if source in df.columns}
        if aliases:
            df = df.rename(columns=aliases)

        return df
