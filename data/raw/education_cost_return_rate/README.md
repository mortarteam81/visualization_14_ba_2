# 교육비 환원율 원본 데이터

## 출처
- 사이트명: 대학재정알리미
- 운영기관: 한국사학진흥재단
- 메뉴 경로: 통계현황 > 테마이슈통계
- URL: https://uniarlimi.kasfo.or.kr/statistics/themeIssue/view/1

## 데이터셋 설명
이 데이터는 대학재정알리미에서 제공하는 교육비 환원율 관련 연도별 원본 엑셀 파일을 수집한 것이다.
본 저장소에서는 원본 파일을 보존하고, 이를 가공하여 서비스/분석용 CSV 파일로 변환하여 사용한다.

## 수집 방식
- 수집 방식: 웹사이트에서 연도별 엑셀 파일 수동 다운로드
- 수집일: 2026-04-21

## 원본 파일 목록
- 2020년_교육여건_교육비+환원율.xlsx
- 2021년_교육여건_교육비+환원율.xlsx
- 2022년_교육여건_교육비+환원율.xlsx
- 2023년_교육여건_교육비+환원율.xlsx
- 2024년_교육여건_교육비+환원율.xlsx
- 2025년_교육여건_교육비+환원율.xlsx

## 가공 결과물
- `data/processed/education_cost_return_rate/education_cost_return_rate_2020_2025_v2_schema_utf8.csv`

## 가공 개요
1. 병합셀 헤더를 논리적으로 해제
2. 상위 헤더와 하위 헤더를 결합하여 단일 컬럼명 생성
3. 연도별 파일을 하나의 테이블로 통합
4. GitHub repo에서 바로 쓰기 좋은 v2 표준 스키마로 변환
5. UTF-8 CSV 파일로 저장

## v2 표준 스키마 주요 컬럼
- `survey_year`
- `university_name`
- `school_level`
- `school_type`
- `region`
- `row_no`
- `tuition_salary`
- `tuition_admin`
- `tuition_research_student`
- `tuition_books`
- `tuition_equipment`
- `tuition_scholarship`
- `tuition_admissions`
- `tuition_account_total`
- `industry_project_cost`
- `industry_support_project_cost`
- `industry_indirect_project_cost`
- `industry_general_admin`
- `industry_equipment`
- `industry_account_total`
- `tuition_revenue`
- `education_cost_return_rate_original_pct`
- `education_cost_return_rate_recalculated_pct`
- `source_file_name`

## 주의사항
- 연도별 원본 엑셀은 헤더 구조와 세부 항목 명칭이 일부 다를 수 있다.
- 본 저장소의 가공 데이터는 이를 공통 스키마로 정규화한 결과이다.
- 시각화 및 계산 로직에서는 `education_cost_return_rate_recalculated_pct`를 우선 기준값으로 사용하는 것을 권장한다.
