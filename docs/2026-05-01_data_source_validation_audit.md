# 2026-05-01 데이터 소스 검증 감사 보고서

대상 프로젝트: 4주기 대학기관평가인증 정량지표 시각화 대시보드

작업 방식: 내부 isolated sub-agent 5개 병렬 read-only 감사 결과를 통합함. 원본 데이터/코드 수정은 수행하지 않음.

## 1. 감사 대상 소스군

| 소스군 | 주요 파일/경로 | 검증 상태 | 요약 판단 |
|---|---|---:|---|
| KCUE/한국대학평가원 대학현황지표 | `data/processed/kcue_university_indicators/*`, `data/raw/kcue_university_indicators/original/*.xlsx` | 높음 | 원자료 11개 XLSX, processed wide/long, 산식 재계산이 대체로 일치함. |
| 대학알리미 원자료/가공자료 | `data/processed/dormitory_accommodation_status`, `data/processed/lecturer_pay`, `data/processed/student_recruitment`, `data/raw/pending_manual/academyinfo` | 중간~부분 | `student_recruitment` 원자료 매핑은 양호하나 metadata 부재 및 재학생충원율 공백 문제 있음. 기숙사/강사료는 원본 XLSX 부재로 부분검증. |
| 사학재정알리미/KASFO | `data/processed/education_cost_return_rate`, `data/결산(22,23,24).csv`, `data/법정부담금_부담율.csv`, `data/raw/pending_manual/finance` | 중간~부분 | 교육비 환원율/법정부담금 산식은 재현됨. 결산 데이터는 활용 가능하나 metadata와 전처리 보강 필요. |
| RINFO 학술정보통계 | `library_staff_per_1000_students`, `library_material_purchase_per_student` | 중간~부분 | 산식 재현 가능. 원본 xls/xlsx 부재로 원자료 대조 제한. 자료구입비 세부 컬럼 매핑 의심. |
| legacy CSV/학교명 매칭 | `data/*.csv`, `data/metadata/datasets/*.metadata.json`, analysis scope | 중간 | 비교대학 11개는 대부분 매칭되지만 공백, 구명칭, 캠퍼스/분교, 샘플 파일 혼재 처리가 필요. |

## 2. 비교대학 기준

기준 파일: `.streamlit/comparison_profile.local.json`

- 기준대학: 성신여자대학교
- 비교군 1: 숙명여자대학교, 덕성여자대학교, 서울여자대학교, 동덕여자대학교, 이화여자대학교
- 비교군 2: 한성대학교, 서경대학교, 광운대학교, 세종대학교, 숭실대학교

검증 결과, 위 11개 학교는 주요 processed/legacy 데이터에서 대부분 정상 매칭됨. 단, 일부 샘플 파일은 성신여자대학교만 포함하므로 운영 데이터에서 제외해야 함.

## 3. 소스별 상세 결과

### 3.1 KCUE/한국대학평가원 대학현황지표

주요 근거:

- `data/processed/kcue_university_indicators/kcue_university_indicators_2015_2025_v1_utf8.csv`
- `data/processed/kcue_university_indicators/kcue_university_metric_values_2015_2025_v1_utf8.csv`
- `data/metadata/kcue_university_indicators_v1.source.json`
- `data/metadata/kcue_university_indicators_v1.processing_report.json`
- `data/raw/kcue_university_indicators/original/*.xlsx`

검증 결과:

- 원자료 11개 XLSX와 metadata의 `original_files`가 일치함.
- processed wide CSV 2,054행, long CSV 43,184행이 processing report와 일치함.
- 2015~2025 전체 연도에서 raw XLSX와 processed CSV 간 학교명 누락/추가 없음.
- 주요 컬럼 매핑 및 2015~2017 `천원 → 원` 환산 정상.
- 분자/분모가 있는 long table 40,136개 row의 산식 재계산 mismatch 없음.

부분검증/주의:

- 다음 지표는 분자/분모가 없어 원자료값만 검증 가능함.
  - `research_performance_vs_standard`
  - 2025년 `adjunct_faculty_rate`
  - 2025년 `faculty_combined_rate`
  - 2025년 `student_recruitment_performance`
  - 2025년 `full_time_faculty_rate`
- UI/metadata에 “원자료값 사용, 재계산 불가” 표시 권장.
- 일부 outlier는 처리 오류가 아니라 원자료 특성/분모효과로 판단됨.

판정: **검증 신뢰도 높음**

### 3.2 대학알리미 계열

주요 근거:

