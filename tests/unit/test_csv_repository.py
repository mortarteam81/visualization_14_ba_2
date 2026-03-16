"""
CsvUniversityRepository 단위 테스트

tmp_path fixture로 임시 CSV 파일을 생성하여 실제 data/ 디렉토리 없이 테스트합니다.
"""

import pandas as pd
import pytest

from utils.config import GYOWON_COL_JEONGWON, GYOWON_COL_JAEHAK
from utils.repository.csv_repository import CsvUniversityRepository


# ── CSV 파일 생성 헬퍼 ────────────────────────────────────────────────────────

def _write_gyowon_csv(tmp_path, df: pd.DataFrame) -> None:
    """테스트용 전임교원 확보율 CSV를 tmp_path에 생성합니다."""
    csv_path = tmp_path / "전임교원_확보율.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")


def _minimal_gyowon_df() -> pd.DataFrame:
    """최소 유효 데이터 (필수 컬럼 모두 포함)"""
    return pd.DataFrame({
        "기준년도":             [2024],
        "학교명":              ["성신여자대학교"],
        "본분교명":             ["본교"],
        "설립유형":             ["사립"],
        GYOWON_COL_JEONGWON:   [79.0],
        GYOWON_COL_JAEHAK:     [84.0],
    })


# ── 정상 동작 테스트 ─────────────────────────────────────────────────────────

class TestCsvRepositoryGetGyowonData:
    """CsvUniversityRepository.get_gyowon_data() 검증"""

    def test_returns_dataframe(self, tmp_path):
        """CSV 로드 결과가 DataFrame이어야 합니다."""
        _write_gyowon_csv(tmp_path, _minimal_gyowon_df())
        repo = CsvUniversityRepository(data_dir=tmp_path)
        result = repo.get_gyowon_data()
        assert isinstance(result, pd.DataFrame)

    def test_returns_all_required_columns(self, tmp_path):
        """필수 컬럼이 모두 포함되어야 합니다."""
        _write_gyowon_csv(tmp_path, _minimal_gyowon_df())
        repo = CsvUniversityRepository(data_dir=tmp_path)
        result = repo.get_gyowon_data()

        required = {"기준년도", "학교명", "본분교명", "설립유형",
                    GYOWON_COL_JEONGWON, GYOWON_COL_JAEHAK}
        assert required.issubset(set(result.columns))

    def test_row_count_matches_csv(self, tmp_path):
        """CSV의 행 수와 반환 DataFrame의 행 수가 일치해야 합니다."""
        df = pd.DataFrame({
            "기준년도":             [2022, 2023, 2024],
            "학교명":              ["A대", "A대", "A대"],
            "본분교명":             ["본교", "본교", "본교"],
            "설립유형":             ["사립", "사립", "사립"],
            GYOWON_COL_JEONGWON:   [70.0, 75.0, 79.0],
            GYOWON_COL_JAEHAK:     [75.0, 80.0, 84.0],
        })
        _write_gyowon_csv(tmp_path, df)
        repo = CsvUniversityRepository(data_dir=tmp_path)
        result = repo.get_gyowon_data()
        assert len(result) == 3

    def test_does_not_apply_business_logic(self, tmp_path, sample_gyowon_with_public):
        """저장소는 원시 데이터를 반환해야 합니다 (사립 필터링 미적용)."""
        # 국립·공립이 포함된 데이터를 저장
        _write_gyowon_csv(tmp_path, sample_gyowon_with_public)
        repo = CsvUniversityRepository(data_dir=tmp_path)
        result = repo.get_gyowon_data()
        # 필터링 전이므로 모든 행이 반환되어야 함
        assert len(result) == len(sample_gyowon_with_public)


# ── 오류 처리 테스트 ─────────────────────────────────────────────────────────

class TestCsvRepositoryErrors:
    """CsvUniversityRepository 오류 처리 검증"""

    def test_raises_file_not_found_when_csv_missing(self, tmp_path):
        """CSV 파일이 없으면 FileNotFoundError가 발생해야 합니다."""
        repo = CsvUniversityRepository(data_dir=tmp_path)
        with pytest.raises(FileNotFoundError, match="전임교원_확보율.csv"):
            repo.get_gyowon_data()

    def test_raises_value_error_when_column_missing(self, tmp_path):
        """필수 컬럼이 누락된 CSV이면 ValueError가 발생해야 합니다."""
        # 필수 컬럼 중 하나(본분교명) 누락
        df = pd.DataFrame({
            "기준년도":           [2024],
            "학교명":            ["성신여자대학교"],
            # "본분교명" 누락
            "설립유형":           ["사립"],
            GYOWON_COL_JEONGWON: [79.0],
            GYOWON_COL_JAEHAK:   [84.0],
        })
        _write_gyowon_csv(tmp_path, df)
        repo = CsvUniversityRepository(data_dir=tmp_path)
        with pytest.raises(ValueError, match="본분교명"):
            repo.get_gyowon_data()
