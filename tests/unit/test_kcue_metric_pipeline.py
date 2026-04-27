from __future__ import annotations

import pandas as pd

from utils.config import STAFF_PER_STUDENT_COL
from utils.data_pipeline import prepare_staff_per_student_frame


def test_prepare_staff_per_student_frame_filters_and_uses_recalculated_value() -> None:
    raw = pd.DataFrame(
        {
            "metric_id": [
                "students_per_staff",
                "students_per_staff",
                "students_per_staff",
                "scholarship_ratio",
            ],
            "metric_label_ko": [
                "직원 1인당 학생수",
                "직원 1인당 학생수",
                "직원 1인당 학생수",
                "장학금 비율",
            ],
            "reference_year": [2025, 2025, 2025, 2025],
            "evaluation_cycle": ["4주기", "4주기", "4주기", "4주기"],
            "university_name": ["성신여자대학교", "서울대학교", "가천대학교", "성신여자대학교"],
            "founding_type": ["사립", "국립", "사립", "사립"],
            "region_name": ["서울", "서울", "경기", "서울"],
            "value": [38.123, 12.0, 24.0, 20.0],
            "value_original": [38.12, 12.0, 24.0, 20.0],
            "value_recalculated": ["38.1234", "12.0", "24.0", "20.0"],
            "numerator": [3812, 1200, 2400, 1000],
            "denominator": [100, 100, 100, 50],
            "unit": ["students_per_staff", "students_per_staff", "students_per_staff", "%"],
            "source_file_name": ["source.xlsx"] * 4,
        }
    )

    result = prepare_staff_per_student_frame(raw)

    assert result["학교명"].tolist() == ["성신여자대학교"]
    assert result["기준년도"].tolist() == [2025]
    assert result[STAFF_PER_STUDENT_COL].tolist() == [38.1234]
    assert result["분자"].tolist() == [3812]
    assert result["분모"].tolist() == [100]
