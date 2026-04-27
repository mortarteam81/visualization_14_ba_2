from __future__ import annotations

import argparse
import json
import re
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd


DATASET_ID = "kcue_university_indicators"
SCHEMA_VERSION = "v1"
RAW_INPUT_DIR = Path("data/raw") / DATASET_ID / "original"
SHEET_NAME = "대학현황지표"

WIDE_OUTPUT = (
    f"data/processed/{DATASET_ID}/"
    f"{DATASET_ID}_2015_2025_{SCHEMA_VERSION}_utf8.csv"
)
LONG_OUTPUT = (
    f"data/processed/{DATASET_ID}/"
    f"kcue_university_metric_values_2015_2025_{SCHEMA_VERSION}_utf8.csv"
)
SOURCE_OUTPUT = f"data/metadata/{DATASET_ID}_{SCHEMA_VERSION}.source.json"
SCHEMA_OUTPUT = f"data/metadata/{DATASET_ID}_{SCHEMA_VERSION}_schema.md"
REPORT_OUTPUT = f"data/metadata/{DATASET_ID}_{SCHEMA_VERSION}.processing_report.json"
RAW_README_OUTPUT = f"data/raw/{DATASET_ID}/README.md"


BASE_COLUMNS = [
    "reference_year",
    "evaluation_cycle",
    "university_name",
    "founding_type",
    "region_name",
    "source_file_name",
]

VALUE_COLUMNS = [
    "undergrad_enrolled_within_quota",
    "undergrad_enrolled_total",
    "total_enrolled_students_basis_1",
    "total_enrolled_students_basis_2",
    "total_enrolled_students_basis_3",
    "full_time_faculty_count",
    "legal_faculty_quota",
    "full_time_faculty_rate_pct_original",
    "full_time_faculty_rate_pct_recalculated",
    "adjunct_faculty_rate_pct_original",
    "faculty_combined_rate_pct_original",
    "building_facility_area_sqm",
    "building_required_area_sqm",
    "building_facility_rate_pct_original",
    "building_facility_rate_pct_recalculated",
    "freshman_admissions_within_quota",
    "freshman_recruitment_quota",
    "freshman_fill_rate_pct_original",
    "freshman_fill_rate_pct_recalculated",
    "enrolled_students_within_quota",
    "adjusted_student_quota",
    "student_fill_rate_pct_original",
    "student_fill_rate_pct_recalculated",
    "student_recruitment_performance_pct_original",
    "total_education_cost_krw",
    "tuition_revenue_for_education_return_krw",
    "education_cost_return_rate_pct_original",
    "education_cost_return_rate_pct_recalculated",
    "scholarship_amount_krw",
    "tuition_revenue_for_scholarship_krw",
    "scholarship_ratio_pct_original",
    "scholarship_ratio_pct_recalculated",
    "tuition_revenue_for_operating_revenue_ratio_krw",
    "operating_revenue_for_tuition_ratio_krw",
    "tuition_revenue_ratio_pct_original",
    "tuition_revenue_ratio_pct_recalculated",
    "donation_amount_krw",
    "operating_revenue_for_donation_ratio_krw",
    "donation_ratio_pct_original",
    "donation_ratio_pct_recalculated",
    "corporate_transfer_amount_krw",
    "operating_revenue_for_corporate_transfer_krw",
    "corporate_transfer_ratio_pct_original",
    "corporate_transfer_ratio_pct_recalculated",
    "legal_burden_paid_krw",
    "legal_burden_standard_krw",
    "legal_burden_rate_pct_original",
    "legal_burden_rate_pct_recalculated",
    "corporate_transfer_for_corporate_finance_krw",
    "corporate_general_account_finance_scale_krw",
    "corporate_finance_transfer_ratio_pct_original",
    "corporate_finance_transfer_ratio_pct_recalculated",
    "lecturer_pay_total_krw",
    "lecture_hours_total",
    "lecturer_hourly_pay_krw_original",
    "lecturer_hourly_pay_krw_recalculated",
    "internal_research_funds_thousand_krw",
    "full_time_faculty_count_internal_research",
    "internal_research_funds_per_faculty_thousand_krw_original",
    "internal_research_funds_per_faculty_thousand_krw_recalculated",
    "staff_enrolled_students",
    "staff_count",
    "students_per_staff_original",
    "students_per_staff_recalculated",
    "dormitory_capacity",
    "dormitory_enrolled_students",
    "dormitory_accommodation_rate_pct_original",
    "dormitory_accommodation_rate_pct_recalculated",
    "dormitory_domestic_residents",
    "dormitory_domestic_enrolled_students",
    "dormitory_domestic_accommodation_rate_pct_original",
    "dormitory_domestic_accommodation_rate_pct_recalculated",
    "library_material_purchase_expense_krw",
    "library_student_count",
    "library_material_purchase_per_student_krw_original",
    "library_material_purchase_per_student_krw_recalculated",
    "library_staff_count",
    "library_staff_enrolled_students",
    "library_staff_per_1000_students_original",
    "library_staff_per_1000_students_recalculated",
    "domestic_paper_count",
    "full_time_faculty_count_domestic_paper",
    "domestic_papers_per_faculty_original",
    "domestic_papers_per_faculty_recalculated",
    "sci_paper_count",
    "full_time_faculty_count_sci_paper",
    "sci_papers_per_faculty_original",
    "sci_papers_per_faculty_recalculated",
    "book_count",
    "full_time_faculty_count_book",
    "books_per_faculty_original",
    "books_per_faculty_recalculated",
    "external_research_funds_thousand_krw",
    "full_time_faculty_count_external_research",
    "external_research_funds_per_faculty_thousand_krw_original",
    "external_research_funds_per_faculty_thousand_krw_recalculated",
    "research_performance_vs_standard_original",
    "employment_count",
    "graduate_count",
    "employment_rate_pct_original",
    "employment_rate_pct_recalculated",
    "career_success_count",
    "career_target_count",
    "graduate_career_performance_pct_original",
    "graduate_career_performance_pct_recalculated",
]

WIDE_COLUMNS = BASE_COLUMNS + VALUE_COLUMNS


