"""Legacy-compatible loader functions backed by the shared data pipeline."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.data_pipeline import (
    load_budam_frame,
    load_education_return_frame,
    load_gyeolsan_frame,
    load_gyowon_csv_frame,
    load_jirosung_frame,
    load_paper_frame,
    load_research_frame,
)


@st.cache_data(show_spinner="데이터 로딩 중...")
def load_budam_data() -> pd.DataFrame:
    return load_budam_frame()


@st.cache_data(show_spinner="데이터 로딩 중...")
def load_gyowon_data(bonkyo_only: bool = True) -> pd.DataFrame:
    return load_gyowon_csv_frame(bonkyo_only=bonkyo_only)


@st.cache_data(show_spinner="데이터 로딩 중...")
def load_research_data(bonkyo_only: bool = True) -> pd.DataFrame:
    return load_research_frame(bonkyo_only=bonkyo_only)


@st.cache_data(show_spinner="데이터 로딩 중...")
def load_paper_data(bonkyo_only: bool = True) -> pd.DataFrame:
    return load_paper_frame(bonkyo_only=bonkyo_only)


@st.cache_data(show_spinner="데이터 로딩 중...")
def load_jirosung_data(bonkyo_only: bool = True) -> pd.DataFrame:
    return load_jirosung_frame(bonkyo_only=bonkyo_only)


@st.cache_data(show_spinner="데이터 로딩 중...")
def load_gyeolsan_data() -> pd.DataFrame:
    return load_gyeolsan_frame()


@st.cache_data(show_spinner="?곗씠??濡쒕뵫 以?..")
def load_education_return_data() -> pd.DataFrame:
    return load_education_return_frame()
