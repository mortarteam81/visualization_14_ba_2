"""Shared dataset loading and transformation helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from utils.config import (
    BUDAM_CSV,
    BUDAM_CSV_ENCODING,
    GYEOLSAN_CSV,
    GYEOLSAN_CSV_ENCODING,
    GYOWON_COL_JAEHAK,
    GYOWON_COL_JEONGWON,
    GYOWON_CSV,
    GYOWON_CSV_ENCODING,
    JIROSUNG_CSV,
    JIROSUNG_CSV_ENCODING,
    PAPER_COL_JAEJI,
    PAPER_COL_SCI,
    PAPER_CSV,
    PAPER_CSV_ENCODING,
    RESEARCH_COL_IN,
    RESEARCH_COL_OUT,
    RESEARCH_CSV,
    RESEARCH_CSV_ENCODING,
)


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
COLUMN_ALIASES = {
    "기준연도": "기준년도",
}


def _apply_column_aliases(df: pd.DataFrame) -> pd.DataFrame:
    aliases = {source: target for source, target in COLUMN_ALIASES.items() if source in df.columns}
    return df.rename(columns=aliases) if aliases else df


def _check_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(
            f"CSV 파일을 찾을 수 없습니다: {path}\n"
            f"data/ 디렉터리에 '{path.name}' 파일이 있는지 확인하세요."
        )


def _check_columns(df: pd.DataFrame, required: Iterable[str]) -> None:
    required_set = set(required)
    missing = required_set - set(df.columns)
    if missing:
        raise ValueError(f"CSV에 필수 컬럼이 없습니다: {missing}")


def _load_csv(filename: str, encoding: str) -> pd.DataFrame:
    path = DATA_DIR / filename
    _check_file(path)
    try:
        return pd.read_csv(path, encoding=encoding)
    except UnicodeDecodeError:
        if encoding.lower() == "utf-8-sig":
            raise
        return pd.read_csv(path, encoding="utf-8-sig")


def _normalize_school_frame(
    df: pd.DataFrame,
    *,
    numeric_columns: list[str],
    bonkyo_only: bool,
    keep_columns: list[str],
    private_only: bool = True,
    dropna_numeric: bool = True,
    fillna_numeric: float | None = None,
) -> pd.DataFrame:
    frame = df[keep_columns].copy()

    if private_only and "설립유형" in frame.columns:
        frame = frame[frame["설립유형"] == "사립"].copy()

    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
        if fillna_numeric is not None:
            frame[column] = frame[column].fillna(fillna_numeric)

    frame["기준년도"] = pd.to_numeric(frame["기준년도"], errors="coerce")
    if dropna_numeric:
        frame = frame.dropna(subset=["기준년도", *numeric_columns])
    else:
        frame = frame.dropna(subset=["기준년도"])

    frame["기준년도"] = frame["기준년도"].astype(int)

    if "본분교명" in frame.columns:
        if bonkyo_only:
            frame = frame[frame["본분교명"] == "본교"].copy()
        else:
            mask = frame["본분교명"] != "본교"
            frame.loc[mask, "학교명"] = (
                frame.loc[mask, "학교명"] + " (" + frame.loc[mask, "본분교명"] + ")"
            )

    return frame.sort_values(["기준년도", "학교명"]).reset_index(drop=True)


def prepare_budam_frame(df: pd.DataFrame) -> pd.DataFrame:
    df = _apply_column_aliases(df)
    required = ["기준년도", "학교명", "부담율"]
    _check_columns(df, required)
    frame = df[required].copy()
    frame["부담율"] = pd.to_numeric(frame["부담율"], errors="coerce")
    frame["기준년도"] = pd.to_numeric(frame["기준년도"], errors="coerce")
    frame = frame.dropna(subset=["기준년도", "부담율"])
    frame["기준년도"] = frame["기준년도"].astype(int)
    return frame.sort_values(["기준년도", "학교명"]).reset_index(drop=True)


def prepare_gyowon_frame(df: pd.DataFrame, *, bonkyo_only: bool = True) -> pd.DataFrame:
    df = _apply_column_aliases(df)
    required = [
        "기준년도",
        "학교명",
        "본분교명",
        "설립유형",
        GYOWON_COL_JEONGWON,
        GYOWON_COL_JAEHAK,
    ]
    _check_columns(df, required)
    frame = _normalize_school_frame(
        df,
        numeric_columns=[GYOWON_COL_JEONGWON, GYOWON_COL_JAEHAK],
        bonkyo_only=bonkyo_only,
        keep_columns=required,
    )
    return frame[["기준년도", "학교명", "본분교명", GYOWON_COL_JEONGWON, GYOWON_COL_JAEHAK]]


def prepare_research_frame(df: pd.DataFrame, *, bonkyo_only: bool = True) -> pd.DataFrame:
    df = _apply_column_aliases(df)
    required = [
        "기준년도",
        "학교명",
        "본분교명",
        "설립유형",
        RESEARCH_COL_IN,
        RESEARCH_COL_OUT,
    ]
    _check_columns(df, required)
    return _normalize_school_frame(
        df,
        numeric_columns=[RESEARCH_COL_IN, RESEARCH_COL_OUT],
        bonkyo_only=bonkyo_only,
        keep_columns=required,
        dropna_numeric=False,
        fillna_numeric=0.0,
    )


def prepare_paper_frame(df: pd.DataFrame, *, bonkyo_only: bool = True) -> pd.DataFrame:
    df = _apply_column_aliases(df)
    required = [
        "기준년도",
        "학교명",
        "본분교명",
        "설립유형",
        PAPER_COL_JAEJI,
        PAPER_COL_SCI,
    ]
    _check_columns(df, required)
    return _normalize_school_frame(
        df,
        numeric_columns=[PAPER_COL_JAEJI, PAPER_COL_SCI],
        bonkyo_only=bonkyo_only,
        keep_columns=required,
        dropna_numeric=False,
        fillna_numeric=0.0,
    )


def prepare_jirosung_frame(df: pd.DataFrame, *, bonkyo_only: bool = True) -> pd.DataFrame:
    df = _apply_column_aliases(df)
    raw_columns = [
        "기준년도",
        "학교명",
        "본분교명",
        "설립유형",
        "졸업자",
        "취업자",
        "진학자",
        "입대자",
        "취업불가능자",
        "외국인유학생",
        "건강보험직장가입제외대상",
    ]
    _check_columns(df, raw_columns)
    frame = df[raw_columns].copy()
    frame = frame[frame["설립유형"] == "사립"].copy()

    for column in raw_columns[4:]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0)

    denominator = (
        frame["졸업자"]
        - frame["입대자"]
        - frame["취업불가능자"]
        - frame["외국인유학생"]
        - frame["건강보험직장가입제외대상"]
    )
    frame["졸업생_진로_성과"] = ((frame["취업자"] + frame["진학자"]) / denominator) * 100
    frame["졸업생_진로_성과"] = (
        frame["졸업생_진로_성과"]
        .replace([float("inf"), float("-inf")], float("nan"))
        .round(1)
    )
    frame = _normalize_school_frame(
        frame,
        numeric_columns=["졸업생_진로_성과"],
        bonkyo_only=bonkyo_only,
        keep_columns=["기준년도", "학교명", "본분교명", "설립유형", "졸업생_진로_성과"],
    )
    return frame[["기준년도", "학교명", "본분교명", "졸업생_진로_성과"]]


def prepare_gyeolsan_frame(df: pd.DataFrame) -> pd.DataFrame:
    frame = _apply_column_aliases(df.copy())
    frame.columns = frame.columns.str.strip()
    required = {
        "학교명",
        "회계",
        "지역",
        "학급",
        "설립",
        "학종",
        "회계연도",
        "2.운영수입[1086]",
        "4.등록금수입[1002]",
        "4.기부금수입[1035]",
    }
    _check_columns(frame, required)

    for column in ["학교명", "회계", "지역", "학급", "설립", "학종", "회계연도"]:
        frame[column] = frame[column].astype(str).str.strip()

    frame = frame[
        (frame["회계"] == "교비")
        & (frame["지역"] == "서울")
        & (frame["학급"] == "대학")
        & (frame["설립"] == "사립")
    ].copy()

    frame["기준년도"] = pd.to_numeric(
        frame["회계연도"].str.replace("년", "", regex=False),
        errors="coerce",
    )
    rename_map = {
        "2.운영수입[1086]": "운영수입",
        "4.등록금수입[1002]": "등록금수입",
        "4.기부금수입[1035]": "기부금수입",
    }
    for raw_col, new_col in rename_map.items():
        frame[new_col] = pd.to_numeric(
            frame[raw_col].astype(str).str.replace(",", "", regex=False),
            errors="coerce",
        )

    frame = frame.dropna(subset=["기준년도", "운영수입", "등록금수입", "기부금수입"])
    frame["기준년도"] = frame["기준년도"].astype(int)
    frame = frame[frame["운영수입"] > 0].copy()
    frame["등록금비율"] = (frame["등록금수입"] / frame["운영수입"] * 100).round(2)
    frame["기부금비율"] = (frame["기부금수입"] / frame["운영수입"] * 100).round(2)
    keep_columns = [
        "기준년도",
        "학교명",
        "운영수입",
        "등록금수입",
        "기부금수입",
        "등록금비율",
        "기부금비율",
    ]
    return frame[keep_columns].sort_values(["기준년도", "학교명"]).reset_index(drop=True)


def load_budam_frame() -> pd.DataFrame:
    return prepare_budam_frame(_load_csv(BUDAM_CSV, BUDAM_CSV_ENCODING))


def load_gyowon_csv_frame(*, bonkyo_only: bool = True) -> pd.DataFrame:
    return prepare_gyowon_frame(
        _load_csv(GYOWON_CSV, GYOWON_CSV_ENCODING),
        bonkyo_only=bonkyo_only,
    )


def load_research_frame(*, bonkyo_only: bool = True) -> pd.DataFrame:
    return prepare_research_frame(
        _load_csv(RESEARCH_CSV, RESEARCH_CSV_ENCODING),
        bonkyo_only=bonkyo_only,
    )


def load_paper_frame(*, bonkyo_only: bool = True) -> pd.DataFrame:
    return prepare_paper_frame(
        _load_csv(PAPER_CSV, PAPER_CSV_ENCODING),
        bonkyo_only=bonkyo_only,
    )


def load_jirosung_frame(*, bonkyo_only: bool = True) -> pd.DataFrame:
    return prepare_jirosung_frame(
        _load_csv(JIROSUNG_CSV, JIROSUNG_CSV_ENCODING),
        bonkyo_only=bonkyo_only,
    )


def load_gyeolsan_frame() -> pd.DataFrame:
    return prepare_gyeolsan_frame(_load_csv(GYEOLSAN_CSV, GYEOLSAN_CSV_ENCODING))
