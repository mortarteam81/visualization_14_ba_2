from __future__ import annotations

import pandas as pd

from utils.config import LIBRARY_STAFF_COL
from utils.data_pipeline import prepare_library_staff_frame


def test_prepare_library_staff_frame_uses_recalculated_r_column() -> None:
    raw = pd.DataFrame(
        {
            "reference_year": [2025, 2025, 2025, 2025],
            "row_no": [1, 2, 3, 4],
            "university_name": ["성신여자대학교", "서울대학교", "가천대학교", "서울전문대학"],
            "school_type": ["대학", "대학", "대학", "전문대학"],
            "founding_type": ["사립", "국립", "사립", "사립"],
            "region_name": ["서울", "서울", "경기", "서울"],
            "size_group": ["B그룹", "A그룹", "A그룹", "C그룹"],
            "regular_staff_certified": [2.0, 3.0, 4.0, 5.0],
            "regular_staff_not_certified": [1.0, 1.0, 1.0, 1.0],
            "non_regular_staff_certified": [1.0, 1.0, 1.0, 1.0],
            "non_regular_staff_not_certified": [0.0, 0.0, 0.0, 0.0],
            "total_staff_certified": [3.0, 4.0, 5.0, 6.0],
            "total_staff_not_certified": [1.0, 1.0, 1.0, 1.0],
            "enrolled_students": [3_000, 3_000, 3_000, 3_000],
            "library_staff_per_1000_students_original": [9.9, 9.9, 9.9, 9.9],
            "student_count_basis": ["current_year"] * 4,
            "schema_group": ["current_2025"] * 4,
            "library_staff_per_1000_students_recalculated": ["1.20", "1.30", "1.40", "1.50"],
            "source_file_name": ["source.xlsx"] * 4,
        }
    )

    result = prepare_library_staff_frame(raw)

    assert result["학교명"].tolist() == ["성신여자대학교"]
    assert result["기준년도"].tolist() == [2025]
    assert result[LIBRARY_STAFF_COL].tolist() == [1.2]
    assert result["기준충족"].tolist() == [True]