- `data/processed/dormitory_accommodation_status/dormitory_accommodation_status_v2_utf8.csv`
- `data/processed/lecturer_pay/lecturer_pay_2023_2025_v2_1_utf8.csv`
- `data/processed/student_recruitment/student_recruitment_2026_candidate.csv`
- `data/raw/pending_manual/academyinfo/*.xlsx`
- `data/raw/pending_manual/manifest.csv`

검증 결과:

- `student_recruitment`는 원자료 3개 파일 매핑이 명확함.
  - `academyinfo_2025_27_freshman_fill_school.xlsx`
  - `academyinfo_2025_29_student_fill_school.xlsx`
  - `academyinfo_2025_31_enrolled_students_school.xlsx`
- 비교대학 11개는 대학알리미 계열 processed 3종에서 모두 매칭됨.
- `student_recruitment`의 각 비교대학은 `본교`, `서울`, `사립`, `대학교`로 확인됨.

문제/주의:

- `student_recruitment_2026_candidate.csv`의 `재학생충원율` 컬럼이 전부 공백임.
  - 원자료 `academyinfo_2025_29_student_fill_school.xlsx`에는 재학생충원율 값이 존재함.
  - 현재 후보 파일은 신입생 충원율 중심 미완성 파일일 가능성이 큼.
- `student_recruitment` source/dataset metadata 부재.
- `dormitory`, `lecturer_pay`는 processed와 metadata는 있으나 실제 원본 XLSX가 repo에 없어 원본 대조 제한.
- `lecturer_pay`는 학교별 다중 행 구조이므로 평균/대표값 산식 없이 바로 시각화하면 중복 집계 위험.

판정: **부분검증, metadata 보강 필요**

### 3.3 사학재정알리미/KASFO 계열

주요 근거:

- `data/processed/education_cost_return_rate/education_cost_return_rate_2020_2025_v2_schema_utf8.csv`
- `data/결산(22,23,24).csv`
- `data/법정부담금_부담율.csv`
- 루트 `14-ba-2.-beobjeongbudamgeum-...csv`
- `data/raw/pending_manual/finance/*`

검증 결과:

- 교육비 환원율 산식 재현 가능.
  - `(tuition_account_total + industry_account_total) / tuition_revenue * 100`
  - 소수 1자리 반올림 기준 전 행 산식 일치.
- 법정부담금 산식 재현 가능.
  - `법정부담금부담액 / 법정부담금기준액 * 100`
  - 루트 원본성 CSV와 `data/법정부담금_부담율.csv`는 실질 내용 동일.
- 비교대학 11개는 교육비 환원율, 법정부담금, 결산, KCUE 법인전입금 비율에서 누락 없음.

문제/주의:

- 교육비 환원율 원본 XLSX가 없어 원자료 대조 제한.
- `data/결산(22,23,24).csv`는 source/schema/report 부재.
- 결산 데이터는 `법인`/`교비` 회계 혼재. 학교 지표 산출 시 `회계=교비` 필터 필수.
- 학교명/법인명/회계 값에 앞뒤 공백이 많아 `strip()` 필수.
- 금액은 쉼표 문자열과 `-` 표현이 혼재하므로 숫자 변환 규칙 필요.
- 법정부담금 CSV는 학교코드 leading zero가 소실된 복사본이 있음.
- 공시연도와 기준년도가 1년 차이남. 예: 공시연도 2025 = 기준년도 2024.

판정: **산식 검증 가능, 원자료/metadata 보강 필요**

### 3.4 RINFO 학술정보통계 계열

주요 근거:

- `data/processed/library_staff_per_1000_students/library_staff_per_1000_students_2008_2025_v6_utf8.csv`
- `data/processed/library_material_purchase_per_student/library_material_purchase_per_student_2008_2025_v2_utf8.csv`
- `data/metadata/library_staff_per_1000_students_v6_schema.md`
- `data/metadata/library_staff_per_1000_students_v6.processing_guide.md`
- `data/metadata/library_material_purchase_per_student_v2_schema.md`

검증 결과:

- 도서관 직원 수: 2008~2025, 8,215행, 중복 키 없음.
- 자료구입비: 2008~2025, 8,226행, 중복 키 없음.
- 도서관 직원 수 산식 재현 가능.
  - `가중직원수 / 재학생수 * 1000`
- 자료구입비 산식 재현 가능.
  - `자료구입비계 / 재학생수`
- 서울 사립 4년제 scope 34개 학교는 두 processed CSV에 exact match로 존재.

문제/주의:

- 원본 RINFO xls/xlsx 파일이 repo에 없어 원자료 대조 제한.
- 도서관 직원 수에서 `enrolled_students = 0`인데 직원 수가 있어 `inf`가 발생한 행이 있음.
- 자료구입비에서 `other_electronic_resources_expense`가 전 행에서 `total_material_purchase_expense`와 동일함.
  - 세부 컬럼 매핑 오류 가능성이 큼.
