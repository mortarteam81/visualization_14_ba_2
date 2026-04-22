# library_staff_per_1000_students v5.1 processing guide

## 1. 문서 목적
이 문서는 `재학생 1,000명당 도서관 직원 수` 데이터셋을 원자료(xlsx)에서 시스템용 CSV/XLSX로 가공하는 방법을 기록한다.

이 데이터셋은 연도별로 원자료 헤더 구조가 다르므로, 단순한 일괄 변환이 아니라 **연도 구간별 파싱 규칙**이 필요하다.  
향후 원자료가 업데이트될 때 동일한 방식으로 재현 가능하도록, 확인된 구조 차이와 계산 규칙을 문서화한다.

---

## 2. 데이터셋 개요
- 데이터셋명: 재학생 1,000명당 도서관 직원 수
- 출처: 학술정보통계시스템 (RINFO)
- URL: https://www.rinfo.kr/
- 메뉴 경로: 통계조회 > 통계검색
- 원본 파일 예시: `기본통계_인적자원_20260422112934.xlsx`

---

## 3. 최종 산출 목적
원자료의 복잡한 헤더 구조를 해석하여, 아래 최소 공통 컬럼만 유지하는 시스템용 데이터셋을 생성한다.

최종 유지 컬럼:
- `reference_year`
- `row_no`
- `university_name`
- `school_type`
- `founding_type`
- `region_name`
- `size_group`
- `regular_staff_certified`
- `regular_staff_not_certified`
- `non_regular_staff_certified`
- `non_regular_staff_not_certified`
- `total_staff_certified`
- `total_staff_not_certified`
- `enrolled_students`
- `library_staff_per_1000_students_original`
- `library_staff_per_1000_students_recalculated`
- `library_staff_per_1000_students_recalculated_2025_weighted`
- `student_count_basis`
- `schema_group`
- `source_file_name`

---

## 4. 연도 구간별 구조 차이

### A. 2008~2016
- 시트 크기: 29열
- 구조 특징:
  - 정규직(사서자격증소지자 / 미소지자)
  - 비정규직(사서자격증소지자 / 미소지자)
  - 합계(사서자격증소지자 / 미소지자)
  - 재학생수(당해년도)
  - 재학생 1,000명당 도서관 직원수
- 처리 기준:
  - 필요한 최소 컬럼을 직접 추출
  - `student_count_basis = current_year`
  - `schema_group = legacy_2008_2016`

### B. 2017~2018
- 시트 크기: 29열
- 구조 특징:
  - 2008~2016과 거의 동일
  - 단, 재학생수 열이 `재학생수(전년도)`로 표기됨
- 처리 기준:
  - 필요한 최소 컬럼을 직접 추출
  - `student_count_basis = previous_year`
  - `schema_group = legacy_2017_2018`

### C. 2019~2020
- 시트 크기: 49열
- 구조 특징:
  - 정규직 / 비정규직 / 합계
  - 각 구분 아래 전담 / 겸직
  - 각 전담/겸직 아래:
    - 1급 정사서
    - 2급 정사서
    - 준사서
    - 미소지자
    - 계
- 처리 기준:
  - 최소 컬럼은 직접 존재하지 않으므로 전담/겸직을 합산해 생성
  - `student_count_basis = current_year`
  - `schema_group = modern_2019_2020`

### D. 2021
- 시트 크기: 53열
- 구조 특징:
  - 2019~2020 인력 구조 유지
  - 교육 컬럼이 3개 블록:
    - 대면교육
    - 비대면 실시간 교육
    - 온라인 교육
- 처리 기준:
  - 교육 관련 컬럼은 사용하지 않으므로 무시
  - 필요한 최소 컬럼과 재학생수 / 최종 1,000명당 직원수 열만 추출
  - `schema_group = modern_2021`

### E. 2022~2024
- 시트 크기: 51열
- 구조 특징:
  - 2019~2020 인력 구조 유지
  - 교육 컬럼이 2개 블록:
    - 대면교육
    - 온라인 교육
- 처리 기준:
  - 교육 관련 컬럼은 무시
  - 필요한 최소 컬럼과 재학생수 / 최종 1,000명당 직원수 열만 추출
  - `schema_group = modern_2022_2024`

### F. 2025
- 시트 크기: 51열
- 구조 특징:
  - 2022~2024와 유사
  - 교육 컬럼 라벨이 `대면교육` → `집합교육`으로 변경
  - 재학생 1,000명당 도서관 직원 수 산식 변경
- 처리 기준:
  - 교육 관련 컬럼은 무시
  - 최소 컬럼과 재학생수 / 원자료 최종값 추출
  - 2025 가중치 재계산 컬럼 별도 생성
  - `schema_group = modern_2025`

