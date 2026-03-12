"""
데이터 로딩 모듈
- 대학알리미 공시자료 CSV 로드 및 전처리
- st.cache_data 로 반복 로딩 방지
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from utils.config import (
    BUDAM_CSV, BUDAM_CSV_ENCODING,
    GYOWON_CSV, GYOWON_CSV_ENCODING,
    GYOWON_COL_JEONGWON, GYOWON_COL_JAEHAK,
    RESEARCH_CSV, RESEARCH_CSV_ENCODING,
    RESEARCH_COL_IN, RESEARCH_COL_OUT,
    PAPER_CSV, PAPER_CSV_ENCODING,
    PAPER_COL_JAEJI, PAPER_COL_SCI,
    JIROSUNG_CSV, JIROSUNG_CSV_ENCODING,
    GYEOLSAN_CSV, GYEOLSAN_CSV_ENCODING,
)

# 프로젝트 루트 기준 data/ 디렉토리
DATA_DIR = Path(__file__).parent.parent / "data"


# ── 법정부담금 부담율 ─────────────────────────────────────────────────────────

@st.cache_data(show_spinner="데이터 로딩 중…")
def load_budam_data() -> pd.DataFrame:
    """
    법정부담금 부담율 CSV 로드 및 전처리.

    Returns
    -------
    pd.DataFrame
        columns: ['기준년도', '학교명', '부담율']
        기준년도 오름차순 정렬

    Raises
    ------
    FileNotFoundError / ValueError
    """
    path = DATA_DIR / BUDAM_CSV
    _check_file(path)

    df = pd.read_csv(path, encoding=BUDAM_CSV_ENCODING)
    _check_columns(df, {"기준년도", "학교명", "부담율"})

    df = df[["기준년도", "학교명", "부담율"]].copy()
    df["부담율"] = pd.to_numeric(df["부담율"], errors="coerce")
    df = df.dropna(subset=["부담율"])
    df["기준년도"] = df["기준년도"].astype(int)

    return df.sort_values(["기준년도", "학교명"]).reset_index(drop=True)


# ── 전임교원 확보율 ───────────────────────────────────────────────────────────

@st.cache_data(show_spinner="데이터 로딩 중…")
def load_gyowon_data(bonkyo_only: bool = True) -> pd.DataFrame:
    """
    전임교원 확보율 CSV 로드 및 전처리.

    Parameters
    ----------
    bonkyo_only : bool
        True이면 본교(본분교명 == '본교') 데이터만 반환 (기본값)

    Returns
    -------
    pd.DataFrame
        columns: ['기준년도', '학교명', '본분교명',
                  '전임교원 확보율(학생정원 기준)',
                  '전임교원 확보율(재학생 기준)']
        기준년도 오름차순 정렬

    Raises
    ------
    FileNotFoundError / ValueError
    """
    path = DATA_DIR / GYOWON_CSV
    _check_file(path)

    df = pd.read_csv(path, encoding=GYOWON_CSV_ENCODING)

    required = {"기준년도", "학교명", "본분교명", GYOWON_COL_JEONGWON, GYOWON_COL_JAEHAK}
    _check_columns(df, required)

    keep = ["기준년도", "학교명", "본분교명", "설립유형",
            GYOWON_COL_JEONGWON, GYOWON_COL_JAEHAK]
    df = df[keep].copy()

    # 사립대학교만 필터링 (국립·공립 제외)
    df = df[df["설립유형"] == "사립"].copy()

    for col in [GYOWON_COL_JEONGWON, GYOWON_COL_JAEHAK]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if bonkyo_only:
        df = df[df["본분교명"] == "본교"].copy()

    df = df.dropna(subset=[GYOWON_COL_JEONGWON, GYOWON_COL_JAEHAK])
    df["기준년도"] = df["기준년도"].astype(int)

    # 분교 포함 시 식별자를 '학교명(캠퍼스)' 형태로 생성
    if not bonkyo_only:
        mask = df["본분교명"] != "본교"
        df.loc[mask, "학교명"] = (
            df.loc[mask, "학교명"] + " (" + df.loc[mask, "본분교명"] + ")"
        )

    return df.sort_values(["기준년도", "학교명"]).reset_index(drop=True)


# ── 연구비 수혜실적 ───────────────────────────────────────────────────────────

@st.cache_data(show_spinner="데이터 로딩 중…")
def load_research_data(bonkyo_only: bool = True) -> pd.DataFrame:
    """
    전임교원 1인당 연구비 CSV 로드 및 전처리.

    Parameters
    ----------
    bonkyo_only : bool
        True이면 본교 데이터만 반환 (기본값)

    Returns
    -------
    pd.DataFrame
        columns: ['기준년도', '학교명', '본분교명',
                  '전임교원 1인당 연구비(교내)',
                  '전임교원 1인당 연구비(교외)']
        단위: 천원 / 기준년도 오름차순 정렬

    Raises
    ------
    FileNotFoundError / ValueError
    """
    path = DATA_DIR / RESEARCH_CSV
    _check_file(path)

    df = pd.read_csv(path, encoding=RESEARCH_CSV_ENCODING)

    required = {"기준년도", "학교명", "본분교명", "설립유형",
                RESEARCH_COL_IN, RESEARCH_COL_OUT}
    _check_columns(df, required)

    keep = ["기준년도", "학교명", "본분교명", "설립유형",
            RESEARCH_COL_IN, RESEARCH_COL_OUT]
    df = df[keep].copy()

    # 사립대학교만 (국립·공립 제외)
    df = df[df["설립유형"] == "사립"].copy()

    for col in [RESEARCH_COL_IN, RESEARCH_COL_OUT]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    if bonkyo_only:
        df = df[df["본분교명"] == "본교"].copy()

    df["기준년도"] = df["기준년도"].astype(int)

    # 분교 포함 시 식별자를 '학교명 (캠퍼스)' 형태로 생성
    if not bonkyo_only:
        mask = df["본분교명"] != "본교"
        df.loc[mask, "학교명"] = (
            df.loc[mask, "학교명"] + " (" + df.loc[mask, "본분교명"] + ")"
        )

    return df.sort_values(["기준년도", "학교명"]).reset_index(drop=True)


# ── 전임교원 1인당 논문실적 ──────────────────────────────────────────────────

@st.cache_data(show_spinner="데이터 로딩 중…")
def load_paper_data(bonkyo_only: bool = True) -> pd.DataFrame:
    """
    전임교원 1인당 논문실적 CSV 로드 및 전처리.

    Parameters
    ----------
    bonkyo_only : bool
        True이면 본교 데이터만 반환 (기본값)

    Returns
    -------
    pd.DataFrame
        columns: ['기준년도', '학교명', '본분교명', '설립유형',
                  PAPER_COL_JAEJI, PAPER_COL_SCI]
        단위: 편/인 / 기준년도 오름차순 정렬

    Raises
    ------
    FileNotFoundError / ValueError
    """
    path = DATA_DIR / PAPER_CSV
    _check_file(path)

    df = pd.read_csv(path, encoding=PAPER_CSV_ENCODING)

    required = {"기준년도", "학교명", "본분교명", "설립유형",
                PAPER_COL_JAEJI, PAPER_COL_SCI}
    _check_columns(df, required)

    keep = ["기준년도", "학교명", "본분교명", "설립유형",
            PAPER_COL_JAEJI, PAPER_COL_SCI]
    df = df[keep].copy()

    # 사립대학교만 (국립·공립 제외)
    df = df[df["설립유형"] == "사립"].copy()

    for col in [PAPER_COL_JAEJI, PAPER_COL_SCI]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    if bonkyo_only:
        df = df[df["본분교명"] == "본교"].copy()

    df["기준년도"] = df["기준년도"].astype(int)

    # 분교 포함 시 식별자를 '학교명 (캠퍼스)' 형태로 생성
    if not bonkyo_only:
        mask = df["본분교명"] != "본교"
        df.loc[mask, "학교명"] = (
            df.loc[mask, "학교명"] + " (" + df.loc[mask, "본분교명"] + ")"
        )

    return df.sort_values(["기준년도", "학교명"]).reset_index(drop=True)


# ── 졸업생 진로 성과 ──────────────────────────────────────────────────────────

@st.cache_data(show_spinner="데이터 로딩 중…")
def load_jirosung_data(bonkyo_only: bool = True) -> pd.DataFrame:
    """
    졸업생 진로 성과 CSV 로드 및 전처리.
    산식: (취업자 + 진학자) / (졸업자 - (입대자 + 취업불가능자 + 외국인유학생 + 건강보험직장가입제외대상)) × 100

    Parameters
    ----------
    bonkyo_only : bool
        True이면 본교 데이터만 반환 (기본값)

    Returns
    -------
    pd.DataFrame
        columns: ['기준년도', '학교명', '본분교명', '졸업생_진로_성과']
        기준년도 오름차순 정렬

    Raises
    ------
    FileNotFoundError / ValueError
    """
    path = DATA_DIR / JIROSUNG_CSV
    _check_file(path)

    df = pd.read_csv(path, encoding=JIROSUNG_CSV_ENCODING)

    raw_cols = {
        "기준년도", "학교명", "본분교명", "설립유형",
        "졸업자", "취업자", "진학자",
        "입대자", "취업불가능자", "외국인유학생", "건강보험직장가입제외대상",
    }
    _check_columns(df, raw_cols)

    df = df[list(raw_cols)].copy()
    df = df[df["설립유형"] == "사립"].copy()

    for col in ["졸업자", "취업자", "진학자",
                "입대자", "취업불가능자", "외국인유학생", "건강보험직장가입제외대상"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["기준년도"] = df["기준년도"].astype(int)

    분모 = (df["졸업자"]
            - df["입대자"]
            - df["취업불가능자"]
            - df["외국인유학생"]
            - df["건강보험직장가입제외대상"])
    df["졸업생_진로_성과"] = (df["취업자"] + df["진학자"]) / 분모 * 100
    df["졸업생_진로_성과"] = (df["졸업생_진로_성과"]
                              .replace([float("inf"), float("-inf")], float("nan")))
    df = df.dropna(subset=["졸업생_진로_성과"])
    df["졸업생_진로_성과"] = df["졸업생_진로_성과"].round(1)

    if bonkyo_only:
        df = df[df["본분교명"] == "본교"].copy()

    if not bonkyo_only:
        mask = df["본분교명"] != "본교"
        df.loc[mask, "학교명"] = (
            df.loc[mask, "학교명"] + " (" + df.loc[mask, "본분교명"] + ")"
        )

    return (
        df[["기준년도", "학교명", "본분교명", "졸업생_진로_성과"]]
        .sort_values(["기준년도", "학교명"])
        .reset_index(drop=True)
    )


# ── 세입 중 등록금 비율 / 기부금 비율 (결산 데이터) ──────────────────────────

@st.cache_data(show_spinner="데이터 로딩 중…")
def load_gyeolsan_data() -> pd.DataFrame:
    """
    결산(22,23,24) CSV 로드 및 전처리.
    서울 소재 사립 4년제 대학교 교비 회계 데이터만 필터링.

    산식
    ----
    - 등록금비율 = 등록금수입[1002] / 운영수입[1086] × 100
    - 기부금비율 = 기부금수입[1035] / 운영수입[1086] × 100

    Returns
    -------
    pd.DataFrame
        columns: ['기준년도', '학교명', '운영수입', '등록금수입', '기부금수입',
                  '등록금비율', '기부금비율']
        기준년도 오름차순 정렬

    Raises
    ------
    FileNotFoundError / ValueError
    """
    path = DATA_DIR / GYEOLSAN_CSV
    _check_file(path)

    df = pd.read_csv(path, encoding=GYEOLSAN_CSV_ENCODING)

    # 컬럼명 공백 제거
    df.columns = df.columns.str.strip()

    required = {"학교명", "회계", "지역", "학급", "회계연도",
                "2.운영수입[1086]", "4.등록금수입[1002]", "4.기부금수입[1035]"}
    _check_columns(df, required)

    # 서울 소재 / 사립 4년제 대학교 / 교비 회계
    df["회계"] = df["회계"].str.strip()
    df["지역"] = df["지역"].str.strip()
    df["학급"] = df["학급"].str.strip()
    df["학교명"] = df["학교명"].str.strip()
    df["회계연도"] = df["회계연도"].str.strip()

    df = df[
        (df["회계"] == "교비") &
        (df["지역"] == "서울") &
        (df["학급"] == "대학")
    ].copy()

    # 회계연도 → 정수 기준년도 (예: '2022년' → 2022)
    df["기준년도"] = df["회계연도"].str.replace("년", "").astype(int)

    # 숫자 변환 (콤마 제거)
    for raw_col, new_col in [
        ("2.운영수입[1086]", "운영수입"),
        ("4.등록금수입[1002]", "등록금수입"),
        ("4.기부금수입[1035]", "기부금수입"),
    ]:
        df[new_col] = (
            pd.to_numeric(
                df[raw_col].astype(str).str.replace(",", ""),
                errors="coerce",
            )
        )

    df = df.dropna(subset=["운영수입", "등록금수입", "기부금수입"])
    df = df[df["운영수입"] > 0].copy()

    df["등록금비율"] = (df["등록금수입"] / df["운영수입"] * 100).round(2)
    df["기부금비율"] = (df["기부금수입"] / df["운영수입"] * 100).round(2)

    return (
        df[["기준년도", "학교명", "운영수입", "등록금수입", "기부금수입",
            "등록금비율", "기부금비율"]]
        .sort_values(["기준년도", "학교명"])
        .reset_index(drop=True)
    )


# ── 공통 헬퍼 ────────────────────────────────────────────────────────────────

def _check_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(
            f"CSV 파일을 찾을 수 없습니다: {path}\n"
            f"data/ 디렉토리에 '{path.name}' 파일을 확인하세요."
        )


def _check_columns(df: pd.DataFrame, required: set) -> None:
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV에 필수 컬럼이 없습니다: {missing}")
