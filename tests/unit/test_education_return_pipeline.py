from __future__ import annotations

import pandas as pd

from utils.config import EDUCATION_RETURN_COL
from utils.data_pipeline import prepare_education_return_frame


def test_prepare_education_return_frame_filters_and_renames() -> None:
    raw = pd.DataFrame(
        {
            "survey_year": [2024, 2024, 2024],
            "university_name": ["성신여자대학교", "서울대학교", "가천대학교"],
            "school_type": ["일반", "대학원", "일반"],
            "region": ["서울", "서울", "경기"],
            "tuition_account_total": [100.0, 200.0, 300.0],
            "industry_account_total": [10.0, 20.0, 30.0],
            "tuition_revenue": [80.0, 100.0, 120.0],
            "education_cost_return_rate_original_pct": [137.5, 220.0, 275.0],
            "education_cost_return_rate_recalculated_pct": [137.5, 220.0, 275.0],
        }
    )

    result = prepare_education_return_frame(raw)

    assert result["학교명"].tolist() == ["성신여자대학교"]
    assert result["기준년도"].tolist() == [2024]
    assert EDUCATION_RETURN_COL in result.columns
    assert result[EDUCATION_RETURN_COL].tolist() == [137.5]