---

## 5. 최소 컬럼 추출 규칙

### 5-1. 2008~2018 직접 추출 컬럼
원자료에서 직접 읽음:
- `regular_staff_certified`
- `regular_staff_not_certified`
- `non_regular_staff_certified`
- `non_regular_staff_not_certified`
- `total_staff_certified`
- `total_staff_not_certified`
- `enrolled_students`
- `library_staff_per_1000_students_original`

### 5-2. 2019~2025 합산 규칙
2019년 이후에는 전담/겸직 구조를 합산하여 최소 컬럼을 생성한다.

#### 정규직(사서자격증소지자)
```text
regular_staff_certified =
(정규직 전담 1급 정사서 + 2급 정사서 + 준사서)
+ (정규직 겸직 1급 정사서 + 2급 정사서 + 준사서)
정규직(사서자격증미소지자)
regular_staff_not_certified =
정규직 전담 미소지자 + 정규직 겸직 미소지자
비정규직(사서자격증소지자)
non_regular_staff_certified =
(비정규직 전담 1급 정사서 + 2급 정사서 + 준사서)
+ (비정규직 겸직 1급 정사서 + 2급 정사서 + 준사서)
비정규직(사서자격증미소지자)
non_regular_staff_not_certified =
비정규직 전담 미소지자 + 비정규직 겸직 미소지자
합계
total_staff_certified =
regular_staff_certified + non_regular_staff_certified
total_staff_not_certified =
regular_staff_not_certified + non_regular_staff_not_certified
6. 계산 규칙
6-1. 원자료값 보존
library_staff_per_1000_students_original
원자료 마지막 열에 있는 최종 표시값을 그대로 저장
6-2. 일반 재계산

2008~2025 공통:

library_staff_per_1000_students_recalculated =
(
  regular_staff_certified
  + regular_staff_not_certified
  + non_regular_staff_certified
  + non_regular_staff_not_certified
) / enrolled_students * 1000
6-3. 2025 가중치 재계산

2025만 별도 계산:

정규직 사서 = 1.0
비정규직 사서 = 1.0
정규직 비사서 = 0.8
비정규직 비사서 = 0.5
weighted_staff_2025 =
(regular_staff_certified + non_regular_staff_certified) * 1.0
+ regular_staff_not_certified * 0.8
+ non_regular_staff_not_certified * 0.5
library_staff_per_1000_students_recalculated_2025_weighted =
weighted_staff_2025 / enrolled_students * 1000

주의:

2025 이전 연도는 이 컬럼을 계산하지 않음
2025 이전은 null
7. 검증 포인트

원자료 갱신 시 아래 샘플 대학으로 수동 검증한다.

성신여자대학교
2018
2019
2021
2025

검증 항목:

정규직(사서자격증소지자)
정규직(사서자격증미소지자)
비정규직(사서자격증소지자)
비정규직(사서자격증미소지자)
재학생수
원자료 최종값
재계산값
2025 가중치 재계산값

특히 2025는 아래를 별도 확인:

원자료 최종값과 가중치 적용 재계산값의 차이
서비스에서 어느 값을 기본 노출값으로 사용할지 정책 확인
8. 최종 산출물
library_staff_per_1000_students_2008_2025_v5_1_utf8.csv
library_staff_per_1000_students_2008_2025_v5_1.xlsx
library_staff_per_1000_students_v5_1.source.json
library_staff_per_1000_students_v5_1_schema.md
libraryStaffPer1000Columns.ts
libraryStaffPer1000Schema.ts
library_staff_per_1000_students_v5_1.processing_guide.md
9. 원자료 업데이트 시 작업 순서
새 원자료 xlsx 다운로드
연도별 시트 존재 여부 확인
각 연도가 기존 구조 구간 중 어디에 속하는지 확인
기존 구조와 다르면 새로운 구조 구간 추가
최소 컬럼 추출
일반 재계산 수행
2025 이후 산식 변경 여부 확인
필요시 가중치 재계산 컬럼 갱신
샘플 대학 수동 검증
CSV/XLSX 재생성
source.json, schema.md, processing_guide.md 업데이트
10. 운영상 주의사항
이 데이터셋은 연도별 구조가 같지 않으므로, “고정 열 인덱스 하나로 전체 연도 처리”를 금지한다.
교육 관련 컬럼은 현재 시스템 사용 범위에서 제외되어 있으며, 구조 분석용으로만 참고한다.
2017~2018의 재학생수(전년도)는 해석상 차이가 있으므로 반드시 student_count_basis를 유지한다.
2025는 구조뿐 아니라 산식도 달라졌으므로 별도 계산 컬럼을 유지한다.