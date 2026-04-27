# 한국대학평가원 대학현황지표 v1 스키마

## 산출물

- Wide CSV: `data/processed/kcue_university_indicators/kcue_university_indicators_2015_2025_v1_utf8.csv`
- Long CSV: `data/processed/kcue_university_indicators/kcue_university_metric_values_2015_2025_v1_utf8.csv`
- Source metadata: `data/metadata/kcue_university_indicators_v1.source.json`
- Processing report: `data/metadata/kcue_university_indicators_v1.processing_report.json`

## Wide CSV 컬럼

| column | description |
| --- | --- |
| `reference_year` | 기준연도 |
| `evaluation_cycle` | 평가 주기(2/3/4) |
| `university_name` | 대학명 |
| `founding_type` | 설립구분 |
| `region_name` | 지역 |
| `source_file_name` | 원본 엑셀 파일명 |
| `undergrad_enrolled_within_quota` | 학부 정원내 재학생수 |
| `undergrad_enrolled_total` | 학부 정원내외 재학생수 |
| `total_enrolled_students_basis_1` | 원자료의 학부 및 대학원 재학생수 1번째 반복 컬럼 |
| `total_enrolled_students_basis_2` | 원자료의 학부 및 대학원 재학생수 2번째 반복 컬럼 |
| `total_enrolled_students_basis_3` | 원자료의 학부 및 대학원 재학생수 3번째 반복 컬럼 |
| `full_time_faculty_count` | 전임교원 확보율 산출용 전임교원수 |
| `legal_faculty_quota` | 전임교원 확보율 산출용 교원법정정원 |
| `full_time_faculty_rate_pct_original` | 원자료 전임교원 확보율 |
| `full_time_faculty_rate_pct_recalculated` | 전임교원수 / 교원법정정원 * 100 |
| `adjunct_faculty_rate_pct_original` | 4주기 원자료 겸임교원 확보율 |
| `faculty_combined_rate_pct_original` | 4주기 원자료 전임교원 및 겸임교원 확보율 |
| `building_facility_area_sqm` | 교사 시설면적 |
| `building_required_area_sqm` | 교사 기준면적 |
| `building_facility_rate_pct_original` | 원자료 교사 확보율 |
| `building_facility_rate_pct_recalculated` | 시설면적 / 기준면적 * 100 |
| `freshman_admissions_within_quota` | 정원내 입학자수 |
| `freshman_recruitment_quota` | 정원내 모집인원 |
| `freshman_fill_rate_pct_original` | 원자료 정원내 신입생 충원율 |
| `freshman_fill_rate_pct_recalculated` | 정원내 입학자수 / 정원내 모집인원 * 100 |
| `enrolled_students_within_quota` | 정원내 재학생수 |
| `adjusted_student_quota` | 학생정원-학생모집정지인원 |
| `student_fill_rate_pct_original` | 원자료 정원내 재학생 충원율 |
| `student_fill_rate_pct_recalculated` | 정원내 재학생수 / 조정 학생정원 * 100 |
| `student_recruitment_performance_pct_original` | 4주기 원자료 학생 충원 성과 |
| `total_education_cost_krw` | 총교육비, 2015~2017 천원 단위 원자료는 원 단위로 환산 |
| `tuition_revenue_for_education_return_krw` | 교육비 환원율 산출용 등록금 |
| `education_cost_return_rate_pct_original` | 원자료 교육비 환원율 |
| `education_cost_return_rate_pct_recalculated` | 총교육비 / 등록금 * 100 |
| `scholarship_amount_krw` | 장학금 |
| `tuition_revenue_for_scholarship_krw` | 장학금 비율 산출용 등록금 |
| `scholarship_ratio_pct_original` | 원자료 장학금 비율 |
| `scholarship_ratio_pct_recalculated` | 장학금 / 등록금 * 100 |
| `tuition_revenue_for_operating_revenue_ratio_krw` | 세입 중 등록금 비율 산출용 등록금 |
| `operating_revenue_for_tuition_ratio_krw` | 세입 중 등록금 비율 산출용 운영수입 |
| `tuition_revenue_ratio_pct_original` | 원자료 세입 중 등록금 비율 |
| `tuition_revenue_ratio_pct_recalculated` | 등록금 / 운영수입 * 100 |
| `donation_amount_krw` | 기부금 |
| `operating_revenue_for_donation_ratio_krw` | 세입 중 기부금 비율 산출용 운영수입 |
| `donation_ratio_pct_original` | 원자료 세입 중 기부금 비율 |
| `donation_ratio_pct_recalculated` | 기부금 / 운영수입 * 100 |
| `corporate_transfer_amount_krw` | 법인전입금 |
| `operating_revenue_for_corporate_transfer_krw` | 법인전입금 비율 산출용 운영수입 |
| `corporate_transfer_ratio_pct_original` | 원자료 세입 중 법인전입금 비율 |
| `corporate_transfer_ratio_pct_recalculated` | 법인전입금 / 운영수입 * 100 |
| `legal_burden_paid_krw` | 4주기 법정부담금 부담액 |
| `legal_burden_standard_krw` | 4주기 법정부담금 기준액 |
| `legal_burden_rate_pct_original` | 4주기 원자료 법정부담금 부담률 |
| `legal_burden_rate_pct_recalculated` | 법정부담금 부담액 / 법정부담금 기준액 * 100 |
| `corporate_transfer_for_corporate_finance_krw` | 4주기 법인 재정규모 대비 비율 산출용 법인전입금 |
| `corporate_general_account_finance_scale_krw` | 4주기 법인 일반회계 재정규모 |
| `corporate_finance_transfer_ratio_pct_original` | 4주기 원자료 법인 재정규모 대비 법인전입금 비율 |
| `corporate_finance_transfer_ratio_pct_recalculated` | 법인전입금 / 법인 일반회계 재정규모 * 100 |
| `lecturer_pay_total_krw` | 강사료 계 |
| `lecture_hours_total` | 강의시간수 계 |
| `lecturer_hourly_pay_krw_original` | 원자료 강사 강의료 |
| `lecturer_hourly_pay_krw_recalculated` | 강사료 계 / 강의시간수 계 |
| `internal_research_funds_thousand_krw` | 교내연구비(천원) |
| `full_time_faculty_count_internal_research` | 교내연구비 산출용 전임교원수 |
| `internal_research_funds_per_faculty_thousand_krw_original` | 원자료 전임교원 1인당 교내연구비(천원) |
| `internal_research_funds_per_faculty_thousand_krw_recalculated` | 교내연구비 / 전임교원수 |
| `staff_enrolled_students` | 직원 1인당 학생수 산출용 재학생수 |
| `staff_count` | 직원수 |
| `students_per_staff_original` | 원자료 직원 1인당 학생수 |
| `students_per_staff_recalculated` | 재학생수 / 직원수 |
| `dormitory_capacity` | 기숙사 수용인원 |
| `dormitory_enrolled_students` | 기숙사 수용률 산출용 재학생수 |
| `dormitory_accommodation_rate_pct_original` | 원자료 기숙사 수용률 |
| `dormitory_accommodation_rate_pct_recalculated` | 수용인원 / 재학생수 * 100 |
| `dormitory_domestic_residents` | 4주기 내국인 입사 인원 |
| `dormitory_domestic_enrolled_students` | 4주기 내국인 재학생수 |
| `dormitory_domestic_accommodation_rate_pct_original` | 4주기 원자료 기숙사 수용률 II |
| `dormitory_domestic_accommodation_rate_pct_recalculated` | 내국인 입사 인원 / 내국인 재학생수 * 100 |
| `library_material_purchase_expense_krw` | 자료구입비 |
| `library_student_count` | 자료구입비 산출용 학생수 |
| `library_material_purchase_per_student_krw_original` | 원자료 재학생 1인당 연간 자료구입비 |
| `library_material_purchase_per_student_krw_recalculated` | 자료구입비 / 학생수 |
| `library_staff_count` | 도서관직원수 |
| `library_staff_enrolled_students` | 도서관 직원수 산출용 재학생수 |
| `library_staff_per_1000_students_original` | 원자료 재학생 1,000명당 도서관 직원수 |
| `library_staff_per_1000_students_recalculated` | 도서관직원수 / 재학생수 * 1000 |
| `domestic_paper_count` | 등재(후보)지 논문 건수 |
| `full_time_faculty_count_domestic_paper` | 등재(후보)지 논문 산출용 전임교원수 |
| `domestic_papers_per_faculty_original` | 원자료 전임교원 1인당 등재(후보)지 논문 실적 |
| `domestic_papers_per_faculty_recalculated` | 등재(후보)지 논문 건수 / 전임교원수 |
| `sci_paper_count` | SCI급 논문 건수 |
| `full_time_faculty_count_sci_paper` | SCI급 논문 산출용 전임교원수 |
| `sci_papers_per_faculty_original` | 원자료 전임교원 1인당 SCI급 논문 실적 |
| `sci_papers_per_faculty_recalculated` | SCI급 논문 건수 / 전임교원수 |
| `book_count` | 저역서수 |
| `full_time_faculty_count_book` | 저역서 산출용 전임교원수 |
| `books_per_faculty_original` | 원자료 전임교원 1인당 저역서 실적 |
| `books_per_faculty_recalculated` | 저역서수 / 전임교원수 |
| `external_research_funds_thousand_krw` | 교외연구비(천원) |
| `full_time_faculty_count_external_research` | 교외연구비 산출용 전임교원수 |
| `external_research_funds_per_faculty_thousand_krw_original` | 원자료 전임교원 1인당 교외연구비(천원) |
| `external_research_funds_per_faculty_thousand_krw_recalculated` | 교외연구비 / 전임교원수 |
| `research_performance_vs_standard_original` | 원자료 연구성과 기준값 대비 실적 |
| `employment_count` | 2~3주기 취업자 |
| `graduate_count` | 2~3주기 졸업자 |
| `employment_rate_pct_original` | 원자료 졸업생 취업률 |
| `employment_rate_pct_recalculated` | 취업자 / 졸업자 * 100 |
| `career_success_count` | 4주기 취업자+창업자+진학자 수 |
| `career_target_count` | 4주기 취·창업 및 진학대상자 수 |
| `graduate_career_performance_pct_original` | 4주기 원자료 졸업생 진로 성과 |
| `graduate_career_performance_pct_recalculated` | 성과 인원 / 대상자 수 * 100 |

