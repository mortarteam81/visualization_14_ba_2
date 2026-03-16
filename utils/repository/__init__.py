"""
데이터 저장소 팩토리 모듈

DATA_SOURCE 환경변수에 따라 CSV 또는 API 저장소 인스턴스를 반환합니다.
pages/ 코드는 get_repository()만 호출하면 되므로, 데이터 소스 전환이 투명하게 이루어집니다.

사용 예:
    from utils.repository import get_repository

    repo = get_repository()           # 환경변수 DATA_SOURCE 자동 참조
    raw_df = repo.get_gyowon_data()   # CSV든 API든 동일한 인터페이스
"""

import os

from utils.repository.base import AbstractUniversityRepository


def get_repository() -> AbstractUniversityRepository:
    """
    설정(DATA_SOURCE 환경변수)에 따라 적절한 저장소 구현체를 반환합니다.

    환경변수
    --------
    DATA_SOURCE : str
        "csv" (기본값) → CsvUniversityRepository
        "api"          → ApiUniversityRepository (DATAGOKR_API_KEY 필수)

    Returns
    -------
    AbstractUniversityRepository
        CsvUniversityRepository 또는 ApiUniversityRepository 인스턴스

    Raises
    ------
    ValueError
        DATA_SOURCE 값이 허용 범위를 벗어나거나,
        DATA_SOURCE=api 인데 DATAGOKR_API_KEY가 비어 있는 경우
    """
    # .env 파일을 로드 (python-dotenv가 설치된 경우 환경변수 우선 적용)
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        # python-dotenv가 없으면 시스템 환경변수만 사용
        pass

    source = os.getenv("DATA_SOURCE", "csv").lower()

    if source == "csv":
        # CSV 저장소는 외부 의존성이 없으므로 바로 반환
        from utils.repository.csv_repository import CsvUniversityRepository
        return CsvUniversityRepository()

    elif source == "api":
        # API 저장소는 인증키가 반드시 필요함
        api_key = os.getenv("DATAGOKR_API_KEY", "")
        if not api_key:
            raise ValueError(
                "DATA_SOURCE=api 설정 시 DATAGOKR_API_KEY 환경변수가 필요합니다.\n"
                ".env 파일에 DATAGOKR_API_KEY=발급받은_인증키 를 추가하세요.\n"
                "참고: .env.example 파일을 복사하여 .env를 생성하세요."
            )
        from utils.api.client import DataGoKrClient
        from utils.repository.api_repository import ApiUniversityRepository

        client = DataGoKrClient(api_key=api_key)
        return ApiUniversityRepository(client=client)

    else:
        raise ValueError(
            f"알 수 없는 DATA_SOURCE 값: '{source}'\n"
            "허용값: 'csv' | 'api'\n"
            ".env 파일의 DATA_SOURCE 설정을 확인하세요."
        )
