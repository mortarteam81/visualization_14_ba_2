"""
대학알리미 데이터 저장소 추상 인터페이스

설계 원칙:
- 의존성 역전 원칙(DIP): pages/는 구체 클래스(CSV/API)가 아닌 이 추상에 의존
- 단일 책임 원칙(SRP): 저장소는 '데이터 원본 접근'만 담당, 비즈니스 로직은 DataService
- 반환 DataFrame의 컬럼명은 CSV 원본 기준 표준 컬럼명을 사용 (API 구현체도 동일)

확장 방법:
- 새 지표를 추가할 때는 이 클래스에 @abstractmethod를 추가하고
  CsvUniversityRepository, ApiUniversityRepository 양쪽에 구현하세요.
"""

from abc import ABC, abstractmethod

import pandas as pd


class AbstractUniversityRepository(ABC):
    """
    대학알리미 지표 데이터 저장소 추상 기반 클래스.

    모든 구현체(CSV, API)는 이 인터페이스를 준수해야 합니다.
    반환 DataFrame은 비즈니스 로직이 적용되기 전 원시(raw) 데이터입니다.
    필터링·계산 등은 DataService에서 처리합니다.
    """

    @abstractmethod
    def get_gyowon_data(self) -> pd.DataFrame:
        """
        전임교원 확보율 원시 데이터를 반환합니다.

        Returns
        -------
        pd.DataFrame
            필수 컬럼:
            - 기준년도       : 연도 (정수 또는 문자열, DataService에서 정수 변환)
            - 학교명         : 대학교 이름
            - 본분교명       : '본교' | '분교명' (예: '제2캠퍼스')
            - 설립유형       : '사립' | '국립' | '공립'
            - 전임교원 확보율(학생정원 기준) : float (%)
            - 전임교원 확보율(재학생 기준)   : float (%)
        """
        ...

    # ── 이후 지표 추가 시 아래에 @abstractmethod를 추가하세요 ──────────────────
    # @abstractmethod
    # def get_budam_data(self) -> pd.DataFrame:
    #     """법정부담금 부담율 원시 데이터"""
    #     ...
    #
    # @abstractmethod
    # def get_research_data(self) -> pd.DataFrame:
    #     """전임교원 1인당 연구비 원시 데이터"""
    #     ...
