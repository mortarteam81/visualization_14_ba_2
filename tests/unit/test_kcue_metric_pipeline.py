from __future__ import annotations

import pandas as pd

from registry import get_series
from utils.config import (
    ADJUNCT_FACULTY_COL_ENROLLED_FINAL,
    ADJUNCT_FACULTY_COL_QUOTA_FINAL,
    CORP_TRANSFER_RATIO_COL,
    SCHOLARSHIP_RATIO_COL,
    STAFF_PER_STUDENT_COL,
)
from utils.data_pipeline import (
    prepare_adjunct_faculty_frame,
    prepare_corp_transfer_ratio_frame,
    prepare_scholarship_ratio_frame,
    prepare_staff_per_student_frame,
)


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


def test_prepare_corp_transfer_ratio_frame_filters_and_uses_recalculated_value() -> None:
    raw = pd.DataFrame(
        {
            "metric_id": [
                "corporate_transfer_ratio",
                "corporate_transfer_ratio",
                "corporate_transfer_ratio",
                "scholarship_ratio",
            ],
            "metric_label_ko": [
                "세입 중 법인전입금 비율",
                "세입 중 법인전입금 비율",
                "세입 중 법인전입금 비율",
                "장학금 비율",
            ],
            "reference_year": [2025, 2025, 2025, 2025],
            "evaluation_cycle": ["4주기", "4주기", "4주기", "4주기"],
            "university_name": ["성신여자대학교", "서울대학교", "가천대학교", "성신여자대학교"],
            "founding_type": ["사립", "국립", "사립", "사립"],
            "region_name": ["서울", "서울", "경기", "서울"],
            "value": [0.51, 0.3, 0.2, 13.0],
            "value_original": [0.50, 0.3, 0.2, 13.0],
            "value_recalculated": ["0.5123", "0.3", "0.2", "13.0"],
            "numerator": [5123, 3000, 2000, 1300],
            "denominator": [1_000_000, 1_000_000, 1_000_000, 10_000],
            "unit": ["%", "%", "%", "%"],
            "source_file_name": ["source.xlsx"] * 4,
        }
    )

    result = prepare_corp_transfer_ratio_frame(raw)

    assert result["학교명"].tolist() == ["성신여자대학교"]
    assert result["기준년도"].tolist() == [2025]
    assert result[CORP_TRANSFER_RATIO_COL].tolist() == [0.5123]
    assert result["분자"].tolist() == [5123]
    assert result["분모"].tolist() == [1_000_000]


def test_corp_transfer_ratio_threshold_is_point_four_percent() -> None:
    series = get_series("corp_transfer_ratio")

    assert series.threshold == 0.4
    assert series.threshold_direction == "gte"


def test_prepare_adjunct_faculty_frame_uses_final_recognition_columns() -> None:
    raw = pd.DataFrame(
        {
            "reference_year": [2025, 2025, 2025],
            "survey_round": [20251, 20251, 20251],
            "school_code": [1, 2, 3],
            "campus_type": ["본교", "본교", "본교"],
            "university_name": ["성신여자대학교", "서울대학교", "가천대학교"],
            "field_category": ["총계", "총계", "총계"],
            "school_type": ["대학교", "대학교", "대학교"],
            "region_name": ["서울", "서울", "경기"],
            "founding_type": ["사립", "국립", "사립"],
            "source_file_name": ["source.xlsx"] * 3,
            "겸임교원확보율(편제정원_최종)": [3.543, 4.0, 2.1],
            "겸임교원확보율(재학생_최종)": [3.321, 4.0, 2.0],
        }
    )

    result = prepare_adjunct_faculty_frame(raw)

    assert result["학교명"].tolist() == ["가천대학교", "성신여자대학교"]
    assert result[ADJUNCT_FACULTY_COL_QUOTA_FINAL].tolist() == [2.1, 3.543]
    assert result[ADJUNCT_FACULTY_COL_ENROLLED_FINAL].tolist() == [2.0, 3.321]
    assert result["평가주기"].tolist() == [4, 4]


def test_adjunct_faculty_threshold_is_max_recognition_four_percent() -> None:
    quota = get_series("adjunct_faculty_quota_final")
    enrolled = get_series("adjunct_faculty_enrolled_final")

    assert quota.threshold == 4.0
    assert enrolled.threshold == 4.0
    assert quota.threshold_label == "최대 인정값"
    assert enrolled.threshold_label == "최대 인정값"