- RINFO 로딩 파이프라인이 scope 파일을 직접 쓰지 않고 `서울/사립/대학` 필터만 적용하면 34개가 아니라 42개 학교가 포함될 위험이 있음.
  - 예: 고려사이버대학교, 서울사이버대학교, 숭실사이버대학교 등.

판정: **산식 검증 가능, 원본 대조/세부 컬럼/scope 필터 보강 필요**

### 3.5 legacy CSV 및 학교명 전처리

주요 근거:

- `data/전임교원_확보율.csv`
- `data/전임교원 확보율.csv`
- `data/전임교원_논문실적.csv`
- `data/전임교원 논문실적.csv`
- `data/연구비_수혜실적.csv`
- `data/연구비 수혜 실적.csv`
- `data/졸업생_취업률.csv`
- `data/법정부담금_부담율.csv`
- `data/결산(22,23,24).csv`
- `data/metadata/analysis_scopes/seoul_private_four_year_universities.json`

검증 결과:

- 비교대학 11개는 주요 legacy CSV에서 대부분 exact match됨.
- `data/결산(22,23,24).csv`는 trim 후 exact match됨.
- `data/전임교원_논문실적.csv`, `data/전임교원 논문실적(샘플).csv`는 성신여자대학교만 포함하므로 샘플/테스트 파일로 분리 필요.

전처리 필요 사례:

- 선행/후행 공백: `data/결산(22,23,24).csv`
- 구 명칭/괄호명:
  - `강서대학교(구.케이씨대학교)`
  - `서울한영대학교(구.한영신학대학교)`
- 과거 학교명:
  - `그리스도대학교`, `케이씨대학교`, `한영신학대학교`
- 캠퍼스/분교:
  - `본교`, `분교`, `제2캠퍼스`, `제3캠퍼스`
- 캠퍼스가 학교명에 포함된 사례:
  - `건국대학교(글로컬)`
  - `고려대학교(세종)`
  - `동국대학교(WISE)`
  - `연세대학교(미래)`
  - `한양대학교(ERICA)`
- 학교명+캠퍼스 접미 혼합:
  - `건국대학교(글로컬)_분교`
  - `영산대학교(양산)_제2캠퍼스`
  - `가톨릭대학교_제2캠퍼스`

판정: **학교명 정규화 체계 필수**

## 4. 공통 리스크

### 4.1 학교명 단순 join 위험

단순 `학교명` join은 위험함. 최소한 다음 조합을 우선해야 함.

1. `school_id` 또는 `학교코드`
2. `rep_school_id` 또는 `대표학교코드`
3. 정규화 학교명
4. 캠퍼스/본분교명
5. 분석 scope 포함 여부

특히 다음 본교/분교 쌍은 절대 괄호 제거만으로 합치면 안 됨.

- 건국대학교 vs 건국대학교(글로컬)
- 고려대학교 vs 고려대학교(세종)
- 동국대학교 vs 동국대학교(WISE)
- 연세대학교 vs 연세대학교(미래)
- 한양대학교 vs 한양대학교(ERICA)

### 4.2 scope 필터 불일치

`data/metadata/analysis_scopes/seoul_private_four_year_universities.json`에는 서울 사립 4년제 본교 34개가 정의되어 있음.

하지만 일부 loader/page는 이 scope 파일을 직접 쓰지 않고 `지역=서울`, `설립=사립`, `학교유형=대학` 같은 조건만 사용함. 이 경우 사이버대/특수 케이스/캠퍼스가 포함될 수 있음.

따라서 모든 지표는 최종적으로 동일한 scope manifest를 기준으로 필터링해야 함.

### 4.3 원본 파일 부재

다음 계열은 processed 산식은 검증 가능하지만 원본 파일이 repo에 없어 원자료 대조가 제한됨.

- 기숙사 수용 현황
- 강사 강의료
- 교육비 환원율
- RINFO 도서관 직원 수
- RINFO 자료구입비

최소한 원본 파일명, 다운로드일, checksum, source URL, 수동 가공 절차를 metadata/report로 남겨야 함.

### 4.4 metadata 공백

다음 항목은 source/schema/report 보강 우선순위가 높음.

- `student_recruitment`
- `budam`
- `gyeolsan`
- RINFO processing report
- 대학알리미 기숙사/강사료 원본 checksum/report

## 5. 수정 우선순위

### P0. 학교명/학교코드 정규화 체계 구축

목표:

- 모든 데이터셋에서 비교대학 11개와 서울 사립 4년제 본교 34개를 안정적으로 매칭.

구현 권고:

- `data/metadata/school_aliases.csv` 또는 JSON 추가.
- 필드 예시:
  - `canonical_school_name`
  - `alias`
  - `rep_school_id`
  - `school_id`
  - `valid_from_year`
  - `valid_to_year`
  - `match_type`
  - `scope_policy`
- 정규화 함수 추가:
  - `strip()`
  - 연속 공백 축약
  - `(구.XXX)` 제거 후보 생성
  - `_분교`, `_제2캠퍼스`, ` 세종캠퍼스` 등 campus suffix 분리
  - 학교코드 zero-padding
  - exact match 우선, alias는 exact miss일 때만 적용

주의:

- 괄호 안 캠퍼스명은 무조건 제거하지 말 것.
- `건국대학교(글로컬)` 등은 본교와 별도 엔티티로 유지.

### P1. scope 필터 통일

목표:

- 모든 시각화 페이지/loader에서 `seoul_private_four_year_universities.json` 기준 34개 본교 scope 사용.

대상:

- RINFO 계열 loader/page
- 교육비 환원율
- 결산 기반 지표
- legacy CSV loader
- 신규 student_recruitment loader

### P2. metadata/report 보강

목표:

- 각 지표가 어떤 원자료에서 어떤 산식으로 만들어졌는지 추적 가능하게 함.

우선 대상:

- `data/metadata/student_recruitment.source.json`
- `data/metadata/datasets/student_recruitment.metadata.json`
- `data/metadata/datasets/budam.metadata.json` 보강
- `data/metadata/datasets/gyeolsan.metadata.json` 보강
- RINFO 두 데이터셋 processing report 추가

### P3. 지표별 데이터 품질 이슈 수정

- `student_recruitment_2026_candidate.csv`
  - 재학생충원율 공백 원인 확인.
  - 원자료 29번 파일 값을 반영하거나 “신입생 충원율 후보”로 명확히 표기.
- `library_staff_per_1000_students`
  - 재학생수 0일 때 `inf` 대신 `null`/산출불가 처리.
- `library_material_purchase_per_student`
  - `other_electronic_resources_expense` 매핑 재검증.
- `lecturer_pay`
  - 학교별 다중 행을 대표값/평균/구분별 표시 중 어떤 방식으로 시각화할지 명시.
- `data/결산(22,23,24).csv`
  - 공백 제거, 회계 필터, 숫자 변환 규칙 일원화.

### P4. QA 리포트/테스트 추가

추가 권장 테스트:

- 비교대학 11개가 모든 current asset에서 최소 1건 이상 매칭되는지.
- 서울 사립 4년제 scope가 모든 지표에서 동일하게 34개로 유지되는지.
- 샘플 파일이 운영 데이터셋으로 사용되지 않는지.
- `강서대학교`, `케이씨대학교`, `강서대학교(구.케이씨대학교)`가 동일 canonical로 정규화되는지.
- `서울한영대학교`, `한영신학대학교`, `서울한영대학교(구.한영신학대학교)`가 동일 canonical로 정규화되는지.
- `건국대학교`와 `건국대학교(글로컬)`이 섞이지 않는지.
- `data/결산(22,23,24).csv`의 공백 포함 학교명이 trim 후 매칭되는지.
- 분모 0/결측 지표가 `inf`로 UI에 노출되지 않는지.

## 6. 실행 제안

다음 구현 순서는 아래가 안전함.

1. 학교명 정규화/alias 유틸과 테스트 추가.
2. scope manifest 기반 필터 공통 함수 추가.
3. RINFO/결산/교육비 환원율/legacy loader에 공통 scope 필터 적용.
4. `student_recruitment` metadata 추가 및 재학생충원율 공백 검토.
5. RINFO `inf` 처리 및 자료구입비 세부 컬럼 매핑 재검증.
6. source/report metadata 보강.
7. 최종 QA 테스트 실행.

## 7. 결론

현재 대시보드 데이터는 핵심 비교대학 11개 기준으로는 대체로 매칭 가능하며, KCUE 계열은 신뢰도가 높다. 그러나 전체 대시보드 품질을 안정화하려면 학교명 정규화, scope 필터 통일, legacy/source metadata 보강이 선행되어야 한다.

특히 가장 먼저 처리해야 할 것은 다음 세 가지다.

1. 학교명/학교코드 정규화 체계 구축
2. 모든 지표의 서울 사립 4년제 본교 34개 scope 필터 통일
3. `student_recruitment`, `budam`, `gyeolsan`, RINFO 계열 metadata/report 보강