## Long CSV 컬럼

| column | description |
| --- | --- |
| `metric_id` | 표준 지표 ID |
| `metric_label_ko` | 지표 한글명 |
| `reference_year` | 기준연도 |
| `evaluation_cycle` | 평가 주기 |
| `university_name` | 대학명 |
| `founding_type` | 설립구분 |
| `region_name` | 지역 |
| `value` | 기본 분석값. 재계산값이 있으면 재계산값, 없으면 원자료값 |
| `value_original` | 원자료 지표값 |
| `value_recalculated` | 분자/분모 기반 재계산값 |
| `numerator` | 지표 산출 분자 |
| `denominator` | 지표 산출 분모 |
| `unit` | 단위 |
| `source_file_name` | 원본 엑셀 파일명 |

## 지표 ID

| metric_id | label | unit |
| --- | --- | --- |
| `full_time_faculty_rate` | 전임교원 확보율 | `%` |
| `adjunct_faculty_rate` | 겸임교원 확보율 | `%` |
| `faculty_combined_rate` | 전임교원 및 겸임교원 확보율 | `%` |
| `building_facility_rate` | 교사 확보율 | `%` |
| `freshman_fill_rate` | 정원내 신입생 충원율 | `%` |
| `student_fill_rate` | 정원내 재학생 충원율 | `%` |
| `student_recruitment_performance` | 학생 충원 성과 | `%` |
| `education_cost_return_rate` | 교육비 환원율 | `%` |
| `scholarship_ratio` | 장학금 비율 | `%` |
| `tuition_revenue_ratio` | 세입 중 등록금 비율 | `%` |
| `donation_ratio` | 세입 중 기부금 비율 | `%` |
| `corporate_transfer_ratio` | 세입 중 법인전입금 비율 | `%` |
| `legal_burden_rate` | 법정부담금 부담률 | `%` |
| `corporate_finance_transfer_ratio` | 법인 재정규모 대비 법인전입금 비율 | `%` |
| `lecturer_hourly_pay` | 강사 강의료 | `krw_per_hour` |
| `internal_research_per_faculty` | 전임교원 1인당 교내연구비 | `thousand_krw_per_faculty` |
| `students_per_staff` | 직원 1인당 학생수 | `students_per_staff` |
| `dormitory_accommodation_rate` | 기숙사 수용률 | `%` |
| `dormitory_domestic_accommodation_rate` | 기숙사 수용률 II | `%` |
| `library_material_purchase_per_student` | 재학생 1인당 연간 자료구입비 | `krw_per_student` |
| `library_staff_per_1000_students` | 재학생 1,000명당 도서관 직원수 | `staff_per_1000_students` |
| `domestic_papers_per_faculty` | 전임교원 1인당 등재(후보)지 논문 실적 | `papers_per_faculty` |
| `sci_papers_per_faculty` | 전임교원 1인당 SCI급 논문 실적 | `papers_per_faculty` |
| `books_per_faculty` | 전임교원 1인당 저역서 실적 | `books_per_faculty` |
| `external_research_per_faculty` | 전임교원 1인당 교외연구비 | `thousand_krw_per_faculty` |
| `research_performance_vs_standard` | 연구성과 기준값 대비 실적 | `score` |
| `employment_rate` | 졸업생 취업률 | `%` |
| `graduate_career_performance` | 졸업생 진로 성과 | `%` |

## 처리상 주의

- 2015~2017년 재정 관련 원자료는 다수 컬럼이 천원 단위이며, wide CSV의 `*_krw` 컬럼은 원 단위로 환산했다.
- 교내/교외 연구비 컬럼은 원자료와 기존 앱 지표 관례에 맞춰 `thousand_krw` 단위를 유지한다.
- 2025년 4주기 파일은 `법정부담금 부담률`, `법인 재정규모 대비 법인전입금 비율`, `학생 충원 성과`, `졸업생 진로 성과`, `기숙사 수용률 II`가 추가되고, `교사 확보율`, 신입생/재학생 충원율 세부 분자·분모가 빠져 있다.
- 원자료에는 대학 식별코드가 없으므로 같은 학교명의 명칭 변경, 통폐합, 캠퍼스 분리 이슈는 별도 매핑으로 보정해야 한다.
