from __future__ import annotations

import pandas as pd

from registry import get_series
from utils.config import SCHOLARSHIP_RATIO_COL, STAFF_PER_STUDENT_COL
from utils.data_pipeline import prepare_scholarship_ratio_frame, prepare_staff_per_student_frame


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


def test_staff_per_student_threshold_is_lte_70_people() -> None:
    series = get_series("students_per_staff")

    assert series.threshold == 70.0
    assert series.threshold_direction == "lte"


def test_prepare_scholarship_ratio_frame_filters_and_uses_recalculated_value() -> None:
    raw = pd.DataFrame(
        {
            "metric_id": [
                "scholarship_ratio",
                "scholarship_ratio",
                "scholarship_ratio",
                "students_per_staff",
            ],
            "metric_label_ko": [
                "장학금 비율",
                "장학금 비율",
                "장학금 비율",
                "직원 1인당 학생수",
            ],
            "reference_year": [2025, 2025, 2025, 2025],
            "evaluation_cycle": ["4주기", "4주기", "4주기", "4주기"],
            "university_name": ["성신여자대학교", "서울대학교", "가천대학교", "성신여자대학교"],
            "founding_type": ["사립", "국립", "사립", "사립"],
            "region_name": ["서울", "서울", "경기", "서울"],
            "value": [13.12, 14.0, 15.0, 38.0],
            "value_original": [13.11, 14.0, 15.0, 38.0],
            "value_recalculated": ["13.1234", "14.0", "15.0", "38.0"],
            "numerator": [1312, 1400, 1500, 3800],
            "denominator": [10_000, 10_000, 10_000, 100],
            "unit": ["%", "%", "%", "students_per_staff"],
            "source_file_name": ["source.xlsx"] * 4,
        }
    )

    result = prepare_scholarship_ratio_frame(raw)

    assert result["학교명"].tolist() == ["성신여자대학교"]
    assert result["기준년도"].tolist() == [2025]
    assert result[SCHOLARSHIP_RATIO_COL].tolist() == [13.1234]
    assert result["분자"].tolist() == [1312]
    assert result["분모"].tolist() == [10_000]


def test_scholarship_ratio_threshold_is_12_percent() -> None:
    series = get_series("scholarship_ratio")

    assert series.threshold == 12.0
    assert series.threshold_direction == "gte"