COLUMN_DESCRIPTIONS = {
    "reference_year": "기준연도",
    "evaluation_cycle": "평가 주기(2/3/4)",
    "university_name": "대학명",
    "founding_type": "설립구분",
    "region_name": "지역",
    "source_file_name": "원본 엑셀 파일명",
    "undergrad_enrolled_within_quota": "학부 정원내 재학생수",
    "undergrad_enrolled_total": "학부 정원내외 재학생수",
    "total_enrolled_students_basis_1": "원자료의 학부 및 대학원 재학생수 1번째 반복 컬럼",
    "total_enrolled_students_basis_2": "원자료의 학부 및 대학원 재학생수 2번째 반복 컬럼",
    "total_enrolled_students_basis_3": "원자료의 학부 및 대학원 재학생수 3번째 반복 컬럼",
    "full_time_faculty_count": "전임교원 확보율 산출용 전임교원수",
    "legal_faculty_quota": "전임교원 확보율 산출용 교원법정정원",
    "full_time_faculty_rate_pct_original": "원자료 전임교원 확보율",
    "full_time_faculty_rate_pct_recalculated": "전임교원수 / 교원법정정원 * 100",
    "adjunct_faculty_rate_pct_original": "4주기 원자료 겸임교원 확보율",
    "faculty_combined_rate_pct_original": "4주기 원자료 전임교원 및 겸임교원 확보율",
    "building_facility_area_sqm": "교사 시설면적",
    "building_required_area_sqm": "교사 기준면적",
    "building_facility_rate_pct_original": "원자료 교사 확보율",
    "building_facility_rate_pct_recalculated": "시설면적 / 기준면적 * 100",
    "freshman_admissions_within_quota": "정원내 입학자수",
    "freshman_recruitment_quota": "정원내 모집인원",
    "freshman_fill_rate_pct_original": "원자료 정원내 신입생 충원율",
    "freshman_fill_rate_pct_recalculated": "정원내 입학자수 / 정원내 모집인원 * 100",
    "enrolled_students_within_quota": "정원내 재학생수",
    "adjusted_student_quota": "학생정원-학생모집정지인원",
    "student_fill_rate_pct_original": "원자료 정원내 재학생 충원율",
    "student_fill_rate_pct_recalculated": "정원내 재학생수 / 조정 학생정원 * 100",
    "student_recruitment_performance_pct_original": "4주기 원자료 학생 충원 성과",
    "total_education_cost_krw": "총교육비, 2015~2017 천원 단위 원자료는 원 단위로 환산",
    "tuition_revenue_for_education_return_krw": "교육비 환원율 산출용 등록금",
    "education_cost_return_rate_pct_original": "원자료 교육비 환원율",
    "education_cost_return_rate_pct_recalculated": "총교육비 / 등록금 * 100",
    "scholarship_amount_krw": "장학금",
    "tuition_revenue_for_scholarship_krw": "장학금 비율 산출용 등록금",
    "scholarship_ratio_pct_original": "원자료 장학금 비율",
    "scholarship_ratio_pct_recalculated": "장학금 / 등록금 * 100",
    "tuition_revenue_for_operating_revenue_ratio_krw": "세입 중 등록금 비율 산출용 등록금",
    "operating_revenue_for_tuition_ratio_krw": "세입 중 등록금 비율 산출용 운영수입",
    "tuition_revenue_ratio_pct_original": "원자료 세입 중 등록금 비율",
    "tuition_revenue_ratio_pct_recalculated": "등록금 / 운영수입 * 100",
    "donation_amount_krw": "기부금",
    "operating_revenue_for_donation_ratio_krw": "세입 중 기부금 비율 산출용 운영수입",
    "donation_ratio_pct_original": "원자료 세입 중 기부금 비율",
    "donation_ratio_pct_recalculated": "기부금 / 운영수입 * 100",
    "corporate_transfer_amount_krw": "법인전입금",
    "operating_revenue_for_corporate_transfer_krw": "법인전입금 비율 산출용 운영수입",
    "corporate_transfer_ratio_pct_original": "원자료 세입 중 법인전입금 비율",
    "corporate_transfer_ratio_pct_recalculated": "법인전입금 / 운영수입 * 100",
    "legal_burden_paid_krw": "4주기 법정부담금 부담액",
    "legal_burden_standard_krw": "4주기 법정부담금 기준액",
    "legal_burden_rate_pct_original": "4주기 원자료 법정부담금 부담률",
    "legal_burden_rate_pct_recalculated": "법정부담금 부담액 / 법정부담금 기준액 * 100",
    "corporate_transfer_for_corporate_finance_krw": "4주기 법인 재정규모 대비 비율 산출용 법인전입금",
    "corporate_general_account_finance_scale_krw": "4주기 법인 일반회계 재정규모",
    "corporate_finance_transfer_ratio_pct_original": "4주기 원자료 법인 재정규모 대비 법인전입금 비율",
    "corporate_finance_transfer_ratio_pct_recalculated": "법인전입금 / 법인 일반회계 재정규모 * 100",
    "lecturer_pay_total_krw": "강사료 계",
    "lecture_hours_total": "강의시간수 계",
    "lecturer_hourly_pay_krw_original": "원자료 강사 강의료",
    "lecturer_hourly_pay_krw_recalculated": "강사료 계 / 강의시간수 계",
    "internal_research_funds_thousand_krw": "교내연구비(천원)",
    "full_time_faculty_count_internal_research": "교내연구비 산출용 전임교원수",
    "internal_research_funds_per_faculty_thousand_krw_original": "원자료 전임교원 1인당 교내연구비(천원)",
    "internal_research_funds_per_faculty_thousand_krw_recalculated": "교내연구비 / 전임교원수",
    "staff_enrolled_students": "직원 1인당 학생수 산출용 재학생수",
    "staff_count": "직원수",
    "students_per_staff_original": "원자료 직원 1인당 학생수",
    "students_per_staff_recalculated": "재학생수 / 직원수",
    "dormitory_capacity": "기숙사 수용인원",
    "dormitory_enrolled_students": "기숙사 수용률 산출용 재학생수",
    "dormitory_accommodation_rate_pct_original": "원자료 기숙사 수용률",
    "dormitory_accommodation_rate_pct_recalculated": "수용인원 / 재학생수 * 100",
    "dormitory_domestic_residents": "4주기 내국인 입사 인원",
    "dormitory_domestic_enrolled_students": "4주기 내국인 재학생수",
    "dormitory_domestic_accommodation_rate_pct_original": "4주기 원자료 기숙사 수용률 II",
    "dormitory_domestic_accommodation_rate_pct_recalculated": "내국인 입사 인원 / 내국인 재학생수 * 100",
    "library_material_purchase_expense_krw": "자료구입비",
    "library_student_count": "자료구입비 산출용 학생수",
    "library_material_purchase_per_student_krw_original": "원자료 재학생 1인당 연간 자료구입비",
    "library_material_purchase_per_student_krw_recalculated": "자료구입비 / 학생수",
    "library_staff_count": "도서관직원수",
    "library_staff_enrolled_students": "도서관 직원수 산출용 재학생수",
    "library_staff_per_1000_students_original": "원자료 재학생 1,000명당 도서관 직원수",
    "library_staff_per_1000_students_recalculated": "도서관직원수 / 재학생수 * 1000",
    "domestic_paper_count": "등재(후보)지 논문 건수",
    "full_time_faculty_count_domestic_paper": "등재(후보)지 논문 산출용 전임교원수",
    "domestic_papers_per_faculty_original": "원자료 전임교원 1인당 등재(후보)지 논문 실적",
    "domestic_papers_per_faculty_recalculated": "등재(후보)지 논문 건수 / 전임교원수",
    "sci_paper_count": "SCI급 논문 건수",
    "full_time_faculty_count_sci_paper": "SCI급 논문 산출용 전임교원수",
    "sci_papers_per_faculty_original": "원자료 전임교원 1인당 SCI급 논문 실적",
    "sci_papers_per_faculty_recalculated": "SCI급 논문 건수 / 전임교원수",
    "book_count": "저역서수",
    "full_time_faculty_count_book": "저역서 산출용 전임교원수",
    "books_per_faculty_original": "원자료 전임교원 1인당 저역서 실적",
    "books_per_faculty_recalculated": "저역서수 / 전임교원수",
    "external_research_funds_thousand_krw": "교외연구비(천원)",
    "full_time_faculty_count_external_research": "교외연구비 산출용 전임교원수",
    "external_research_funds_per_faculty_thousand_krw_original": "원자료 전임교원 1인당 교외연구비(천원)",
    "external_research_funds_per_faculty_thousand_krw_recalculated": "교외연구비 / 전임교원수",
    "research_performance_vs_standard_original": "원자료 연구성과 기준값 대비 실적",
    "employment_count": "2~3주기 취업자",
    "graduate_count": "2~3주기 졸업자",
    "employment_rate_pct_original": "원자료 졸업생 취업률",
    "employment_rate_pct_recalculated": "취업자 / 졸업자 * 100",
    "career_success_count": "4주기 취업자+창업자+진학자 수",
    "career_target_count": "4주기 취·창업 및 진학대상자 수",
    "graduate_career_performance_pct_original": "4주기 원자료 졸업생 진로 성과",
    "graduate_career_performance_pct_recalculated": "성과 인원 / 대상자 수 * 100",
}


