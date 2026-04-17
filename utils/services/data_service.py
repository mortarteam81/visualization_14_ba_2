"""Service helpers for metric data transformations."""

from __future__ import annotations

import pandas as pd

from utils.data_pipeline import prepare_gyowon_frame


class GyowonDataService:
    """Backward-compatible service wrapper over the shared pipeline."""

    @staticmethod
    def prepare(df: pd.DataFrame, bonkyo_only: bool = True) -> pd.DataFrame:
        return prepare_gyowon_frame(df, bonkyo_only=bonkyo_only)
