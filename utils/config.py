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

CHART_HEIGHT = 620
CHART_THRESHOLD_COLOR = "#F59E0B"
CHART_TEMPLATE = "plotly_dark"

DATA_SOURCE: str = os.getenv("DATA_SOURCE", "csv")
DATAGOKR_API_KEY: str = os.getenv("DATAGOKR_API_KEY", "")
