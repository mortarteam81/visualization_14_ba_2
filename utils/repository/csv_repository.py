"""
CSV 기반 대학알리미 데이터 저장소 구현체

data/ 디렉토리의 CSV 파일을 데이터 원본으로 사용합니다.
비즈니스 로직(사립 필터링, 본교/분교 처리 등)은 DataService에서 처리합니다.

테스트 지원:
- __init__에서 data_dir를 주입받아 테스트 시 임시 디렉토리를 사용할 수 있습니다.
"""

from pathlib import Path
from typing import Optional

import pandas as pd

from utils.config import (
    GYOWON_CSV,
    GYOWON_CSV_ENCODING,
    GYOWON_COL_JEONGWON,
    GYOWON_COL_JAEHAK,
)
from utils.repository.base import AbstractUniversityRepository
from utils.data_pipeline import COLUMN_ALIASES

# 프로젝트 루트 기준 data/ 디렉토리 (기본값)
_DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent / "data"


class CsvUniversityRepository(AbstractUniversityRepository):
    """
    CSV 파일을 데이터 원본으로 사용하는 저장소 구현체.

    Parameters
    ----------
    data_dir : Path, optional
        CSV 파일들이 위치한 디렉토리.
        기본값은 프로젝트 루트의 data/ 디렉토리.
        테스트에서는 tmp_path fixture를 통해 임시 디렉토리를 주입합니다.
    """

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        # 의존성 주입: 테스트 시 tmp_path 등을 주입하여 실제 파일 없이도 테스트 가능
        self._data_dir = data_dir if data_dir is not None else _DEFAULT_DATA_DIR

    def get_gyowon_data(self) -> pd.DataFrame:
        """
        전임교원 확보율 CSV를 로드하여 원시 DataFrame을 반환합니다.

        Returns
        -------
        pd.DataFrame
            CSV 원본 데이터 (비즈니스 로직 미적용 상태)

        Raises
        ------
        FileNotFoundError
            CSV 파일이 존재하지 않는 경우
        ValueError
            CSV에 필수 컬럼이 없는 경우
        """
        path = self._data_dir / GYOWON_CSV
        self._check_file(path)

        df = pd.read_csv(path, encoding=GYOWON_CSV_ENCODING)
        aliases = {source: target for source, target in COLUMN_ALIASES.items() if source in df.columns}
        if aliases:
            df = df.rename(columns=aliases)

        # 필수 컬럼 존재 여부 검증
        required = {
            "기준년도", "학교명", "본분교명", "설립유형",
            GYOWON_COL_JEONGWON, GYOWON_COL_JAEHAK,
        }
        self._check_columns(df, required)

        return df

    # ── 내부 헬퍼 ─────────────────────────────────────────────────────────────

    @staticmethod
    def _check_file(path: Path) -> None:
        """파일 존재 여부를 확인하고 없으면 FileNotFoundError를 발생시킵니다."""
        if not path.exists():
            raise FileNotFoundError(
                f"CSV 파일을 찾을 수 없습니다: {path}\n"
                f"data/ 디렉토리에 '{path.name}' 파일이 있는지 확인하세요."
            )

    @staticmethod
    def _check_columns(df: pd.DataFrame, required: set) -> None:
        """필수 컬럼 누락 시 ValueError를 발생시킵니다."""
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"CSV에 필수 컬럼이 없습니다: {missing}")