METRICS = [
    {
        "metric_id": "full_time_faculty_rate",
        "label_ko": "전임교원 확보율",
        "value_original": "full_time_faculty_rate_pct_original",
        "value_recalculated": "full_time_faculty_rate_pct_recalculated",
        "numerator": "full_time_faculty_count",
        "denominator": "legal_faculty_quota",
        "unit": "%",
    },
    {
        "metric_id": "adjunct_faculty_rate",
        "label_ko": "겸임교원 확보율",
        "value_original": "adjunct_faculty_rate_pct_original",
        "unit": "%",
    },
    {
        "metric_id": "faculty_combined_rate",
        "label_ko": "전임교원 및 겸임교원 확보율",
        "value_original": "faculty_combined_rate_pct_original",
        "unit": "%",
    },
    {
        "metric_id": "building_facility_rate",
        "label_ko": "교사 확보율",
        "value_original": "building_facility_rate_pct_original",
        "value_recalculated": "building_facility_rate_pct_recalculated",
        "numerator": "building_facility_area_sqm",
        "denominator": "building_required_area_sqm",
        "unit": "%",
    },
    {
        "metric_id": "freshman_fill_rate",
        "label_ko": "정원내 신입생 충원율",
        "value_original": "freshman_fill_rate_pct_original",
        "value_recalculated": "freshman_fill_rate_pct_recalculated",
        "numerator": "freshman_admissions_within_quota",
        "denominator": "freshman_recruitment_quota",
        "unit": "%",
    },
    {
        "metric_id": "student_fill_rate",
        "label_ko": "정원내 재학생 충원율",
        "value_original": "student_fill_rate_pct_original",
        "value_recalculated": "student_fill_rate_pct_recalculated",
        "numerator": "enrolled_students_within_quota",
        "denominator": "adjusted_student_quota",
        "unit": "%",
    },
    {
        "metric_id": "student_recruitment_performance",
        "label_ko": "학생 충원 성과",
        "value_original": "student_recruitment_performance_pct_original",
        "unit": "%",
    },
    {
        "metric_id": "education_cost_return_rate",
        "label_ko": "교육비 환원율",
        "value_original": "education_cost_return_rate_pct_original",
        "value_recalculated": "education_cost_return_rate_pct_recalculated",
        "numerator": "total_education_cost_krw",
        "denominator": "tuition_revenue_for_education_return_krw",
        "unit": "%",
    },
    {
        "metric_id": "scholarship_ratio",
        "label_ko": "장학금 비율",
        "value_original": "scholarship_ratio_pct_original",
        "value_recalculated": "scholarship_ratio_pct_recalculated",
        "numerator": "scholarship_amount_krw",
        "denominator": "tuition_revenue_for_scholarship_krw",
        "unit": "%",
    },
    {
        "metric_id": "tuition_revenue_ratio",
        "label_ko": "세입 중 등록금 비율",
        "value_original": "tuition_revenue_ratio_pct_original",
        "value_recalculated": "tuition_revenue_ratio_pct_recalculated",
        "numerator": "tuition_revenue_for_operating_revenue_ratio_krw",
        "denominator": "operating_revenue_for_tuition_ratio_krw",
        "unit": "%",
    },
    {
        "metric_id": "donation_ratio",
        "label_ko": "세입 중 기부금 비율",
        "value_original": "donation_ratio_pct_original",
        "value_recalculated": "donation_ratio_pct_recalculated",
        "numerator": "donation_amount_krw",
        "denominator": "operating_revenue_for_donation_ratio_krw",
        "unit": "%",
    },
    {
        "metric_id": "corporate_transfer_ratio",
        "label_ko": "세입 중 법인전입금 비율",
        "value_original": "corporate_transfer_ratio_pct_original",
        "value_recalculated": "corporate_transfer_ratio_pct_recalculated",
        "numerator": "corporate_transfer_amount_krw",
        "denominator": "operating_revenue_for_corporate_transfer_krw",
        "unit": "%",
    },
    {
        "metric_id": "legal_burden_rate",
        "label_ko": "법정부담금 부담률",
        "value_original": "legal_burden_rate_pct_original",
        "value_recalculated": "legal_burden_rate_pct_recalculated",
        "numerator": "legal_burden_paid_krw",
        "denominator": "legal_burden_standard_krw",
        "unit": "%",
    },
    {
        "metric_id": "corporate_finance_transfer_ratio",
        "label_ko": "법인 재정규모 대비 법인전입금 비율",
        "value_original": "corporate_finance_transfer_ratio_pct_original",
        "value_recalculated": "corporate_finance_transfer_ratio_pct_recalculated",
        "numerator": "corporate_transfer_for_corporate_finance_krw",
        "denominator": "corporate_general_account_finance_scale_krw",
        "unit": "%",
    },
    {
        "metric_id": "lecturer_hourly_pay",
        "label_ko": "강사 강의료",
        "value_original": "lecturer_hourly_pay_krw_original",
        "value_recalculated": "lecturer_hourly_pay_krw_recalculated",
        "numerator": "lecturer_pay_total_krw",
        "denominator": "lecture_hours_total",
        "unit": "krw_per_hour",
    },
    {
        "metric_id": "internal_research_per_faculty",
        "label_ko": "전임교원 1인당 교내연구비",
        "value_original": "internal_research_funds_per_faculty_thousand_krw_original",
        "value_recalculated": "internal_research_funds_per_faculty_thousand_krw_recalculated",
        "numerator": "internal_research_funds_thousand_krw",
        "denominator": "full_time_faculty_count_internal_research",
        "unit": "thousand_krw_per_faculty",
    },
    {
        "metric_id": "students_per_staff",
        "label_ko": "직원 1인당 학생수",
        "value_original": "students_per_staff_original",
        "value_recalculated": "students_per_staff_recalculated",
        "numerator": "staff_enrolled_students",
        "denominator": "staff_count",
        "unit": "students_per_staff",
    },
    {
        "metric_id": "dormitory_accommodation_rate",
        "label_ko": "기숙사 수용률",
        "value_original": "dormitory_accommodation_rate_pct_original",
        "value_recalculated": "dormitory_accommodation_rate_pct_recalculated",
        "numerator": "dormitory_capacity",
        "denominator": "dormitory_enrolled_students",
        "unit": "%",
    },
    {
        "metric_id": "dormitory_domestic_accommodation_rate",
        "label_ko": "기숙사 수용률 II",
        "value_original": "dormitory_domestic_accommodation_rate_pct_original",
        "value_recalculated": "dormitory_domestic_accommodation_rate_pct_recalculated",
        "numerator": "dormitory_domestic_residents",
        "denominator": "dormitory_domestic_enrolled_students",
        "unit": "%",
    },
    {
        "metric_id": "library_material_purchase_per_student",
        "label_ko": "재학생 1인당 연간 자료구입비",
        "value_original": "library_material_purchase_per_student_krw_original",
        "value_recalculated": "library_material_purchase_per_student_krw_recalculated",
        "numerator": "library_material_purchase_expense_krw",
        "denominator": "library_student_count",
        "unit": "krw_per_student",
    },
    {
        "metric_id": "library_staff_per_1000_students",
        "label_ko": "재학생 1,000명당 도서관 직원수",
        "value_original": "library_staff_per_1000_students_original",
        "value_recalculated": "library_staff_per_1000_students_recalculated",
        "numerator": "library_staff_count",
        "denominator": "library_staff_enrolled_students",
        "unit": "staff_per_1000_students",
    },
    {
        "metric_id": "domestic_papers_per_faculty",
        "label_ko": "전임교원 1인당 등재(후보)지 논문 실적",
        "value_original": "domestic_papers_per_faculty_original",
        "value_recalculated": "domestic_papers_per_faculty_recalculated",
        "numerator": "domestic_paper_count",
        "denominator": "full_time_faculty_count_domestic_paper",
        "unit": "papers_per_faculty",
    },
    {
        "metric_id": "sci_papers_per_faculty",
        "label_ko": "전임교원 1인당 SCI급 논문 실적",
        "value_original": "sci_papers_per_faculty_original",
        "value_recalculated": "sci_papers_per_faculty_recalculated",
        "numerator": "sci_paper_count",
        "denominator": "full_time_faculty_count_sci_paper",
        "unit": "papers_per_faculty",
    },
    {
        "metric_id": "books_per_faculty",
        "label_ko": "전임교원 1인당 저역서 실적",
        "value_original": "books_per_faculty_original",
        "value_recalculated": "books_per_faculty_recalculated",
        "numerator": "book_count",
        "denominator": "full_time_faculty_count_book",
        "unit": "books_per_faculty",
    },
    {
        "metric_id": "external_research_per_faculty",
        "label_ko": "전임교원 1인당 교외연구비",
        "value_original": "external_research_funds_per_faculty_thousand_krw_original",
        "value_recalculated": "external_research_funds_per_faculty_thousand_krw_recalculated",
        "numerator": "external_research_funds_thousand_krw",
        "denominator": "full_time_faculty_count_external_research",
        "unit": "thousand_krw_per_faculty",
    },
    {
        "metric_id": "research_performance_vs_standard",
        "label_ko": "연구성과 기준값 대비 실적",
        "value_original": "research_performance_vs_standard_original",
        "unit": "score",
    },
    {
        "metric_id": "employment_rate",
        "label_ko": "졸업생 취업률",
        "value_original": "employment_rate_pct_original",
        "value_recalculated": "employment_rate_pct_recalculated",
        "numerator": "employment_count",
        "denominator": "graduate_count",
        "unit": "%",
    },
    {
        "metric_id": "graduate_career_performance",
        "label_ko": "졸업생 진로 성과",
        "value_original": "graduate_career_performance_pct_original",
        "value_recalculated": "graduate_career_performance_pct_recalculated",
        "numerator": "career_success_count",
        "denominator": "career_target_count",
        "unit": "%",
    },
]


