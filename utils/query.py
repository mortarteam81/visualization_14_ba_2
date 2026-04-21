"""Unified dataset query facade for Streamlit pages."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from utils.api.client import DataGoKrClient
from utils.config import DATA_SOURCE
from utils.data_pipeline import (
    load_budam_frame,
    load_education_return_frame,
    load_gyeolsan_frame,
    load_gyowon_csv_frame,
    load_jirosung_frame,
    load_paper_frame,
    load_research_frame,
    prepare_gyowon_frame,
)
from utils.repository.api_repository import ApiUniversityRepository


@dataclass(frozen=True)
class QueryOptions:
    include_branch: bool = False
    data_source: str | None = None


def _load_api_key() -> str:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    import os

    return os.getenv("DATAGOKR_API_KEY", "")


@st.cache_data(show_spinner="데이터 로딩 중...")
def _get_dataset(dataset_key: str, include_branch: bool, data_source: str | None) -> pd.DataFrame:
    bonkyo_only = not include_branch

    if dataset_key == "budam":
        return load_budam_frame()
    if dataset_key == "research":
        return load_research_frame(bonkyo_only=bonkyo_only)
    if dataset_key == "paper":
        return load_paper_frame(bonkyo_only=bonkyo_only)
    if dataset_key == "jirosung":
        return load_jirosung_frame(bonkyo_only=bonkyo_only)
    if dataset_key == "gyeolsan":
        return load_gyeolsan_frame()
    if dataset_key == "education_return":
        return load_education_return_frame()
    if dataset_key == "gyowon":
        source = (data_source or DATA_SOURCE or "csv").lower()
        if source == "api":
            api_key = _load_api_key()
            if not api_key:
                raise ValueError("DATA_SOURCE=api 설정 시 DATAGOKR_API_KEY가 필요합니다.")
            repository = ApiUniversityRepository(client=DataGoKrClient(api_key=api_key))
            return prepare_gyowon_frame(
                repository.get_gyowon_data(),
                bonkyo_only=bonkyo_only,
            )
        return load_gyowon_csv_frame(bonkyo_only=bonkyo_only)
    raise ValueError(f"알 수 없는 dataset_key: {dataset_key}")


def get_dataset(
    dataset_key: str,
    *,
    include_branch: bool = False,
    data_source: str | None = None,
) -> pd.DataFrame:
    options = QueryOptions(include_branch=include_branch, data_source=data_source)
    return _get_dataset(dataset_key, options.include_branch, options.data_source)
