"""
대학알리미 지표별 데이터 처리 서비스

Repository에서 받은 원시 DataFrame을 시각화에 적합한 형태로 변환합니다.

설계 원칙:
- 단일 책임 원칙(SRP): 순수 데이터 변환 로직만 담당 (UI, 파일I/O, 네트워크 의존 없음)
- 정적 메서드로 구성하여 상태를 갖지 않음 → 테스트가 쉬움
- CSV 저장소와 API 저장소 모두 동일한 서비스를 거쳐 동일한 결과를 반환
"""

import pandas as pd

from utils.config import GYOWON_COL_JEONGWON, GYOWON_COL_JAEHAK


class GyowonDataService:
    """
    전임교원 확보율 지표 데이터 처리 서비스.

    Repository에서 받은 원시 DataFrame을 전처리하여
    pages/에서 바로 사용할 수 있는 형태로 반환합니다.
    """

    # 최종 반환 DataFrame에 포함될 컬럼 순서
    _OUTPUT_COLUMNS = [
        "기준년도",
        "학교명",
        "본분교명",
        GYOWON_COL_JEONGWON,
        GYOWON_COL_JAEHAK,
    ]

    @staticmethod
    def prepare(df: pd.DataFrame, bonkyo_only: bool = True) -> pd.DataFrame:
        """
        전임교원 확보율 원시 DataFrame을 전처리합니다.

        처리 순서:
        1. 필수 컬럼 존재 여부 검증
        2. 사립대학교만 필터링 (국립·공립 제외)
        3. 확보율 컬럼 숫자형 변환 (API 응답에서 문자열로 올 수 있음)
        4. 결측값(NaN) 제거
        5. 기준년도 정수형 변환
        6. 본교 / 분교 필터링
        7. 분교 포함 시 학교명에 캠퍼스 표시 추가

        Parameters
        ----------
        df : pd.DataFrame
            Repository.get_gyowon_data()가 반환한 원시 DataFrame
        bonkyo_only : bool
            True  → 본교만 반환 (기본값, 4주기 인증 평가 기준)
            False → 분교 포함 반환

        Returns
        -------
        pd.DataFrame
            columns: ['기준년도', '학교명', '본분교명',
                      '전임교원 확보율(학생정원 기준)',
                      '전임교원 확보율(재학생 기준)']
            기준년도 오름차순, 학교명 가나다순 정렬

        Raises
        ------
        ValueError
            필수 컬럼이 없는 경우
        """
        # ── 1. 필수 컬럼 검증 ───────────────────────────────────────────────
        required = {
            "기준년도", "학교명", "본분교명", "설립유형",
            GYOWON_COL_JEONGWON, GYOWON_COL_JAEHAK,
        }
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"DataFrame에 필수 컬럼이 없습니다: {missing}")

        # 필요한 컬럼만 추출하여 복사 (원본 DataFrame 보호)
        df = df[list(required)].copy()

        # ── 2. 사립대학교만 필터링 ─────────────────────────────────────────
        # 국립·공립 대학을 제외하고 사립 대학만 분석 대상으로 사용
        df = df[df["설립유형"] == "사립"].copy()

        # ── 3. 숫자형 변환 ─────────────────────────────────────────────────
        # API 응답에서 확보율이 문자열(예: "85.5")로 올 수 있으므로 강제 변환
        # errors="coerce" → 변환 실패 시 NaN 처리 (이후 step에서 제거)
        for col in [GYOWON_COL_JEONGWON, GYOWON_COL_JAEHAK]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # ── 4. 결측값 제거 ─────────────────────────────────────────────────
        # 확보율이 NaN인 행은 분석에서 제외
        df = df.dropna(subset=[GYOWON_COL_JEONGWON, GYOWON_COL_JAEHAK])

        # ── 5. 기준년도 정수 변환 ──────────────────────────────────────────
        # API 응답에서 "2024" 같은 문자열로 올 수 있으므로 변환
        df["기준년도"] = pd.to_numeric(df["기준년도"], errors="coerce")
        df = df.dropna(subset=["기준년도"])
        df["기준년도"] = df["기준년도"].astype(int)

        # ── 6. 본교/분교 필터링 ────────────────────────────────────────────
        if bonkyo_only:
            # 4주기 인증 평가에서는 본교 기준이 원칙
            df = df[df["본분교명"] == "본교"].copy()
        else:
            # 분교 포함 시 '학교명 (캠퍼스명)' 형태로 식별자 생성
            # 예: '가톨릭대학교' + ' (제2캠퍼스)' → '가톨릭대학교 (제2캠퍼스)'
            mask = df["본분교명"] != "본교"
            df.loc[mask, "학교명"] = (
                df.loc[mask, "학교명"] + " (" + df.loc[mask, "본분교명"] + ")"
            )

        # ── 7. 정렬 및 반환 ────────────────────────────────────────────────
        return (
            df[GyowonDataService._OUTPUT_COLUMNS]
            .sort_values(["기준년도", "학교명"])
            .reset_index(drop=True)
        )
