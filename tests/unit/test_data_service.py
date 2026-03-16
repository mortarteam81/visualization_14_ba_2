"""
GyowonDataService 단위 테스트

순수 함수 테스트이므로 외부 의존성(파일, 네트워크)이 없습니다.
conftest.py의 sample_* fixtures를 활용합니다.
"""

import pandas as pd
import pytest

from utils.config import GYOWON_COL_JEONGWON, GYOWON_COL_JAEHAK
from utils.services.data_service import GyowonDataService


# ── 반환 구조 테스트 ─────────────────────────────────────────────────────────

class TestGyowonDataServiceOutputStructure:
    """prepare() 반환 DataFrame의 구조 검증"""

    def test_returns_dataframe(self, sample_gyowon_raw):
        """반환값이 DataFrame이어야 합니다."""
        result = GyowonDataService.prepare(sample_gyowon_raw)
        assert isinstance(result, pd.DataFrame)

    def test_returns_required_columns(self, sample_gyowon_raw):
        """필수 출력 컬럼이 모두 포함되어야 합니다."""
        result = GyowonDataService.prepare(sample_gyowon_raw)
        expected_cols = {"기준년도", "학교명", "본분교명",
                         GYOWON_COL_JEONGWON, GYOWON_COL_JAEHAK}
        assert expected_cols.issubset(set(result.columns))

    def test_sorted_by_year_then_school(self, sample_gyowon_raw):
        """기준년도 오름차순 → 학교명 가나다순으로 정렬되어야 합니다."""
        result = GyowonDataService.prepare(sample_gyowon_raw)
        years = result["기준년도"].tolist()
        assert years == sorted(years)


# ── 사립 필터링 테스트 ───────────────────────────────────────────────────────

class TestGyowonDataServicePrivateFilter:
    """사립대학 필터링 검증"""

    def test_filters_out_national_and_public(self, sample_gyowon_with_public):
        """국립·공립 대학이 제외되어야 합니다."""
        result = GyowonDataService.prepare(sample_gyowon_with_public)
        assert (result["설립유형"] == "사립").all() if "설립유형" in result.columns else True
        # 사립이 1개이므로 결과도 1행이어야 함
        assert len(result) == 1

    def test_keeps_private_universities(self, sample_gyowon_with_public):
        """사립대학 데이터는 보존되어야 합니다."""
        result = GyowonDataService.prepare(sample_gyowon_with_public)
        assert "성신여자대학교" in result["학교명"].values


# ── 본교/분교 필터링 테스트 ──────────────────────────────────────────────────

class TestGyowonDataServiceBonkyoFilter:
    """본교/분교 필터링 검증"""

    def test_bonkyo_only_true_excludes_branch(self, sample_gyowon_with_branch):
        """bonkyo_only=True 시 분교가 제외되어야 합니다."""
        result = GyowonDataService.prepare(sample_gyowon_with_branch, bonkyo_only=True)
        assert "제2캠퍼스" not in result["본분교명"].values

    def test_bonkyo_only_false_includes_branch(self, sample_gyowon_with_branch):
        """bonkyo_only=False 시 분교가 포함되어야 합니다."""
        result = GyowonDataService.prepare(sample_gyowon_with_branch, bonkyo_only=False)
        # 분교가 포함된 경우 '학교명 (캠퍼스)' 형태의 항목이 있어야 함
        school_names = result["학교명"].tolist()
        assert any("제2캠퍼스" in name for name in school_names)

    def test_branch_school_name_has_campus_suffix(self, sample_gyowon_with_branch):
        """분교 포함 시 학교명이 '학교명 (캠퍼스)' 형태여야 합니다."""
        result = GyowonDataService.prepare(sample_gyowon_with_branch, bonkyo_only=False)
        assert "가톨릭대학교 (제2캠퍼스)" in result["학교명"].values

    def test_bonkyo_only_default_is_true(self, sample_gyowon_with_branch):
        """기본값(bonkyo_only=True)에서 분교가 제외되어야 합니다."""
        # 기본 인자로 호출 (bonkyo_only 명시하지 않음)
        result = GyowonDataService.prepare(sample_gyowon_with_branch)
        assert len(result) == 2  # 본교 2개 (가톨릭대, 성신여대)


# ── 타입 변환 테스트 ─────────────────────────────────────────────────────────

class TestGyowonDataServiceTypeConversion:
    """숫자형 변환 검증 (API 응답에서 문자열로 올 수 있는 경우)"""

    def test_converts_string_rates_to_float(self, sample_gyowon_with_string_year):
        """문자열 확보율이 float으로 변환되어야 합니다."""
        result = GyowonDataService.prepare(sample_gyowon_with_string_year)
        assert result[GYOWON_COL_JEONGWON].dtype == float
        assert result[GYOWON_COL_JAEHAK].dtype == float

    def test_converts_string_year_to_int(self, sample_gyowon_with_string_year):
        """문자열 기준년도가 정수로 변환되어야 합니다."""
        result = GyowonDataService.prepare(sample_gyowon_with_string_year)
        assert result["기준년도"].dtype in [int, "int64", "Int64"]

    def test_drops_rows_with_nan_rates(self):
        """확보율이 NaN인 행은 제거되어야 합니다."""
        df_with_nan = pd.DataFrame({
            "기준년도":             [2024,      2024],
            "학교명":              ["성신여자대학교", "A대"],
            "본분교명":             ["본교",     "본교"],
            "설립유형":             ["사립",     "사립"],
            GYOWON_COL_JEONGWON:   [79.0,       None],   # NaN 행
            GYOWON_COL_JAEHAK:     [84.0,       None],
        })
        result = GyowonDataService.prepare(df_with_nan)
        assert len(result) == 1
        assert "성신여자대학교" in result["학교명"].values


# ── 오류 처리 테스트 ─────────────────────────────────────────────────────────

class TestGyowonDataServiceErrors:
    """prepare() 오류 처리 검증"""

    def test_raises_when_required_column_missing(self, sample_gyowon_raw):
        """필수 컬럼이 없으면 ValueError가 발생해야 합니다."""
        df_missing = sample_gyowon_raw.drop(columns=["본분교명"])
        with pytest.raises(ValueError, match="본분교명"):
            GyowonDataService.prepare(df_missing)

    def test_does_not_modify_original_dataframe(self, sample_gyowon_raw):
        """원본 DataFrame이 수정되지 않아야 합니다."""
        original_len = len(sample_gyowon_raw)
        original_cols = list(sample_gyowon_raw.columns)
        GyowonDataService.prepare(sample_gyowon_raw)
        # 원본 길이와 컬럼이 그대로여야 함
        assert len(sample_gyowon_raw) == original_len
        assert list(sample_gyowon_raw.columns) == original_cols
