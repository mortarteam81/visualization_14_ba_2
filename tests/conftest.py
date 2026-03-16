"""
pytest 공용 fixtures

모든 테스트 모듈에서 재사용하는 샘플 데이터와 Mock 객체를 정의합니다.

fixture 명명 규칙:
- sample_*   : 테스트용 샘플 DataFrame
- mock_*     : Mock 객체 또는 API 응답 데이터
"""

import pandas as pd
import pytest

from utils.config import GYOWON_COL_JEONGWON, GYOWON_COL_JAEHAK


# ── 전임교원 확보율 샘플 데이터 ───────────────────────────────────────────────

@pytest.fixture
def sample_gyowon_raw() -> pd.DataFrame:
    """
    전임교원 확보율 원시 데이터 fixture.

    Repository.get_gyowon_data()가 반환하는 형태와 동일합니다.
    (비즈니스 로직 적용 전 상태)
    """
    return pd.DataFrame({
        "기준년도":             [2022,      2022,       2023,      2023,       2024],
        "학교명":              ["성신여자대학교", "연세대학교", "성신여자대학교", "연세대학교", "성신여자대학교"],
        "본분교명":             ["본교",     "본교",     "본교",     "본교",     "본교"],
        "설립유형":             ["사립",     "사립",     "사립",     "사립",     "사립"],
        GYOWON_COL_JEONGWON:   [75.0,      85.0,       77.0,      87.0,       79.0],
        GYOWON_COL_JAEHAK:     [80.0,      90.0,       82.0,      92.0,       84.0],
    })


@pytest.fixture
def sample_gyowon_with_branch() -> pd.DataFrame:
    """
    분교가 포함된 전임교원 확보율 원시 데이터 fixture.

    bonkyo_only=False 시나리오 테스트에 사용합니다.
    """
    return pd.DataFrame({
        "기준년도":             [2024,        2024,          2024],
        "학교명":              ["가톨릭대학교",  "가톨릭대학교",   "성신여자대학교"],
        "본분교명":             ["본교",       "제2캠퍼스",      "본교"],
        "설립유형":             ["사립",       "사립",         "사립"],
        GYOWON_COL_JEONGWON:   [70.0,         83.0,           79.0],
        GYOWON_COL_JAEHAK:     [75.0,         88.0,           84.0],
    })


@pytest.fixture
def sample_gyowon_with_public() -> pd.DataFrame:
    """
    국립·공립 대학이 섞인 원시 데이터 fixture.

    사립 필터링 테스트에 사용합니다.
    """
    return pd.DataFrame({
        "기준년도":             [2024,      2024,       2024],
        "학교명":              ["서울대학교",  "성신여자대학교", "서울시립대학교"],
        "본분교명":             ["본교",     "본교",     "본교"],
        "설립유형":             ["국립",     "사립",     "공립"],
        GYOWON_COL_JEONGWON:   [90.0,       79.0,       85.0],
        GYOWON_COL_JAEHAK:     [95.0,       84.0,       88.0],
    })


@pytest.fixture
def sample_gyowon_with_string_year() -> pd.DataFrame:
    """
    기준년도가 문자열로 들어온 경우의 fixture (API 응답 시뮬레이션).
    """
    return pd.DataFrame({
        "기준년도":             ["2024",    "2024"],
        "학교명":              ["성신여자대학교", "연세대학교"],
        "본분교명":             ["본교",     "본교"],
        "설립유형":             ["사립",     "사립"],
        GYOWON_COL_JEONGWON:   ["79.0",    "87.0"],   # 문자열 숫자
        GYOWON_COL_JAEHAK:     ["84.0",    "92.0"],
    })


# ── data.go.kr API 응답 Mock 데이터 ──────────────────────────────────────────

@pytest.fixture
def mock_api_items() -> list[dict]:
    """
    data.go.kr API 응답의 'data' 배열 fixture.

    실제 API 응답에서 GYOWON_COLUMN_MAP이 적용되기 전의 원본 형태입니다.
    API 컬럼명은 utils/api/endpoints.py의 GYOWON_COLUMN_MAP 키와 일치해야 합니다.
    """
    return [
        {
            "기준년도": "2024",
            "학교명": "성신여자대학교",
            "본분교구분": "본교",
            "설립유형구분": "사립",
            "전임교원확보율(학생정원기준)(%)": "79.0",
            "전임교원확보율(재학생기준)(%)":   "84.0",
        },
        {
            "기준년도": "2024",
            "학교명": "연세대학교",
            "본분교구분": "본교",
            "설립유형구분": "사립",
            "전임교원확보율(학생정원기준)(%)": "87.0",
            "전임교원확보율(재학생기준)(%)":   "92.0",
        },
    ]
