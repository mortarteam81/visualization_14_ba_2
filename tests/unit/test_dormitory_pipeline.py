from __future__ import annotations

import pandas as pd

from utils.config import DORMITORY_COL
from utils.data_pipeline import prepare_dormitory_frame


def test_prepare_dormitory_frame_filters_and_renames() -> None:
    raw = pd.DataFrame(
        {
            "reference_year": [2024, 2024, 2024, 2024],
            "university_name": ["성신여자대학교", "서울대학교", "가천대학교", "성신여자대학교"],
            "campus_type": ["본교", "본교", "본교", "분교"],
            "school_type": ["대학교", "대학교", "대학교", "대학교"],
            "founding_type_detail": ["사립", "국공립", "사립", "사립"],
            "region_name": ["서울", "서울", "경기", "서울"],
            "enrolled_students": [10000, 20000, 15000, 5000],
            "total_room_count": [100, 200, 150, 50],
            "dormitory_capacity": [1200, 3000, 1800, 400],
            "dormitory_applicants": [1500, 3100, 2000, 450],
            "dormitory_competition_rate": [1.3, 1.0, 1.1, 1.1],
            "dormitory_accommodation_rate_pct": [12.0, 15.0, 12.0, 8.0],
        }
    )

    result = prepare_dormitory_frame(raw)

    assert result["학교명"].tolist() == ["성신여자대학교"]
    assert result["기준년도"].tolist() == [2024]
    assert DORMITORY_COL in result.columns
    assert result[DORMITORY_COL].tolist() == [12.0]
