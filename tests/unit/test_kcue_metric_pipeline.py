from __future__ import annotations

import pandas as pd

from registry import get_series
from utils.config import (
    ADJUNCT_FACULTY_COL_ENROLLED_FINAL,
    ADJUNCT_FACULTY_COL_QUOTA_FINAL,
    CORP_TRANSFER_RATIO_COL,
    FACULTY_REFERENCE_COL_ADJUNCT_INCLUDED_ENROLLED_RATE,
    FACULTY_REFERENCE_COL_ADJUNCT_INCLUDED_QUOTA_RATE,
    FACULTY_REFERENCE_COL_FULLTIME_ENROLLED_RATE,
    FACULTY_REFERENCE_COL_FULLTIME_QUOTA_RATE,
    FACULTY_REFERENCE_COL_INVITED_INCLUDED_ENROLLED_RATE,
    FACULTY_REFERENCE_COL_INVITED_INCLUDED_QUOTA_RATE,
    FULLTIME_ADJUNCT_FACULTY_COL_ENROLLED_RATE,
    FULLTIME_ADJUNCT_FACULTY_COL_QUOTA_RATE,
    SCHOLARSHIP_RATIO_COL,
    STAFF_PER_STUDENT_COL,
)
from utils.data_pipeline import (
    prepare_adjunct_faculty_frame,
    prepare_corp_transfer_ratio_frame,
    prepare_faculty_securing_reference_frame,
    prepare_fulltime_adjunct_faculty_frame,
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


def test_prepare_fulltime_adjunct_faculty_frame_adds_fulltime_and_adjunct_final_values() -> None:
    raw = pd.DataFrame(
        {
            "reference_year": [2025, 2025, 2025, 2025],
            "survey_round": [20251, 20251, 20251, 20251],
            "school_code": [1, 2, 3, 4],
            "campus_type": ["본교", "본교", "본교", "본교"],
            "university_name": ["성신여자대학교", "서울대학교", "가천대학교", "성신여자대학교"],
            "field_category": ["총계", "총계", "총계", "인문사회계열"],
            "school_type": ["대학교", "대학교", "대학교", "대학교"],
            "region_name": ["서울", "서울", "경기", "서울"],
            "founding_type": ["사립", "국립", "사립", "사립"],
            "source_file_name": ["source.xlsx"] * 4,
            "교원확보율(전임교원)(편제정원)": [61.0, 70.0, 59.5, 80.0],
            "교원확보율(전임교원)(재학생)": [60.5, 71.0, 62.0, 81.0],
            "겸임교원확보율(편제정원_최종)": [3.543, 4.0, 4.0, 1.0],
            "겸임교원확보율(재학생_최종)": [3.321, 4.0, 3.0, 1.0],
        }
    )

    result = prepare_fulltime_adjunct_faculty_frame(raw)

    assert result["학교명"].tolist() == ["가천대학교", "성신여자대학교"]
    assert result[FULLTIME_ADJUNCT_FACULTY_COL_QUOTA_RATE].tolist() == [63.5, 64.543]
    assert result[FULLTIME_ADJUNCT_FACULTY_COL_ENROLLED_RATE].tolist() == [65.0, 63.821]
    assert result["평가주기"].tolist() == [4, 4]


def test_fulltime_adjunct_faculty_threshold_is_64_percent() -> None:
    quota = get_series("fulltime_adjunct_faculty_quota_rate")
    enrolled = get_series("fulltime_adjunct_faculty_enrolled_rate")

    assert quota.threshold == 64.0
    assert enrolled.threshold == 64.0
    assert quota.threshold_label == "4주기 인증 기준"
    assert enrolled.threshold_label == "4주기 인증 기준"


def test_prepare_faculty_securing_reference_frame_keeps_six_reference_rate_columns() -> None:
    raw = pd.DataFrame(
        {
            "reference_year": [2025, 2025, 2025, 2025],
            "survey_round": [20251, 20251, 20251, 20251],
            "school_code": [1, 2, 3, 4],
            "campus_type": ["본교", "본교", "본교", "본교"],
            "university_name": ["성신여자대학교", "서울대학교", "가천대학교", "성신여자대학교"],
            "field_category": ["총계", "총계", "총계", "인문사회계열"],
            "school_type": ["대학교", "대학교", "대학교", "대학교"],
            "region_name": ["서울", "서울", "경기", "서울"],
            "founding_type": ["사립", "국립", "사립", "사립"],
            "source_file_name": ["source.xlsx"] * 4,
            "교원확보율(전임교원)(편제정원)": [61.0, 70.0, 59.5, 80.0],
            "교원확보율(전임교원)(재학생)": [60.5, 71.0, 62.0, 81.0],
            "교원확보율(겸임포함)(편제정원)": [72.0, 77.0, 63.5, 82.0],
            "교원확보율(겸임포함)(재학생)": [71.5, 78.0, 65.0, 83.0],
            "교원확보율(초빙포함)(편제정원)": [101.0, 103.0, 99.5, 84.0],
            "교원확보율(초빙포함)(재학생)": [100.5, 104.0, 101.0, 85.0],
        }
    )

    result = prepare_faculty_securing_reference_frame(raw)

    assert result["학교명"].tolist() == ["가천대학교", "성신여자대학교"]
    assert result[FACULTY_REFERENCE_COL_FULLTIME_QUOTA_RATE].tolist() == [59.5, 61.0]
    assert result[FACULTY_REFERENCE_COL_FULLTIME_ENROLLED_RATE].tolist() == [62.0, 60.5]
    assert result[FACULTY_REFERENCE_COL_ADJUNCT_INCLUDED_QUOTA_RATE].tolist() == [63.5, 72.0]
    assert result[FACULTY_REFERENCE_COL_ADJUNCT_INCLUDED_ENROLLED_RATE].tolist() == [65.0, 71.5]
    assert result[FACULTY_REFERENCE_COL_INVITED_INCLUDED_QUOTA_RATE].tolist() == [99.5, 101.0]
    assert result[FACULTY_REFERENCE_COL_INVITED_INCLUDED_ENROLLED_RATE].tolist() == [101.0, 100.5]


def test_faculty_securing_reference_threshold_is_100_percent() -> None:
    series_ids = (
        "faculty_reference_fulltime_quota_rate",
        "faculty_reference_fulltime_enrolled_rate",
        "faculty_reference_adjunct_included_quota_rate",
        "faculty_reference_adjunct_included_enrolled_rate",
        "faculty_reference_invited_included_quota_rate",
        "faculty_reference_invited_included_enrolled_rate",
    )

    for series_id in series_ids:
        series = get_series(series_id)
        assert series.threshold == 100.0
        assert series.threshold_label == "교원확보율 100%"
