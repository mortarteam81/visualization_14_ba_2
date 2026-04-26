# student_recruitment 다음 구현 메모

## 결정

- 다음 지표 확장 1순위는 `student_recruitment`로 둔다.
- 단일 합성값이 아니라 `신입생 충원율`, `재학생 충원율` 2개 series로 구현한다.
- 이번 신뢰성 보강 사이클에서는 계산 지표로 등록하지 않는다.

## 확보 원자료

- `data/raw/pending_manual/academyinfo/academyinfo_2025_27_freshman_fill_school.xlsx`
  - 대학알리미 `4-다. 신입생 충원 현황`
  - 확인 컬럼: 입학정원, 모집인원, 지원자, 입학자, 정원내 신입생 충원율
- `data/raw/pending_manual/academyinfo/academyinfo_2025_29_student_fill_school.xlsx`
  - 대학알리미 `4-라-1. 재학생 충원율`
  - 확인 컬럼: 학생정원, 학생모집정지인원, 재학생, 재학생충원율, 정원내 재학생 충원율
- `data/raw/pending_manual/academyinfo_trend_samples/academyinfo_trend_student_fill_rate_CMN81_015.xlsx`
  - 재학생 충원율 다년치 후보

## 산식/출력 후보

- `freshman_fill_rate`
  - label: `신입생 충원율`
  - column: `신입생충원율`
  - unit: `%`
  - 기본은 원자료 직접값 사용, 필요 시 `입학자 수 / 모집인원 * 100` 검산
- `student_fill_rate`
  - label: `재학생 충원율`
  - column: `재학생충원율`
  - unit: `%`
  - 기본은 원자료 직접값 사용, 필요 시 `재학생 수 / 편제정원 * 100` 검산

## 다음 구현 체크리스트

- raw schema registry에 2025 학교별 XLSX 또는 변환 CSV 스키마를 등록한다.
- `utils.data_pipeline`에 학생 충원 loader/prepare 함수를 추가한다.
- `registry.metadata`에서 `student_recruitment`를 구현 완료로 승격한다.
- 경영 인사이트 대시보드 `ANALYSIS_LOADERS`에 두 series를 추가한다.
- 개별 페이지를 만들지 여부는 대시보드 반영 후 결정한다.
- 계약 테스트와 단위 테스트에서 원자료 컬럼, 낮음/높음 방향, 대시보드 포함 여부를 검증한다.
