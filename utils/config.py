"""Global config constants backed by the typed metric registry."""

from __future__ import annotations

import os

from registry import APP_METADATA, get_metric, get_series


APP_TITLE = APP_METADATA["title"]
APP_SUBTITLE = APP_METADATA["subtitle"]
APP_ICON = APP_METADATA["icon"]
DATA_UPDATED = APP_METADATA["data_updated"]

_BUDAM = get_metric("budam")
BUDAM_CSV = _BUDAM.csv_file
BUDAM_CSV_ENCODING = _BUDAM.csv_encoding
BUDAM_THRESHOLD = get_series("budam_rate").threshold
BUDAM_DEFAULT_SCHOOL = _BUDAM.default_school
BUDAM_PAGE_TITLE = _BUDAM.title
BUDAM_PAGE_ICON = _BUDAM.icon

_GYOWON = get_metric("gyowon")
GYOWON_CSV = _GYOWON.csv_file
GYOWON_CSV_ENCODING = _GYOWON.csv_encoding
GYOWON_THRESHOLD = get_series("gyowon_jeongwon").threshold
GYOWON_DEFAULT_SCHOOL = _GYOWON.default_school
GYOWON_PAGE_TITLE = _GYOWON.title
GYOWON_PAGE_ICON = _GYOWON.icon
GYOWON_COL_JEONGWON = get_series("gyowon_jeongwon").column
GYOWON_COL_JAEHAK = get_series("gyowon_jaehak").column

_RESEARCH = get_metric("research")
RESEARCH_CSV = _RESEARCH.csv_file
RESEARCH_CSV_ENCODING = _RESEARCH.csv_encoding
RESEARCH_THRESHOLD_IN = get_series("research_in").threshold
RESEARCH_THRESHOLD_OUT = get_series("research_out").threshold
RESEARCH_DEFAULT_SCHOOL = _RESEARCH.default_school
RESEARCH_PAGE_TITLE = _RESEARCH.title
RESEARCH_PAGE_ICON = _RESEARCH.icon
RESEARCH_COL_IN = get_series("research_in").column
RESEARCH_COL_OUT = get_series("research_out").column

_PAPER = get_metric("paper")
PAPER_CSV = _PAPER.csv_file
PAPER_CSV_ENCODING = _PAPER.csv_encoding
PAPER_THRESHOLD_JAEJI = get_series("paper_jaeji").threshold
PAPER_THRESHOLD_SCI = get_series("paper_sci").threshold
PAPER_DEFAULT_SCHOOL = _PAPER.default_school
PAPER_PAGE_TITLE = _PAPER.title
PAPER_PAGE_ICON = _PAPER.icon
PAPER_COL_JAEJI = get_series("paper_jaeji").column
PAPER_COL_SCI = get_series("paper_sci").column

_JIROSUNG = get_metric("jirosung")
JIROSUNG_CSV = _JIROSUNG.csv_file
JIROSUNG_CSV_ENCODING = _JIROSUNG.csv_encoding
JIROSUNG_THRESHOLD = get_series("jirosung_outcome").threshold
JIROSUNG_DEFAULT_SCHOOL = _JIROSUNG.default_school
JIROSUNG_PAGE_TITLE = _JIROSUNG.title
JIROSUNG_PAGE_ICON = _JIROSUNG.icon

_TUITION = get_metric("tuition")
GYEOLSAN_CSV = _TUITION.csv_file
GYEOLSAN_CSV_ENCODING = _TUITION.csv_encoding
TUITION_THRESHOLD = get_series("tuition_ratio").threshold
TUITION_DEFAULT_SCHOOL = _TUITION.default_school
TUITION_PAGE_TITLE = _TUITION.title
TUITION_PAGE_ICON = _TUITION.icon

_DONATION = get_metric("donation")
DONATION_THRESHOLD = get_series("donation_ratio").threshold
DONATION_DEFAULT_SCHOOL = _DONATION.default_school
DONATION_PAGE_TITLE = _DONATION.title
DONATION_PAGE_ICON = _DONATION.icon

