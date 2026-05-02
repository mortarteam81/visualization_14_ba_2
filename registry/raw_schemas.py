"""Raw CSV schema contracts for implemented metric inputs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

from .metadata import METRIC_REGISTRY


@dataclass(frozen=True)
class RawCsvSchema:
    """Required raw CSV columns for a registered metric input."""

    metric_id: str
    dataset_key: str
    csv_file: str
    csv_encoding: str
    required_columns: tuple[str, ...]

    @property
    def data_relative_path(self) -> Path:
        return Path("data") / self.csv_file

    def file_path(self, project_root: Path) -> Path:
        return project_root / self.data_relative_path


def _schema(metric_id: str, required_columns: tuple[str, ...]) -> RawCsvSchema:
    metric = METRIC_REGISTRY[metric_id]
    if not metric.implemented or not metric.csv_file:
        raise ValueError(f"{metric_id!r} is not an implemented CSV-backed metric")
    return RawCsvSchema(
        metric_id=metric.id,
        dataset_key=metric.dataset_key,
        csv_file=metric.csv_file,
        csv_encoding=metric.csv_encoding,
        required_columns=required_columns,
    )


RAW_SCHEMA_REGISTRY: Final[dict[str, RawCsvSchema]] = {
    "budam": _schema(
        "budam",
        (
            "기준년도",
            "학교명",
            "부담율",
        ),
    ),
    "gyowon": _schema(
        "gyowon",
        (
            "기준년도",
            "학교명",
            "본분교명",
            "설립유형",
            "전임교원 확보율(학생정원 기준)",
            "전임교원 확보율(재학생 기준)",
        ),
    ),
    "adjunct_faculty": _schema(
        "adjunct_faculty",
        (
            "reference_year",
            "university_name",
            "field_category",
            "source_file_name",
            "겸임교원확보율(편제정원_최종)",
            "겸임교원확보율(재학생_최종)",
        ),
    ),
    "fulltime_adjunct_faculty": _schema(
        "fulltime_adjunct_faculty",
        (
            "reference_year",
            "university_name",
            "field_category",
            "source_file_name",
            "교원확보율(전임교원)(편제정원)",
            "교원확보율(전임교원)(재학생)",
            "겸임교원확보율(편제정원_최종)",
            "겸임교원확보율(재학생_최종)",
        ),
    ),
    "faculty_securing_reference": _schema(
        "faculty_securing_reference",
        (
            "reference_year",
            "university_name",
            "field_category",
            "source_file_name",
            "교원확보율(전임교원)(편제정원)",
            "교원확보율(전임교원)(재학생)",
            "교원확보율(겸임포함)(편제정원)",
            "교원확보율(겸임포함)(재학생)",
            "교원확보율(초빙포함)(편제정원)",
            "교원확보율(초빙포함)(재학생)",
        ),
    ),
    "research": _schema(
        "research",
        (
            "기준년도",
            "학교명",
            "본분교명",
            "설립유형",
            "전임교원 1인당 연구비(교내)",
            "전임교원 1인당 연구비(교외)",
        ),
    ),
    "paper": _schema(
        "paper",
        (
            "기준년도",
            "학교명",
            "본분교명",
            "설립유형",
            "전임교원1인당논문실적(국내, 연구재단등재지(후보포함))",
            "전임교원1인당논문실적(국제, SCI급/SCOPUS학술지)",
        ),
    ),
    "jirosung": _schema(
        "jirosung",
        (
            "기준년도",
            "학교명",
            "본분교명",
            "설립유형",
            "졸업자",
            "취업자",
            "진학자",
            "입대자",
            "취업불가능자",
            "외국인유학생",
            "건강보험직장가입제외대상",
        ),
    ),
    "tuition": _schema(
        "tuition",
        (
            "학교명",
            "회계",
            "지역",
            "학급",
            "설립",
            "학종",
            "회계연도",
            "2.운영수입[1086]",
            "4.등록금수입[1002]",
            "4.기부금수입[1035]",
        ),
    ),
    "donation": _schema(
        "donation",
        (
            "학교명",
            "회계",
            "지역",
            "학급",
            "설립",
            "학종",
            "회계연도",
            "2.운영수입[1086]",
            "4.등록금수입[1002]",
            "4.기부금수입[1035]",
        ),
    ),
    "education_return": _schema(
        "education_return",
        (
            "survey_year",
            "university_name",
            "school_type",
            "region",
            "tuition_account_total",
            "industry_account_total",
            "tuition_revenue",
            "education_cost_return_rate_recalculated_pct",
        ),
    ),
    "dormitory_rate": _schema(
        "dormitory_rate",
        (
            "reference_year",
            "university_name",
            "campus_type",
            "school_type",
            "founding_type_detail",
            "region_name",
            "enrolled_students",
            "total_room_count",
            "dormitory_capacity",
            "dormitory_applicants",
            "dormitory_competition_rate",
            "dormitory_accommodation_rate_pct",
        ),
    ),
    "lecturer_pay": _schema(
        "lecturer_pay",
        (
            "reference_year",
            "university_name",
            "school_type",
            "founding_type",
            "region_name",
            "school_status",
            "lecturer_category",
            "payment_category",
            "paid_lecturer_count",
            "시간당 지급기준 단가(원)",
            "총 강의시간 수",
            "지급인원비율(%)",
        ),
    ),
    "library_material_purchase": _schema(
        "library_material_purchase",
        (
            "reference_year",
            "university_name",
            "school_type",
            "founding_type",
            "region_name",
            "size_group",
            "total_material_purchase_expense",
            "enrolled_students_current_year",
            "material_purchase_expense_per_student",
        ),
    ),
    "library_staff": _schema(
        "library_staff",
        (
            "reference_year",
            "university_name",
            "school_type",
            "founding_type",
            "region_name",
            "size_group",
            "regular_staff_certified",
            "regular_staff_not_certified",
            "non_regular_staff_certified",
            "non_regular_staff_not_certified",
            "total_staff_certified",
            "total_staff_not_certified",
            "enrolled_students",
            "library_staff_per_1000_students_recalculated",
        ),
    ),
    "staff_per_student": _schema(
        "staff_per_student",
        (
            "metric_id",
            "metric_label_ko",
            "reference_year",
            "evaluation_cycle",
            "university_name",
            "founding_type",
            "region_name",
            "value",
            "value_original",
            "value_recalculated",
            "numerator",
            "denominator",
            "unit",
            "source_file_name",
        ),
    ),
    "scholarship_ratio": _schema(
        "scholarship_ratio",
        (
            "metric_id",
            "metric_label_ko",
            "reference_year",
            "evaluation_cycle",
            "university_name",
            "founding_type",
            "region_name",
            "value",
            "value_original",
            "value_recalculated",
            "numerator",
            "denominator",
            "unit",
            "source_file_name",
        ),
    ),
    "corp_transfer_ratio": _schema(
        "corp_transfer_ratio",
        (
            "metric_id",
            "metric_label_ko",
            "reference_year",
            "evaluation_cycle",
            "university_name",
            "founding_type",
            "region_name",
            "value",
            "value_original",
            "value_recalculated",
            "numerator",
            "denominator",
            "unit",
            "source_file_name",
        ),
    ),
}


UNREGISTERED_RAW_CSV_ALLOWLIST: Final[frozenset[Path]] = frozenset(
    Path(path)
    for path in (
        "14-ba-2.-beobjeongbudamgeum-budam-hyeonhwang_daehag_beobjeongbudamgeum-budamryul-20260309-seoul-sojae-saribdaehag.csv",
        "data/연구비 수혜 실적.csv",
        "data/전임교원 확보율.csv",
        "data/전임교원 논문실적(샘플).csv",
        "data/전임교원_논문실적.csv",
        "data/raw/academyinfo/university_key_indicators/2026/academyinfo_key_indicators_2026.csv",
        "data/raw/pending_manual/classification/academyinfo_university_department_info_20230614.csv",
        "data/raw/pending_manual/manifest.csv",
        "data/raw/pending_manual/scholarship/kosaf_scholarship_by_university_20250831.csv",
        "data/processed/student_recruitment/student_recruitment_2026_candidate.csv",
        "data/processed/student_recruitment/student_recruitment_2026_candidate_v2.csv",
        "data/validation/mismatch_reports/student_recruitment_2026_v2.mismatch.csv",
        "data/conversion_outputs/academyinfo/budam/budam_2011_2024_candidate.csv",
        "data/conversion_outputs/academyinfo/dormitory_accommodation_status/dormitory_accommodation_status_2025_candidate.csv",
        "data/conversion_outputs/academyinfo/gyowon/gyowon_2008_2025_candidate.csv",
        "data/conversion_outputs/academyinfo/jirosung/jirosung_2008_2024_candidate.csv",
        "data/conversion_outputs/academyinfo/lecturer_pay/lecturer_pay_2023_2025_candidate.csv",
        "data/conversion_outputs/academyinfo/paper/paper_2007_2024_candidate.csv",
        "data/conversion_outputs/academyinfo/research/research_2007_2024_candidate.csv",
        "data/conversion_outputs/kasfo/education_return/kasfo_education_return_2020_2025_restated_candidate.csv",
        "data/conversion_outputs/kasfo/legal_burden/kasfo_legal_burden_2025_restated_candidate.csv",
        "data/conversion_outputs/kasfo/settlement/kasfo_settlement_processed_2022_2024_restated_candidate.csv",
        "data/conversion_outputs/kasfo/settlement/kasfo_settlement_raw_2020_2024_candidate.csv",
        "data/conversion_outputs/kcue/kcue_university_indicators_2015_2025_v1_candidate_utf8.csv",
        "data/conversion_outputs/kcue/kcue_university_metric_values_2015_2025_v1_candidate_utf8.csv",
        "data/conversion_outputs/rinfo/library_staff/library_staff_per_1000_students_2008_2025_candidate_all_no_inf.csv",
        "data/conversion_outputs/rinfo/library_staff/library_staff_per_1000_students_2008_2025_candidate_scope34_no_inf.csv",
        "data/conversion_outputs/rinfo/material_purchase/library_material_purchase_per_student_2008_2025_candidate_all_no_inf.csv",
        "data/conversion_outputs/rinfo/material_purchase/library_material_purchase_per_student_2008_2025_candidate_scope34_no_inf.csv",
        "data/validation/mismatch_reports/academyinfo_budam.mismatch.csv",
        "data/validation/mismatch_reports/academyinfo_dormitory_accommodation_status.mismatch.csv",
        "data/validation/mismatch_reports/academyinfo_gyowon.mismatch.csv",
        "data/validation/mismatch_reports/academyinfo_jirosung.mismatch.csv",
        "data/validation/mismatch_reports/academyinfo_lecturer_pay.mismatch.csv",
        "data/validation/mismatch_reports/academyinfo_paper.mismatch.csv",
        "data/validation/mismatch_reports/academyinfo_research.mismatch.csv",
        "data/validation/mismatch_reports/kasfo_education_return_formula_mismatch.csv",
        "data/validation/mismatch_reports/kasfo_education_return_raw_limitation.csv",
        "data/validation/mismatch_reports/kasfo_legal_burden_original_vs_processed.csv",
        "data/validation/mismatch_reports/kasfo_legal_burden_school_code_risk.csv",
        "data/validation/mismatch_reports/kasfo_settlement_alias_risk.csv",
        "data/validation/mismatch_reports/kasfo_settlement_processed_vs_raw_sample.csv",
        "data/validation/mismatch_reports/kcue_university_indicators_v1_candidate.mismatch.csv",
        "data/validation/mismatch_reports/rinfo_library_staff_coverage.csv",
        "data/validation/mismatch_reports/rinfo_library_staff_formula_mismatch.csv",
        "data/validation/mismatch_reports/rinfo_material_purchase_coverage.csv",
        "data/validation/mismatch_reports/rinfo_material_purchase_detail_mapping_limitation.csv",
        "data/validation/mismatch_reports/rinfo_material_purchase_formula_mismatch.csv",
        "data/processed/kcue_university_indicators/kcue_university_indicators_2015_2025_v1_utf8.csv",
        "data/processed/faculty_securing_rate/faculty_securing_metric_values_2015_2025_v1_utf8.csv",
        "data/processed/faculty_securing_rate/faculty_securing_rate_2015_2025_v1_utf8.csv",
    )
)


__all__ = [
    "RAW_SCHEMA_REGISTRY",
    "UNREGISTERED_RAW_CSV_ALLOWLIST",
    "RawCsvSchema",
]