def nfc(value: Any) -> str:
    return unicodedata.normalize("NFC", str(value))


def find_raw_dir(project_root: Path) -> Path:
    raw_dir = project_root / RAW_INPUT_DIR
    if raw_dir.exists():
        return raw_dir
    raise FileNotFoundError(f"Cannot find raw directory: {raw_dir}")


def parse_file_info(path: Path) -> tuple[int, int, str]:
    name = nfc(path.name)
    year_match = re.search(r"(20\d{2})년도", name)
    cycle_match = re.search(r"(\d+)주기", name)
    if not year_match or not cycle_match:
        raise ValueError(f"Cannot parse year/cycle from {name}")
    return int(year_match.group(1)), int(cycle_match.group(1)), name


def read_indicator_sheet(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=SHEET_NAME)
    drop_columns = []
    for column in df.columns:
        column_name = str(column)
        if column_name.startswith("Unnamed") and df[column].isna().all():
            drop_columns.append(column)
        elif column_name == "정량지표 명을 입력하는 공간" and df[column].isna().all():
            drop_columns.append(column)
    return df.drop(columns=drop_columns)


def clean_text(value: Any) -> str | None:
    if pd.isna(value):
        return None
    text = nfc(value).strip()
    return text or None


def number(value: Any, multiplier: float = 1.0) -> float | None:
    if pd.isna(value):
        return None
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        if not cleaned:
            return None
        value = cleaned
    parsed = pd.to_numeric(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return float(parsed) * multiplier


def ratio(numerator: Any, denominator: Any, factor: float = 100.0) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    try:
        return round(float(numerator) / float(denominator) * factor, 5)
    except ZeroDivisionError:
        return None


def blank_row(year: int, cycle: int, source_file_name: str, values: list[Any]) -> dict[str, Any]:
    row = {column: None for column in WIDE_COLUMNS}
    row.update(
        {
            "reference_year": year,
            "evaluation_cycle": cycle,
            "university_name": clean_text(values[0]),
            "founding_type": clean_text(values[1]),
            "region_name": clean_text(values[2]),
            "source_file_name": source_file_name,
        }
    )
    return row


def set_common(row: dict[str, Any], values: list[Any]) -> None:
    row["undergrad_enrolled_within_quota"] = number(values[3])
    row["undergrad_enrolled_total"] = number(values[4])
    row["total_enrolled_students_basis_1"] = number(values[5])
    row["total_enrolled_students_basis_2"] = number(values[6])
    row["total_enrolled_students_basis_3"] = number(values[7])


def map_cycle_2(values: list[Any], year: int, cycle: int, source_file_name: str) -> dict[str, Any]:
    row = blank_row(year, cycle, source_file_name, values)
    set_common(row, values)
    money = 1000.0

    row["full_time_faculty_count"] = number(values[8])
    row["legal_faculty_quota"] = number(values[9])
    row["full_time_faculty_rate_pct_original"] = number(values[10])
    row["building_facility_area_sqm"] = number(values[11])
    row["building_required_area_sqm"] = number(values[12])
    row["building_facility_rate_pct_original"] = number(values[13])
    row["freshman_admissions_within_quota"] = number(values[14])
    row["freshman_recruitment_quota"] = number(values[15])
    row["freshman_fill_rate_pct_original"] = number(values[16])
    row["enrolled_students_within_quota"] = number(values[17])
    row["adjusted_student_quota"] = number(values[18])
    row["student_fill_rate_pct_original"] = number(values[19])
    row["total_education_cost_krw"] = number(values[20], money)
    row["tuition_revenue_for_education_return_krw"] = number(values[21], money)
    row["education_cost_return_rate_pct_original"] = number(values[22])
    row["scholarship_amount_krw"] = number(values[23], money)
    row["tuition_revenue_for_scholarship_krw"] = number(values[24], money)
    row["scholarship_ratio_pct_original"] = number(values[25])
    row["tuition_revenue_for_operating_revenue_ratio_krw"] = number(values[26], money)
    row["operating_revenue_for_tuition_ratio_krw"] = number(values[27], money)
    row["tuition_revenue_ratio_pct_original"] = number(values[28])
    row["donation_amount_krw"] = number(values[29], money)
    row["operating_revenue_for_donation_ratio_krw"] = number(values[30], money)
    row["donation_ratio_pct_original"] = number(values[31])
    row["corporate_transfer_amount_krw"] = number(values[32], money)
    row["operating_revenue_for_corporate_transfer_krw"] = number(values[33], money)
    row["corporate_transfer_ratio_pct_original"] = number(values[34])
    row["lecturer_pay_total_krw"] = number(values[35])
    row["lecture_hours_total"] = number(values[36])
    row["lecturer_hourly_pay_krw_original"] = number(values[37])
    row["internal_research_funds_thousand_krw"] = number(values[38])
    row["full_time_faculty_count_internal_research"] = number(values[39])
    row["internal_research_funds_per_faculty_thousand_krw_original"] = number(values[40])
    row["staff_enrolled_students"] = number(values[41])
    row["staff_count"] = number(values[42])
    row["students_per_staff_original"] = number(values[43])
    row["dormitory_capacity"] = number(values[44])
    row["dormitory_enrolled_students"] = number(values[45])
    row["dormitory_accommodation_rate_pct_original"] = number(values[46])
    row["library_material_purchase_expense_krw"] = number(values[47])
    row["library_student_count"] = number(values[48])
    row["library_material_purchase_per_student_krw_original"] = number(values[49])
    row["library_staff_count"] = number(values[50])
    row["library_staff_enrolled_students"] = number(values[51])
    row["library_staff_per_1000_students_original"] = number(values[52])
    row["domestic_paper_count"] = number(values[53])
    row["full_time_faculty_count_domestic_paper"] = number(values[54])
    row["domestic_papers_per_faculty_original"] = number(values[55])
    row["sci_paper_count"] = number(values[56])
    row["full_time_faculty_count_sci_paper"] = number(values[57])
    row["sci_papers_per_faculty_original"] = number(values[58])
    row["book_count"] = number(values[59])
    row["full_time_faculty_count_book"] = number(values[60])
    row["books_per_faculty_original"] = number(values[61])
    row["external_research_funds_thousand_krw"] = number(values[62])
    row["full_time_faculty_count_external_research"] = number(values[63])
    row["external_research_funds_per_faculty_thousand_krw_original"] = number(values[64])
    row["research_performance_vs_standard_original"] = number(values[65])
    row["employment_count"] = number(values[66])
    row["graduate_count"] = number(values[67])
    row["employment_rate_pct_original"] = number(values[68])
    return row


def map_cycle_3(values: list[Any], year: int, cycle: int, source_file_name: str) -> dict[str, Any]:
    row = blank_row(year, cycle, source_file_name, values)
    set_common(row, values)

    row["tuition_revenue_for_operating_revenue_ratio_krw"] = number(values[8])
    row["operating_revenue_for_tuition_ratio_krw"] = number(values[9])
    row["tuition_revenue_ratio_pct_original"] = number(values[10])
    row["donation_amount_krw"] = number(values[11])
    row["operating_revenue_for_donation_ratio_krw"] = number(values[12])
    row["donation_ratio_pct_original"] = number(values[13])
    row["corporate_transfer_amount_krw"] = number(values[14])
    row["operating_revenue_for_corporate_transfer_krw"] = number(values[15])
    row["corporate_transfer_ratio_pct_original"] = number(values[16])
    row["total_education_cost_krw"] = number(values[17])
    row["tuition_revenue_for_education_return_krw"] = number(values[18])
    row["education_cost_return_rate_pct_original"] = number(values[19])
    row["full_time_faculty_count"] = number(values[20])
    row["legal_faculty_quota"] = number(values[21])
    row["full_time_faculty_rate_pct_original"] = number(values[22])
    row["lecturer_pay_total_krw"] = number(values[23])
    row["lecture_hours_total"] = number(values[24])
    row["lecturer_hourly_pay_krw_original"] = number(values[25])
    row["internal_research_funds_thousand_krw"] = number(values[26])
    row["full_time_faculty_count_internal_research"] = number(values[27])
    row["internal_research_funds_per_faculty_thousand_krw_original"] = number(values[28])
    row["staff_enrolled_students"] = number(values[29])
    row["staff_count"] = number(values[30])
    row["students_per_staff_original"] = number(values[31])
    row["scholarship_amount_krw"] = number(values[32])
    row["tuition_revenue_for_scholarship_krw"] = number(values[33])
    row["scholarship_ratio_pct_original"] = number(values[34])
    row["building_facility_area_sqm"] = number(values[35])
    row["building_required_area_sqm"] = number(values[36])
    row["building_facility_rate_pct_original"] = number(values[37])
    row["dormitory_capacity"] = number(values[38])
    row["dormitory_enrolled_students"] = number(values[39])
    row["dormitory_accommodation_rate_pct_original"] = number(values[40])
    row["library_material_purchase_expense_krw"] = number(values[41])
    row["library_student_count"] = number(values[42])
    row["library_material_purchase_per_student_krw_original"] = number(values[43])
    row["library_staff_count"] = number(values[44])
    row["library_staff_enrolled_students"] = number(values[45])
    row["library_staff_per_1000_students_original"] = number(values[46])
    row["freshman_admissions_within_quota"] = number(values[47])
    row["freshman_recruitment_quota"] = number(values[48])
    row["freshman_fill_rate_pct_original"] = number(values[49])
    row["enrolled_students_within_quota"] = number(values[50])
    row["adjusted_student_quota"] = number(values[51])
    row["student_fill_rate_pct_original"] = number(values[52])
    row["domestic_paper_count"] = number(values[53])
    row["full_time_faculty_count_domestic_paper"] = number(values[54])
    row["domestic_papers_per_faculty_original"] = number(values[55])
    row["sci_paper_count"] = number(values[56])
    row["full_time_faculty_count_sci_paper"] = number(values[57])
    row["sci_papers_per_faculty_original"] = number(values[58])
    row["book_count"] = number(values[59])
    row["full_time_faculty_count_book"] = number(values[60])
    row["books_per_faculty_original"] = number(values[61])
    row["external_research_funds_thousand_krw"] = number(values[62])
    row["full_time_faculty_count_external_research"] = number(values[63])
    row["external_research_funds_per_faculty_thousand_krw_original"] = number(values[64])
    row["research_performance_vs_standard_original"] = number(values[65])
    row["employment_count"] = number(values[66])
    row["graduate_count"] = number(values[67])
    row["employment_rate_pct_original"] = number(values[68])
    return row


def map_cycle_4(values: list[Any], year: int, cycle: int, source_file_name: str) -> dict[str, Any]:
    row = blank_row(year, cycle, source_file_name, values)
    set_common(row, values)

    row["tuition_revenue_for_operating_revenue_ratio_krw"] = number(values[8])
    row["operating_revenue_for_tuition_ratio_krw"] = number(values[9])
    row["tuition_revenue_ratio_pct_original"] = number(values[10])
    row["donation_amount_krw"] = number(values[11])
    row["operating_revenue_for_donation_ratio_krw"] = number(values[12])
    row["donation_ratio_pct_original"] = number(values[13])
    row["corporate_transfer_amount_krw"] = number(values[14])
    row["operating_revenue_for_corporate_transfer_krw"] = number(values[15])
    row["corporate_transfer_ratio_pct_original"] = number(values[16])
    row["legal_burden_paid_krw"] = number(values[17])
    row["legal_burden_standard_krw"] = number(values[18])
    row["legal_burden_rate_pct_original"] = number(values[19])
    row["corporate_transfer_for_corporate_finance_krw"] = number(values[20])
    row["corporate_general_account_finance_scale_krw"] = number(values[21])
    row["corporate_finance_transfer_ratio_pct_original"] = number(values[22])
    row["total_education_cost_krw"] = number(values[23])
    row["tuition_revenue_for_education_return_krw"] = number(values[24])
    row["education_cost_return_rate_pct_original"] = number(values[25])
    row["student_recruitment_performance_pct_original"] = number(values[26])
    row["career_success_count"] = number(values[27])
    row["career_target_count"] = number(values[28])
    row["graduate_career_performance_pct_original"] = number(values[29])
    row["full_time_faculty_rate_pct_original"] = number(values[30])
    row["adjunct_faculty_rate_pct_original"] = number(values[31])
    row["faculty_combined_rate_pct_original"] = number(values[32])
    row["lecturer_pay_total_krw"] = number(values[33])
    row["lecture_hours_total"] = number(values[34])
    row["lecturer_hourly_pay_krw_original"] = number(values[35])
    row["internal_research_funds_thousand_krw"] = number(values[36])
    row["full_time_faculty_count_internal_research"] = number(values[37])
    row["internal_research_funds_per_faculty_thousand_krw_original"] = number(values[38])
    row["domestic_paper_count"] = number(values[39])
    row["full_time_faculty_count_domestic_paper"] = number(values[40])
    row["domestic_papers_per_faculty_original"] = number(values[41])
    row["sci_paper_count"] = number(values[42])
    row["full_time_faculty_count_sci_paper"] = number(values[43])
    row["sci_papers_per_faculty_original"] = number(values[44])
    row["book_count"] = number(values[45])
    row["full_time_faculty_count_book"] = number(values[46])
    row["books_per_faculty_original"] = number(values[47])
    row["external_research_funds_thousand_krw"] = number(values[48])
    row["full_time_faculty_count_external_research"] = number(values[49])
    row["external_research_funds_per_faculty_thousand_krw_original"] = number(values[50])
    row["research_performance_vs_standard_original"] = number(values[51])
    row["staff_enrolled_students"] = number(values[52])
    row["staff_count"] = number(values[53])
    row["students_per_staff_original"] = number(values[54])
    row["scholarship_amount_krw"] = number(values[55])
    row["tuition_revenue_for_scholarship_krw"] = number(values[56])
    row["scholarship_ratio_pct_original"] = number(values[57])
    row["dormitory_capacity"] = number(values[58])
    row["dormitory_enrolled_students"] = number(values[59])
    row["dormitory_accommodation_rate_pct_original"] = number(values[60])
    row["dormitory_domestic_residents"] = number(values[61])
    row["dormitory_domestic_enrolled_students"] = number(values[62])
    row["dormitory_domestic_accommodation_rate_pct_original"] = number(values[63])
    row["library_material_purchase_expense_krw"] = number(values[64])
    row["library_student_count"] = number(values[65])
    row["library_material_purchase_per_student_krw_original"] = number(values[66])
    row["library_staff_count"] = number(values[67])
    row["library_staff_enrolled_students"] = number(values[68])
    row["library_staff_per_1000_students_original"] = number(values[69])
    return row


def add_recalculations(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    formulas = {
        "full_time_faculty_rate_pct_recalculated": ("full_time_faculty_count", "legal_faculty_quota", 100.0),
        "building_facility_rate_pct_recalculated": ("building_facility_area_sqm", "building_required_area_sqm", 100.0),
        "freshman_fill_rate_pct_recalculated": ("freshman_admissions_within_quota", "freshman_recruitment_quota", 100.0),
        "student_fill_rate_pct_recalculated": ("enrolled_students_within_quota", "adjusted_student_quota", 100.0),
        "education_cost_return_rate_pct_recalculated": ("total_education_cost_krw", "tuition_revenue_for_education_return_krw", 100.0),
        "scholarship_ratio_pct_recalculated": ("scholarship_amount_krw", "tuition_revenue_for_scholarship_krw", 100.0),
        "tuition_revenue_ratio_pct_recalculated": ("tuition_revenue_for_operating_revenue_ratio_krw", "operating_revenue_for_tuition_ratio_krw", 100.0),
        "donation_ratio_pct_recalculated": ("donation_amount_krw", "operating_revenue_for_donation_ratio_krw", 100.0),
        "corporate_transfer_ratio_pct_recalculated": ("corporate_transfer_amount_krw", "operating_revenue_for_corporate_transfer_krw", 100.0),
        "legal_burden_rate_pct_recalculated": ("legal_burden_paid_krw", "legal_burden_standard_krw", 100.0),
        "corporate_finance_transfer_ratio_pct_recalculated": (
            "corporate_transfer_for_corporate_finance_krw",
            "corporate_general_account_finance_scale_krw",
            100.0,
        ),
        "lecturer_hourly_pay_krw_recalculated": ("lecturer_pay_total_krw", "lecture_hours_total", 1.0),
        "internal_research_funds_per_faculty_thousand_krw_recalculated": (
            "internal_research_funds_thousand_krw",
            "full_time_faculty_count_internal_research",
            1.0,
        ),
        "students_per_staff_recalculated": ("staff_enrolled_students", "staff_count", 1.0),
        "dormitory_accommodation_rate_pct_recalculated": (
            "dormitory_capacity",
            "dormitory_enrolled_students",
            100.0,
        ),
        "dormitory_domestic_accommodation_rate_pct_recalculated": (
            "dormitory_domestic_residents",
            "dormitory_domestic_enrolled_students",
            100.0,
        ),
        "library_material_purchase_per_student_krw_recalculated": (
            "library_material_purchase_expense_krw",
            "library_student_count",
            1.0,
        ),
        "library_staff_per_1000_students_recalculated": (
            "library_staff_count",
            "library_staff_enrolled_students",
            1000.0,
        ),
        "domestic_papers_per_faculty_recalculated": (
            "domestic_paper_count",
            "full_time_faculty_count_domestic_paper",
            1.0,
        ),
        "sci_papers_per_faculty_recalculated": (
            "sci_paper_count",
            "full_time_faculty_count_sci_paper",
            1.0,
        ),
        "books_per_faculty_recalculated": ("book_count", "full_time_faculty_count_book", 1.0),
        "external_research_funds_per_faculty_thousand_krw_recalculated": (
            "external_research_funds_thousand_krw",
            "full_time_faculty_count_external_research",
            1.0,
        ),
        "employment_rate_pct_recalculated": ("employment_count", "graduate_count", 100.0),
        "graduate_career_performance_pct_recalculated": ("career_success_count", "career_target_count", 100.0),
    }

    for output, (numerator, denominator, factor) in formulas.items():
        frame[output] = [
            ratio(n, d, factor)
            for n, d in zip(frame[numerator], frame[denominator])
        ]
    return frame


def build_wide(project_root: Path) -> pd.DataFrame:
    raw_dir = find_raw_dir(project_root)
    rows = []
    for source_file in sorted(raw_dir.glob("*.xlsx")):
        year, cycle, source_file_name = parse_file_info(source_file)
        sheet = read_indicator_sheet(source_file)
        expected_columns = 70 if cycle == 4 else 69
        if sheet.shape[1] != expected_columns:
            raise ValueError(
                f"{source_file_name}: expected {expected_columns} columns after cleanup, "
                f"found {sheet.shape[1]}"
            )

        mapper = map_cycle_4 if cycle == 4 else map_cycle_3 if cycle == 3 else map_cycle_2
        for values in sheet.to_numpy().tolist():
            if clean_text(values[0]) is None:
                continue
            rows.append(mapper(values, year, cycle, source_file_name))

    frame = pd.DataFrame(rows, columns=WIDE_COLUMNS)
    frame = add_recalculations(frame)
    frame = frame[WIDE_COLUMNS].sort_values(["reference_year", "university_name"]).reset_index(drop=True)
    return frame


def build_long(wide: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, source in wide.iterrows():
        for spec in METRICS:
            original_col = spec["value_original"]
            recalculated_col = spec.get("value_recalculated")
            original = source.get(original_col)
            recalculated = source.get(recalculated_col) if recalculated_col else None
            if pd.isna(original) and (recalculated_col is None or pd.isna(recalculated)):
                continue
            value = recalculated if recalculated_col and not pd.isna(recalculated) else original
            numerator_col = spec.get("numerator")
            denominator_col = spec.get("denominator")
            rows.append(
                {
                    "metric_id": spec["metric_id"],
                    "metric_label_ko": spec["label_ko"],
                    "reference_year": int(source["reference_year"]),
                    "evaluation_cycle": int(source["evaluation_cycle"]),
                    "university_name": source["university_name"],
                    "founding_type": source["founding_type"],
                    "region_name": source["region_name"],
                    "value": value,
                    "value_original": original,
                    "value_recalculated": recalculated if recalculated_col else None,
                    "numerator": source.get(numerator_col) if numerator_col else None,
                    "denominator": source.get(denominator_col) if denominator_col else None,
                    "unit": spec["unit"],
                    "source_file_name": source["source_file_name"],
                }
            )
    return pd.DataFrame(rows)


def summarize_validation(wide: pd.DataFrame) -> dict[str, Any]:
    checks = []
    tolerance = 0.05
    for spec in METRICS:
        recalculated_col = spec.get("value_recalculated")
        if not recalculated_col:
            continue
        original_col = spec["value_original"]
        diff = (wide[original_col] - wide[recalculated_col]).abs()
        comparable = diff.notna()
        mismatch = comparable & (diff > tolerance)
        max_diff = None if diff[comparable].empty else round(float(diff[comparable].max()), 5)
        checks.append(
            {
                "metric_id": spec["metric_id"],
                "compared_rows": int(comparable.sum()),
                "mismatch_rows_over_0_05": int(mismatch.sum()),
                "max_abs_diff": max_diff,
            }
        )
    return {"tolerance": tolerance, "formula_checks": checks}


def report_payload(
    wide: pd.DataFrame,
    long: pd.DataFrame,
    project_root: Path,
) -> dict[str, Any]:
    raw_dir = find_raw_dir(project_root)
    files = sorted(nfc(path.name) for path in raw_dir.glob("*.xlsx"))
    duplicate_keys = wide.duplicated(["reference_year", "university_name"]).sum()
    year_counts = {
        str(year): int(count)
        for year, count in wide.groupby("reference_year")["university_name"].count().items()
    }
    metric_counts = {
        metric: int(count)
        for metric, count in long.groupby("metric_id")["university_name"].count().items()
    }
    missing_by_column = {
        column: int(wide[column].isna().sum())
        for column in WIDE_COLUMNS
        if wide[column].isna().any()
    }
    return {
        "dataset_id": DATASET_ID,
        "schema_version": SCHEMA_VERSION,
        "processed_at": date.today().isoformat(),
        "raw_file_count": len(files),
        "raw_files": files,
        "wide_output": WIDE_OUTPUT,
        "long_output": LONG_OUTPUT,
        "wide_rows": int(len(wide)),
        "wide_columns": len(WIDE_COLUMNS),
        "long_rows": int(len(long)),
        "duplicate_reference_year_university_rows": int(duplicate_keys),
        "year_counts": year_counts,
        "metric_counts": metric_counts,
        "missing_by_column": missing_by_column,
        "validation": summarize_validation(wide),
        "known_limitations": [
            "한국대학평가원 대학통계는 평가용 2차 집계 자료이므로, 최종 제출/심사 수치로 쓰기 전 원 공시자료와 대조가 필요하다.",
            "4주기 2025 파일은 일부 2~3주기 지표가 빠지고 신규 지표가 추가되어 지표별 연도 커버리지가 다르다.",
            "원자료에는 캠퍼스/본분교 코드와 대학알리미 학교 ID가 없어 학교명 기반 매칭만 가능하다.",
        ],
    }


def source_payload(project_root: Path) -> dict[str, Any]:
    raw_dir = find_raw_dir(project_root)
    file_infos = [parse_file_info(path) for path in sorted(raw_dir.glob("*.xlsx"))]
    return {
        "dataset_id": DATASET_ID,
        "dataset_name_ko": "한국대학평가원 대학현황지표",
        "dataset_name_en": "KCUE/KUAI University Indicator Statistics",
        "schema_version": SCHEMA_VERSION,
        "source_name": "한국대학평가원 대학통계",
        "source_org": "한국대학교육협의회 병설 한국대학평가원",
        "source_url": "https://aims.kcue.or.kr/kor/sub03/eval/evalView.do",
        "source_section": "대학통계 > 대학 및 평가지표 > 데이터 다운로드",
        "download_method": "사용자 수동 다운로드",
        "original_file_format": "xlsx",
        "raw_input_directory": RAW_INPUT_DIR.as_posix(),
        "sheet_name": SHEET_NAME,
        "collected_years": sorted({year for year, _, _ in file_infos}),
        "evaluation_cycles": sorted({cycle for _, cycle, _ in file_infos}),
        "downloaded_at": "2026-04-27",
        "processed_at": date.today().isoformat(),
        "original_files": [name for _, _, name in file_infos],
        "processed_output_files": [WIDE_OUTPUT, LONG_OUTPUT],
        "processing_summary": [
            "연도별 엑셀의 대학현황지표 시트를 읽음",
            "2016년 파일의 빈 보조 컬럼 3개를 제거함",
            "2주기, 3주기, 4주기별 컬럼 순서 차이를 의미 기반 표준 컬럼으로 매핑함",
            "2015~2017년 천원 단위 재정 원자료를 원 단위 표준 컬럼으로 환산함",
            "원자료 지표값과 분자/분모 기반 재계산값을 함께 보존함",
            "wide CSV와 metric-values long CSV를 UTF-8-SIG로 저장함",
        ],
        "recommended_primary_table": WIDE_OUTPUT,
        "recommended_metric_values_table": LONG_OUTPUT,
        "notes": [
            "이 자료는 대학알리미/대학재정알리미/RINFO 등 1차 원자료를 한국대학평가원이 평가 주기별 지표로 집계한 2차 자료다.",
            "지표별 정의와 컬럼 구성은 주기별로 다르므로 장기 추세 분석 시 metric_id별 연도 커버리지를 먼저 확인해야 한다.",
            "학교명 외 식별자가 없으므로 후속 DB에서는 학교 ID 매핑 테이블을 별도로 붙이는 것을 권장한다.",
        ],
    }


def schema_markdown() -> str:
    lines = [
        "# 한국대학평가원 대학현황지표 v1 스키마",
        "",
        "## 산출물",
        "",
        f"- Wide CSV: `{WIDE_OUTPUT}`",
        f"- Long CSV: `{LONG_OUTPUT}`",
        f"- Source metadata: `{SOURCE_OUTPUT}`",
        f"- Processing report: `{REPORT_OUTPUT}`",
        "",
        "## Wide CSV 컬럼",
        "",
        "| column | description |",
        "| --- | --- |",
    ]
    for column in WIDE_COLUMNS:
        lines.append(f"| `{column}` | {COLUMN_DESCRIPTIONS.get(column, '')} |")

    lines.extend(
        [
            "",
            "## Long CSV 컬럼",
            "",
            "| column | description |",
            "| --- | --- |",
            "| `metric_id` | 표준 지표 ID |",
            "| `metric_label_ko` | 지표 한글명 |",
            "| `reference_year` | 기준연도 |",
            "| `evaluation_cycle` | 평가 주기 |",
            "| `university_name` | 대학명 |",
            "| `founding_type` | 설립구분 |",
            "| `region_name` | 지역 |",
            "| `value` | 기본 분석값. 재계산값이 있으면 재계산값, 없으면 원자료값 |",
            "| `value_original` | 원자료 지표값 |",
            "| `value_recalculated` | 분자/분모 기반 재계산값 |",
            "| `numerator` | 지표 산출 분자 |",
            "| `denominator` | 지표 산출 분모 |",
            "| `unit` | 단위 |",
            "| `source_file_name` | 원본 엑셀 파일명 |",
            "",
            "## 지표 ID",
            "",
            "| metric_id | label | unit |",
            "| --- | --- | --- |",
        ]
    )
    for metric in METRICS:
        lines.append(f"| `{metric['metric_id']}` | {metric['label_ko']} | `{metric['unit']}` |")

    lines.extend(
        [
            "",
            "## 처리상 주의",
            "",
            "- 2015~2017년 재정 관련 원자료는 다수 컬럼이 천원 단위이며, wide CSV의 `*_krw` 컬럼은 원 단위로 환산했다.",
            "- 교내/교외 연구비 컬럼은 원자료와 기존 앱 지표 관례에 맞춰 `thousand_krw` 단위를 유지한다.",
            "- 2025년 4주기 파일은 `법정부담금 부담률`, `법인 재정규모 대비 법인전입금 비율`, `학생 충원 성과`, `졸업생 진로 성과`, `기숙사 수용률 II`가 추가되고, `교사 확보율`, 신입생/재학생 충원율 세부 분자·분모가 빠져 있다.",
            "- 원자료에는 대학 식별코드가 없으므로 같은 학교명의 명칭 변경, 통폐합, 캠퍼스 분리 이슈는 별도 매핑으로 보정해야 한다.",
        ]
    )
    return "\n".join(lines) + "\n"


def raw_readme(project_root: Path) -> str:
    raw_dir = find_raw_dir(project_root)
    files = [parse_file_info(path) for path in sorted(raw_dir.glob("*.xlsx"))]
    lines = [
        "# 한국대학평가원 대학현황지표 원본 데이터",
        "",
        "## 출처",
        "",
        "- 사이트명: 한국대학평가원 대학통계",
        "- 운영기관: 한국대학교육협의회 병설 한국대학평가원",
        "- 메뉴 경로: 대학통계 > 대학 및 평가지표 > 데이터 다운로드",
        "- URL: https://aims.kcue.or.kr/kor/sub03/eval/evalView.do",
        "",
        "## 데이터셋 설명",
        "",
        "2015~2025년 대학별 대학현황지표 엑셀 원자료를 보존하고, 이를 표준 CSV와 DB 적재형 long CSV로 변환한다.",
        "평가 주기별로 지표명과 컬럼 배치가 달라 v1 변환에서는 주기별 위치 매핑을 명시적으로 적용한다.",
        "",
        "## 수집 방식",
        "",
        "- 수집 방식: 한국대학평가원 대학통계 화면에서 연도별 엑셀 파일 수동 다운로드",
        "- 수집일: 2026-04-27",
        f"- 원본 보존 위치: `{RAW_INPUT_DIR.as_posix()}`",
        "",
        "## 원본 파일 목록",
    ]
    for year, cycle, name in files:
        lines.append(f"- {year}년 {cycle}주기: `{name}`")
    lines.extend(
        [
            "",
            "## 가공 결과물",
            "",
            f"- `{WIDE_OUTPUT}`",
            f"- `{LONG_OUTPUT}`",
            f"- `{SOURCE_OUTPUT}`",
            f"- `{SCHEMA_OUTPUT}`",
            f"- `{REPORT_OUTPUT}`",
            "",
            "## 처리 개요",
            "",
            "1. 연도와 평가 주기를 파일명에서 추출",
            "2. `대학현황지표` 시트를 읽고 2016년 빈 보조 컬럼 제거",
            "3. 2주기, 3주기, 4주기 컬럼 순서 차이를 표준 영문 스키마로 매핑",
            "4. 2015~2017년 천원 단위 재정 컬럼을 원 단위 컬럼으로 환산",
            "5. 가능한 지표는 원자료값과 분자/분모 재계산값을 함께 보존",
            "6. wide CSV와 metric-values long CSV를 UTF-8-SIG로 저장",
            "",
            "## 객관적 주의사항",
            "",
            "- 이 데이터는 1차 공시 원자료가 아니라 한국대학평가원이 평가 지표 형태로 재집계한 2차 자료다.",
            "- 빠른 후보 DB 구축에는 매우 유용하지만, 최종 평가·공시·대외 보고 수치로 사용하기 전에는 대학알리미/대학재정알리미/RINFO 등 1차 출처와 대조해야 한다.",
            "- 2025년 4주기 지표 구조가 이전 주기와 달라, 단일 그래프에 장기 추세를 그릴 때는 metric_id별 정의 변경 여부를 반드시 표시해야 한다.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def install_script(project_root: Path) -> None:
    target = project_root / "scripts" / "build_kcue_university_indicators.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(Path(__file__).read_text(encoding="utf-8"), encoding="utf-8")


def update_allowlist(project_root: Path) -> None:
    path = project_root / "registry" / "raw_schemas.py"
    text = path.read_text(encoding="utf-8")
    additions = [
        f'        "{WIDE_OUTPUT}",',
        f'        "{LONG_OUTPUT}",',
    ]
    missing = [line for line in additions if line not in text]
    if not missing:
        return
    anchor = '        "data/processed/student_recruitment/student_recruitment_2026_candidate.csv",'
    if anchor not in text:
        raise ValueError("Cannot find raw schema allowlist insertion anchor")
    replacement = anchor + "\n" + "\n".join(missing)
    path.write_text(text.replace(anchor, replacement), encoding="utf-8")


def write_outputs(project_root: Path, install: bool = False, patch_allowlist: bool = False) -> None:
    wide = build_wide(project_root)
    long = build_long(wide)

    wide_path = project_root / WIDE_OUTPUT
    long_path = project_root / LONG_OUTPUT
    wide_path.parent.mkdir(parents=True, exist_ok=True)
    wide.to_csv(wide_path, index=False, encoding="utf-8-sig")
    long.to_csv(long_path, index=False, encoding="utf-8-sig")

    write_json(project_root / SOURCE_OUTPUT, source_payload(project_root))
    write_json(project_root / REPORT_OUTPUT, report_payload(wide, long, project_root))

    schema_path = project_root / SCHEMA_OUTPUT
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    schema_path.write_text(schema_markdown(), encoding="utf-8")

    readme_path = project_root / RAW_README_OUTPUT
    readme_path.parent.mkdir(parents=True, exist_ok=True)
    readme_path.write_text(raw_readme(project_root), encoding="utf-8")

    if install:
        install_script(project_root)
    if patch_allowlist:
        update_allowlist(project_root)

    print(
        json.dumps(
            {
                "wide_rows": int(len(wide)),
                "wide_columns": int(len(wide.columns)),
                "long_rows": int(len(long)),
                "wide_output": str(wide_path),
                "long_output": str(long_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--install-script", action="store_true")
    parser.add_argument("--patch-allowlist", action="store_true")
    args = parser.parse_args()
    write_outputs(args.project_root.resolve(), install=args.install_script, patch_allowlist=args.patch_allowlist)


if __name__ == "__main__":
    main()