_EDUCATION_RETURN = get_metric("education_return")
EDUCATION_RETURN_CSV = _EDUCATION_RETURN.csv_file
EDUCATION_RETURN_CSV_ENCODING = _EDUCATION_RETURN.csv_encoding
EDUCATION_RETURN_DEFAULT_SCHOOL = _EDUCATION_RETURN.default_school
EDUCATION_RETURN_PAGE_TITLE = _EDUCATION_RETURN.title
EDUCATION_RETURN_PAGE_ICON = _EDUCATION_RETURN.icon
EDUCATION_RETURN_COL = get_series("education_return_rate").column

_DORMITORY = get_metric("dormitory_rate")
DORMITORY_CSV = _DORMITORY.csv_file
DORMITORY_CSV_ENCODING = _DORMITORY.csv_encoding
DORMITORY_THRESHOLD = get_series("dormitory_accommodation_rate").threshold
DORMITORY_DEFAULT_SCHOOL = _DORMITORY.default_school
DORMITORY_PAGE_TITLE = _DORMITORY.title
DORMITORY_PAGE_ICON = _DORMITORY.icon
DORMITORY_COL = get_series("dormitory_accommodation_rate").column

_LECTURER_PAY = get_metric("lecturer_pay")
LECTURER_PAY_CSV = _LECTURER_PAY.csv_file
LECTURER_PAY_CSV_ENCODING = _LECTURER_PAY.csv_encoding
LECTURER_PAY_DEFAULT_SCHOOL = _LECTURER_PAY.default_school
LECTURER_PAY_PAGE_TITLE = _LECTURER_PAY.title
LECTURER_PAY_PAGE_ICON = _LECTURER_PAY.icon
LECTURER_PAY_COL = get_series("lecturer_hourly_pay").column

_LIBRARY_MATERIAL_PURCHASE = get_metric("library_material_purchase")
LIBRARY_MATERIAL_PURCHASE_CSV = _LIBRARY_MATERIAL_PURCHASE.csv_file
LIBRARY_MATERIAL_PURCHASE_CSV_ENCODING = _LIBRARY_MATERIAL_PURCHASE.csv_encoding
LIBRARY_MATERIAL_PURCHASE_DEFAULT_SCHOOL = _LIBRARY_MATERIAL_PURCHASE.default_school
LIBRARY_MATERIAL_PURCHASE_PAGE_TITLE = _LIBRARY_MATERIAL_PURCHASE.title
LIBRARY_MATERIAL_PURCHASE_PAGE_ICON = _LIBRARY_MATERIAL_PURCHASE.icon
LIBRARY_MATERIAL_PURCHASE_COL = get_series("library_material_purchase_per_student").column

_LIBRARY_STAFF = get_metric("library_staff")
LIBRARY_STAFF_CSV = _LIBRARY_STAFF.csv_file
LIBRARY_STAFF_CSV_ENCODING = _LIBRARY_STAFF.csv_encoding
LIBRARY_STAFF_DEFAULT_SCHOOL = _LIBRARY_STAFF.default_school
LIBRARY_STAFF_PAGE_TITLE = _LIBRARY_STAFF.title
LIBRARY_STAFF_PAGE_ICON = _LIBRARY_STAFF.icon
LIBRARY_STAFF_COL = get_series("library_staff_per_1000_students").column

_STAFF_PER_STUDENT = get_metric("staff_per_student")
STAFF_PER_STUDENT_CSV = _STAFF_PER_STUDENT.csv_file
STAFF_PER_STUDENT_CSV_ENCODING = _STAFF_PER_STUDENT.csv_encoding
STAFF_PER_STUDENT_DEFAULT_SCHOOL = _STAFF_PER_STUDENT.default_school
STAFF_PER_STUDENT_PAGE_TITLE = _STAFF_PER_STUDENT.title
STAFF_PER_STUDENT_PAGE_ICON = _STAFF_PER_STUDENT.icon
STAFF_PER_STUDENT_COL = get_series("students_per_staff").column

CHART_HEIGHT = 620
CHART_THRESHOLD_COLOR = "#F59E0B"
CHART_TEMPLATE = "plotly_dark"

DATA_SOURCE: str = os.getenv("DATA_SOURCE", "csv")
DATAGOKR_API_KEY: str = os.getenv("DATAGOKR_API_KEY", "")
