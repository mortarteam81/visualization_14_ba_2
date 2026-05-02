# 2026-05-01 원자료 자동변환 시스템 구축계획서

대상 프로젝트: 4주기 대학기관평가인증 정량지표 시각화 대시보드

대상 경로: `/Users/mortarteam81/Documents/Codex/2026-04-25/users-mortarteam81-visualization-14-ba-2/visualization_14_ba_2`

작성 목적: 대학알리미, 사학재정알리미/KASFO, 한국대학평가원/KCUE, RINFO, legacy CSV 원자료를 시스템에서 사용할 수 있는 표준 DB/CSV/metadata 형식으로 자동 변환하는 파이프라인 구축 계획을 정의한다.

작성 기준:

- `docs/2026-05-01_data_source_validation_audit.md`
- `docs/2026-05-01_source_db_consistency_audit.md`
- gstack `plan-eng-review` 관점: architecture, data flow, edge cases, test coverage, rollout safety 중심

---

## 1. 배경과 문제 정의

현재 대시보드는 여러 출처의 원자료를 수동 편집·가공한 CSV/processed DB를 사용한다. 일부 데이터는 원자료와 일치성이 높지만, 일부는 metadata/원본 보존/전처리/산식 검증이 부족하다.

감사 결과 확인된 핵심 문제는 다음과 같다.

1. 원자료 파일 구조가 출처별로 다름.
   - 대학알리미: XLSX/ZIP, 다중 헤더, 공시연도/기준연도 혼재
   - KASFO: XLSX/ZIP, 회계 구분, 금액 문자열, 음수/결측 표현 혼재
   - KCUE: 연도별 XLSX, 주기별 컬럼 구조 변화
   - RINFO: XLS/XLSX, 병합셀/연도별 컬럼 구조 변화
   - legacy CSV: CP949/UTF-8 혼재, 학교코드 leading zero 소실

2. 학교 식별 체계가 불안정함.
   - 학교명 단독 join은 위험
   - `건국대학교` vs `건국대학교(글로컬)` 등 캠퍼스 오염 가능
   - `강서대학교/케이씨대학교/그리스도대학교` 등 구명칭 alias 필요
   - legacy 파일은 `0000136`이 `136`으로 저장되는 경우 존재

3. 일부 processed DB는 원자료와 완전히 일치하지 않음.
   - `student_recruitment_2026_candidate.csv`의 `재학생충원율` 전 행 공백
   - KASFO 결산 2022년 `기타국고지원[1514]` 누락 가능
   - 음수 이월자금 부호 차이
   - RINFO 자료구입비 세부 컬럼 매핑 의심
   - `inf` 값 발생

4. metadata/report가 부족함.
   - source metadata, schema, processing report, checksum 미비
   - 일부 원본 XLSX가 repo에 없음
   - SQLite `metric_values`는 0행이라 운영 DB로 보기 어려움

따라서 원자료를 일관된 규칙으로 자동 변환하고, 변환 결과를 자동 검증하는 시스템이 필요하다.

---

## 2. 목표

### 2.1 최종 목표

원자료 파일을 지정 위치에 넣으면 시스템이 자동으로 다음을 수행한다.

1. 원자료 인식
2. 원자료 파싱
3. 학교명/학교코드 정규화
4. 표준 raw schema 변환
5. 지표별 processed schema 변환
6. 산식 재계산 및 원자료값 대조
7. scope 필터 적용
8. metadata/report/checksum 생성
9. QA 테스트 실행
10. 대시보드 loader가 사용할 current asset 생성

### 2.2 성공 기준

- 원자료 → processed 변환이 재현 가능해야 한다.
- 동일 원자료로 변환하면 같은 output이 생성되어야 한다.
- 변환 과정의 row count, school count, year count가 보고서에 남아야 한다.
- 비교대학 11개와 서울 사립 4년제 본교 34개 scope가 모든 relevant 지표에서 검증되어야 한다.
- 학교명 부분검색/괄호 제거로 인한 캠퍼스 오염이 없어야 한다.
- 산식 mismatch, 분모 0, `inf`, 결측은 자동으로 severity가 부여되어야 한다.
- 원자료 파일명, 공식 URL, checksum, 다운로드일, 처리 스크립트 버전이 metadata에 남아야 한다.

---

## 3. 비범위

1. 공식 사이트 대량 자동 크롤링은 1차 범위에서 제외한다.
   - 공개 페이지 확인은 가능하지만, 자동 대량 다운로드는 별도 승인 후 진행한다.
2. 로그인/인증이 필요한 데이터 접근은 제외한다.
3. 원자료 자체의 공식성 보증은 하지 않는다.
   - 시스템은 “보관된 raw 파일과 processed 결과의 일치성”을 보증한다.
4. 전체 지표 동시 변환은 1차 범위에서 제외한다.
   - 파일럿 지표부터 시작해 확장한다.

---

## 4. 전체 아키텍처

```text
                 ┌──────────────────────────────┐
                 │ official/public source sites │
                 │ academyinfo / kasfo / kcue   │
                 │ rinfo / legacy csv           │
                 └──────────────┬───────────────┘
                                │ manual/public download
                                ▼
┌────────────────────────────────────────────────────────┐
│ data/raw/                                              │
│  academyinfo/                                          │
│  kasfo/                                                │
│  kcue/                                                 │
│  rinfo/                                                │
│  legacy/                                               │
└──────────────┬─────────────────────────────────────────┘
               │ raw inventory + checksum
               ▼
┌────────────────────────────────────────────────────────┐
│ source inventory layer                                 │
│ - source_manifest.json/csv                             │
│ - checksum                                             │
│ - source url                                           │
│ - downloaded_at                                        │
│ - raw file profile                                     │
└──────────────┬─────────────────────────────────────────┘
               │
               ▼
┌────────────────────────────────────────────────────────┐
│ converter layer                                        │
│ - academyinfo converters                               │
│ - kasfo converters                                     │
│ - kcue converters                                      │
│ - rinfo converters                                     │
│ - legacy converters                                    │
└──────────────┬─────────────────────────────────────────┘
               │ standardize
               ▼
┌────────────────────────────────────────────────────────┐
│ normalization layer                                    │
│ - school_id / rep_school_id zfill                      │
│ - exact school name                                    │
│ - explicit alias                                       │
│ - campus-aware mapping                                 │
│ - default 34-school scope                              │
└──────────────┬─────────────────────────────────────────┘
               │
               ▼
┌────────────────────────────────────────────────────────┐
│ processed asset layer                                  │
│ - data/processed/<dataset>/*.csv                       │
│ - optional SQLite metric tables                        │
│ - current asset manifest                               │
└──────────────┬─────────────────────────────────────────┘
               │ validate
               ▼
┌────────────────────────────────────────────────────────┐
│ validation/report layer                                │
│ - metadata/*.source.json                               │
│ - metadata/datasets/*.metadata.json                    │
│ - processing_report.json                               │
│ - mismatch report                                      │
│ - pytest contract tests                                │
└────────────────────────────────────────────────────────┘
```

---

## 5. 제안 디렉터리 구조

```text
data/
  raw/
    academyinfo/
      student_recruitment/
      dormitory/
      lecturer_pay/
    kasfo/
      settlement/
      education_return/
      legal_burden/
    kcue/
      university_indicators/
    rinfo/
      library_staff/
      material_purchase/
    legacy/
  processed/
  metadata/
    source_inventory/
    datasets/
    analysis_scopes/
    school_aliases.csv
  validation/
    mismatch_reports/
    processing_reports/

scripts/
  converters/
    academyinfo_student_recruitment.py
    academyinfo_dormitory.py
    academyinfo_lecturer_pay.py
    kasfo_settlement.py
    kasfo_education_return.py
    kasfo_legal_burden.py
    kcue_university_indicators.py
    rinfo_library_staff.py
    rinfo_material_purchase.py
    legacy_csv_standardizer.py
  validate_sources.py
  build_current_assets.py

utils/
  school_normalization.py
  source_inventory.py
  file_fingerprint.py
  formula_registry.py
  validation_report.py
  table_profile.py

tests/
  contracts/
    test_raw_to_processed_consistency.py
    test_scope_consistency.py
    test_school_normalization_contracts.py
    test_source_metadata_contracts.py
  unit/
    test_school_normalization.py
    test_formula_registry.py
    test_file_fingerprint.py
```

---

## 6. 핵심 컴포넌트 설계

## 6.1 Source Inventory Layer

역할:

- raw 파일을 하나의 inventory로 관리한다.
- 파일명, 공식 URL, 다운로드일, checksum, 파일 크기, row/column profile을 저장한다.

예상 산출물:

```json
{
  "source_id": "academyinfo_student_recruitment_2025_29",
  "source_name": "대학알리미 4-라-1 재학생 충원율",
  "source_url": "https://academyinfo.go.kr/main/main0830/main0830.do",
  "local_path": "data/raw/academyinfo/student_recruitment/academyinfo_2025_29_student_fill_school.xlsx",
  "format": "xlsx",
  "downloaded_at": "2026-04-xx",
  "checksum_sha256": "...",
  "encoding": null,
  "sheet_names": ["..."],
  "row_count": 489,
  "status": "acquired"
}
```

필수 기능:

- `sha256` 생성
- xlsx sheet 목록 추출
- csv encoding 감지
- row/column count 추출
- inventory와 실제 파일 존재 여부 검증

---

## 6.2 School Normalization Layer

가장 먼저 구축해야 하는 핵심 모듈이다.

역할:

- 학교명, 학교코드, 대표학교코드, 본분교/캠퍼스를 표준화한다.
- exact match를 우선하고, explicit alias는 exact miss일 때만 적용한다.
- 부분검색과 무조건 괄호 제거를 금지한다.

주요 규칙:

1. 학교코드/대표학교코드는 문자열 7자리.
   - `136` → `0000136`
2. 학교명은 trim과 연속 공백 축약만 기본 적용.
3. 괄호 안 캠퍼스명은 보존.
   - `건국대학교(글로컬)`을 `건국대학교`로 병합 금지.
4. old-name alias는 명시 테이블만 허용.
5. campus suffix는 별도 `campus_label`로 분리하되, 본교 canonical로 자동 병합하지 않는다.

alias table 초기값:

| canonical_school_name | alias | match_type | policy |
|---|---|---|---|
| 강서대학교 | 그리스도대학교 | old_name | canonical_alias |
| 강서대학교 | 케이씨대학교 | old_name | canonical_alias |
| 강서대학교 | 강서대학교(구.케이씨대학교) | old_name_parentheses | canonical_alias |
| 서울한영대학교 | 한영신학대학교 | old_name | canonical_alias |
| 서울한영대학교 | 서울한영대학교(구.한영신학대학교) | old_name_parentheses | canonical_alias |
| 서울한영대학교 | 한영대학교 | short_or_legacy | review_required |
| 서울한영대학교 | 한영대학 | short_or_legacy | review_required |

병합 금지 목록:

- 건국대학교(글로컬)
- 고려대학교(세종)
- 동국대학교(WISE)
- 연세대학교(미래)
- 한양대학교(ERICA)
- 대전가톨릭대학교
- 대구가톨릭대학교
- 부산가톨릭대학교
- 수원가톨릭대학교

---

## 6.3 Converter Layer

각 converter는 다음 공통 interface를 따른다.

```python
class ConversionResult:
    dataset_id: str
    source_files: list[str]
    raw_rows: int
    processed_rows: int
    output_files: list[str]
    metadata_files: list[str]
    warnings: list[str]
    mismatches: list[dict]

class BaseConverter:
    dataset_id: str
    def inspect(self) -> SourceProfile: ...
    def parse_raw(self) -> pd.DataFrame: ...
    def normalize(self, df: pd.DataFrame) -> pd.DataFrame: ...
    def build_processed(self, df: pd.DataFrame) -> pd.DataFrame: ...
    def validate(self, raw: pd.DataFrame, processed: pd.DataFrame) -> ValidationReport: ...
    def write_outputs(self, processed: pd.DataFrame, report: ValidationReport) -> ConversionResult: ...
```

공통 원칙:

- raw 파일은 수정하지 않는다.
- processed output은 deterministic 해야 한다.
- 기존 current asset은 바로 덮어쓰지 않고 candidate로 생성한다.
- 검증 통과 후 current asset 승격한다.

출력 파일 예시:

```text
data/processed/student_recruitment/student_recruitment_2026_candidate_v2.csv
data/metadata/student_recruitment.source.json
data/metadata/datasets/student_recruitment.metadata.json
data/validation/processing_reports/student_recruitment_2026_v2.processing_report.json
data/validation/mismatch_reports/student_recruitment_2026_v2.mismatch.csv
```

---

## 6.4 Formula Registry

역할:

- 지표별 산식을 코드와 metadata에서 동일하게 관리한다.
- 원자료값, 재계산값, 최종 표시값을 분리한다.

예시:

```python
FORMULAS = {
    "student_fill_rate": {
        "label": "재학생충원율",
        "numerator": "enrolled_students_within_quota",
        "denominator": "adjusted_student_quota",
        "formula": "numerator / denominator * 100",
        "unit": "%",
        "round": 1,
        "zero_denominator": "null"
    },
    "dormitory_accommodation_rate": {
        "formula": "dormitory_capacity / enrolled_students * 100",
        "unit": "%",
        "round": 1,
        "zero_denominator": "null"
    }
}
```

필수 규칙:

- 분모 0이면 `inf` 금지.
- `null` 또는 산출불가 flag 사용.
- 원자료값이 있고 분자/분모가 없으면 `source_value_only`로 표기.

---

## 6.5 Validation/Report Layer

자동 생성할 report:

1. source metadata
2. dataset metadata
3. schema file
4. processing report
5. mismatch report
6. QA summary markdown

processing report 필수 항목:

```json
{
  "dataset_id": "student_recruitment",
  "version": "v2",
  "processed_at": "2026-05-xx",
  "source_files": [...],
  "row_counts": {
    "raw": 489,
    "processed": 489
  },
  "year_counts": {...},
  "school_counts": {...},
  "scope_counts": {
    "seoul_private_four_year_main": 34,
    "comparison_11": 11
  },
  "formula_checks": [...],
  "mismatch_summary": {
    "blocker": 0,
    "high": 0,
    "medium": 0,
    "low": 0
  },
  "known_limitations": [...]
}
```

---

## 7. 서브에이전트 활용 계획

이번 구축은 병렬 작업이 효과적이다. 단, 최종 통합 권한은 main이 가진다.

## 7.1 에이전트 역할

### Agent A. Architecture/Contract Agent

목표:

- 전체 converter interface 설계
- source inventory schema 설계
- metadata/report 표준 설계
- current asset 승격 규칙 설계

산출물:

- `docs/conversion_system_architecture.md`
- converter base class 초안
- processing report schema 초안
- severity 기준 문서

검토 기준:

- 모듈 경계가 명확한가
- 기존 loader와 충돌하지 않는가
- candidate → verified → current 승격 흐름이 안전한가

---

### Agent B. School Normalization Agent

목표:

- 학교명/학교코드/캠퍼스 정규화 모듈 설계 및 구현
- alias table 구축
- 위험학교 regression test 작성

산출물:

- `utils/school_normalization.py`
- `data/metadata/school_aliases.csv`
- `tests/unit/test_school_normalization.py`
- `tests/contracts/test_school_scope_consistency.py`

반드시 포함할 테스트:

- `136` → `0000136`
- 강서/케이씨/그리스도 alias
- 서울한영/한영신학 alias
- 건국대와 건국대(글로컬) 병합 금지
- 고려대와 고려대(세종) 병합 금지
- 가톨릭대학교 부분검색 오염 금지

---

### Agent C. Academyinfo Converter Agent

목표:

- `student_recruitment` 파일럿 converter 구현
- 27/29/31번 XLSX 병합
- 재학생충원율 공백 문제 해결
- source/dataset metadata 생성

산출물:

- `scripts/converters/academyinfo_student_recruitment.py`
- `data/processed/student_recruitment/student_recruitment_2026_candidate_v2.csv`
- `data/metadata/student_recruitment.source.json`
- `data/metadata/datasets/student_recruitment.metadata.json`
- `data/validation/processing_reports/student_recruitment_2026_v2.processing_report.json`
- 관련 tests

검증 기준:

- 비교대학 11개 재학생충원율이 원자료 29번과 일치
- 전체 489행 `재학생충원율` 결측이 해소 또는 사유 문서화
- 가톨릭대 다중 캠퍼스가 학교코드/본분교로 분리

---

### Agent D. KASFO Converter Agent

목표:

- KASFO 결산 converter 설계
- 2022년 `기타국고지원[1514]` 누락 원인 확인
- 음수 부호 처리 규칙 확정
- 법정부담금 converter/metadata 보강

산출물:

- `scripts/converters/kasfo_settlement.py`
- `scripts/converters/kasfo_legal_burden.py`
- KASFO processing report
- mismatch report
- 관련 tests

검증 기준:

- 2022~2024 raw ZIP/XLSX row count와 processed row count 일치
- 비교대학 11개 주요 금액 일치
- 음수 부호 보존
- 공시연도/기준년도 차이 명시

---

### Agent E. KCUE/RINFO Converter Agent

목표:

- KCUE 기존 build script를 converter 표준 interface에 맞게 정리
- RINFO converter 설계
- RINFO `inf` 처리와 자료구입비 세부 컬럼 매핑 검증

산출물:

- `scripts/converters/kcue_university_indicators.py`
- `scripts/converters/rinfo_library_staff.py`
- `scripts/converters/rinfo_material_purchase.py`
- 관련 processing report/tests

검증 기준:

- KCUE raw→wide→long mismatch 0 유지
- RINFO 분모 0이 `inf`로 남지 않음
- RINFO scope 34개 필터 적용

---

### Agent F. QA/Reviewer Agent

목표:

- 전체 converter 결과에 대한 contract/unit test 작성
- mismatch severity 검증
- regression test 보강
- 최종 release readiness 판단

산출물:

- `tests/contracts/test_raw_to_processed_consistency.py`
- `tests/contracts/test_source_metadata_contracts.py`
- `tests/contracts/test_no_inf_in_metrics.py`
- `docs/conversion_system_qa_report.md`

검증 기준:

- pytest 통과
- 기존 대시보드 loader smoke test 통과
- current asset 변경 전후 diff 확인

---

## 7.2 서브에이전트 실행 순서

### Phase 0. 준비

main이 수행:

1. 현재 git 상태 확인
2. 기존 보고서/테스트/loader inventory 확인
3. 구현 브랜치 확인
4. read-only 설계 문서 확정

### Phase 1. 병렬 설계

동시 실행:

- Agent A: architecture/contract
- Agent B: school normalization 설계
- Agent F: QA test plan

목표:

- 공통 interface와 테스트 기준을 먼저 고정한다.

### Phase 2. 파일럿 구현

동시 또는 순차 실행:

- Agent B: normalization module 구현
- Agent C: student_recruitment converter 구현
- Agent F: 관련 contract test 작성

목표:

- `student_recruitment`를 첫 성공 사례로 만든다.

### Phase 3. 소스군 확장

동시 실행:

- Agent D: KASFO converter
- Agent E: KCUE/RINFO converter
- Agent C: academyinfo 기숙사/강사료 확장 설계

목표:

- converter framework를 다른 소스군으로 확장한다.

### Phase 4. 통합/검증

main + Reviewer Agent:

1. 전체 pytest 실행
2. processed current asset diff 확인
3. mismatch report 검토
4. dashboard smoke test
5. 최종 QA 보고서 작성

---

## 8. 구현 마일스톤

## M1. 설계 고정

기간: 0.5~1일

산출물:

- conversion system architecture 문서
- source inventory schema
- processing report schema
- converter base interface
- severity 기준

완료 조건:

- main이 architecture 승인
- QA test 목록 확정

## M2. 학교 정규화 기반 구축

기간: 1일

산출물:

- `utils/school_normalization.py`
- `data/metadata/school_aliases.csv`
- unit/contract tests

완료 조건:

- 위험학교 regression test 통과
- scope 34개 exact 유지 확인

## M3. student_recruitment 파일럿 converter

기간: 1~2일

산출물:

- academyinfo student recruitment converter
- candidate v2 CSV
- source/dataset metadata
- processing report
- mismatch report

완료 조건:

- 27/29/31번 원자료 병합 성공
- 비교대학 11개 값 일치
- 재학생충원율 전 행 공백 해소
- metadata/report 생성

## M4. KASFO converter

기간: 1~2일

산출물:

- settlement converter
- legal burden converter
- 누락/부호 mismatch report

완료 조건:

- 2022 기타국고지원 누락 원인 확인
- 음수 부호 처리 규칙 확정
- 법정부담금 leading zero 보존

## M5. KCUE/RINFO converter 표준화

기간: 1~2일

산출물:

- KCUE converter 표준화
- RINFO converter 및 report
- no-inf handling

완료 조건:

- KCUE mismatch 0 유지
- RINFO `inf` 제거
- 자료구입비 세부 컬럼 매핑 검증 또는 limitation 명시

## M6. 통합 QA/대시보드 연결

기간: 1일

산출물:

- 전체 pytest 결과
- dashboard smoke test 결과
- conversion QA report
- current asset 승격 후보 목록

완료 조건:

- blocker 0
- high issue는 owner/action 명시
- 대시보드 loader 정상 작동

---

## 9. 데이터 승격 정책

원자료 변환 결과는 바로 운영 current asset으로 덮어쓰지 않는다.

### 단계

1. `candidate`
   - 변환 완료
   - 검증 전
2. `validated`
   - row/value/scope 검증 통과
   - mismatch가 medium 이하이거나 문서화됨
3. `current`
   - main 승인 후 대시보드 loader가 사용하는 파일
4. `archived`
   - 이전 current asset 보관

### 승격 조건

- blocker 0
- high 0 또는 승인된 known issue
- 비교대학 11개 누락 0
- scope 34개 유지
- source metadata 존재
- processing report 존재
- pytest 통과
- dashboard smoke test 통과

---

## 10. 테스트 전략

### 10.1 Unit Tests

대상:

- school normalization
- formula registry
- file fingerprint
- parser helpers
- numeric conversion
- date/year handling

예시:

- `test_legacy_school_code_zfill_7_digits`
- `test_no_parentheses_strip_for_branch_campus`
- `test_dash_to_null_numeric_conversion`
- `test_comma_number_parse`

### 10.2 Contract Tests

대상:

- source metadata
- raw file existence
- processing report counts
- scope consistency
- no-inf metrics
- current asset manifest

예시:

- `test_raw_files_declared_in_source_metadata_exist`
- `test_processing_report_counts_match_processed_files`
- `test_comparison_11_schools_present_in_all_current_assets`
- `test_default_scope_34_schools_after_loader_filter`
- `test_no_inf_or_literal_inf_in_display_metric_columns`

### 10.3 Integration Tests

대상:

- raw → processed 변환
- processed → loader
- loader → dashboard service

예시:

- student_recruitment 27/29/31번 XLSX fixture 변환
- KASFO settlement raw ZIP sample 변환
- KCUE raw XLSX sample 변환

### 10.4 Smoke Tests

대상:

- Streamlit page import
- 주요 loader 실행
- 비교대학 설정 로드
- chart data 생성

---

## 11. 위험과 대응

| 위험 | 영향 | 대응 |
|---|---|---|
| 원자료 구조 변경 | converter 실패 | table profile + schema versioning |
| 병합셀/다중 헤더 파싱 오류 | 값 mismatch | parser snapshot + row/cell audit |
| 학교명 부분검색 오염 | 다른 학교 값 귀속 | exact/alias only, partial 금지 테스트 |
| old-name alias 누락 | 과거연도 누락 | alias table valid_from/to 관리 |
| raw 파일 미보존 | 검증 불가 | source inventory + checksum 필수화 |
| 산식 정의 불명확 | 값 해석 오류 | source_value_only 플래그 |
| KASFO 계정 정의 혼동 | 법인전입금/재정지표 오류 | KCUE/KASFO 지표 분리 표시 |
| `inf` UI 노출 | 차트/표 오류 | zero denominator policy |
| current asset 덮어쓰기 | 운영 데이터 손상 | candidate→validated→current 승격 |

---

## 12. 우선 구현 대상

### 1순위: student_recruitment

이유:

- 원자료 27/29/31번 XLSX가 이미 있음.
- mismatch가 명확함: 재학생충원율 전 행 공백.
- converter 파일럿에 적합함.
- 비교대학 11개 검증값이 확보되어 있음.

### 2순위: school_normalization

이유:

- 모든 converter의 공통 기반.
- 잘못 만들면 본교/분교 데이터가 오염됨.
- KASFO, 대학알리미, RINFO, legacy 전체에 영향.

실제로는 1순위와 2순위를 함께 진행해야 한다. 단, current asset 승격은 school normalization 테스트가 통과한 뒤 진행한다.

### 3순위: KASFO settlement

이유:

- 2022 기타국고지원 누락과 음수 부호 차이가 high severity.
- 결산 기반 지표가 많아질 가능성이 큼.

### 4순위: RINFO

이유:

- `inf`와 자료구입비 세부 컬럼 매핑 의심.
- 원본 파일 복원이 필요함.

### 5순위: KCUE 표준화

이유:

- 이미 검증 상태가 좋음.
- converter framework에 맞춰 정리하면 됨.

---

## 13. 첫 구현 스프린트 제안

### 목표

`student_recruitment` 원자료 자동변환 파일럿 완성.

### 작업 목록

1. `school_aliases.csv` 초안 작성.
2. `utils/school_normalization.py` 구현.
3. 위험학교 테스트 추가.
4. `academyinfo_student_recruitment.py` converter 구현.
5. 27/29/31번 XLSX 병합.
6. `student_recruitment_2026_candidate_v2.csv` 생성.
7. source/dataset metadata 생성.
8. processing/mismatch report 생성.
9. 기존 candidate와 v2 diff 작성.
10. pytest 실행.

### 완료 기준

- 비교대학 11개 신입생충원율/경쟁률/재학생수/재학생충원율이 원자료와 일치.
- `재학생충원율` 전 행 공백 문제 해소.
- 가톨릭대 다중 캠퍼스가 분리됨.
- 건국대 본교/글로컬이 병합되지 않음.
- blocker 0.
- high 0 또는 명시적 known issue.

---

## 14. 서브에이전트 운영 규칙

1. main이 전체 계획과 최종 승인 담당.
2. 각 에이전트는 제한된 범위의 파일만 수정.
3. raw 파일은 절대 수정하지 않음.
4. current asset 직접 덮어쓰기 금지.
5. candidate output만 생성.
6. 모든 에이전트는 산출물에 다음을 포함.
   - 변경 파일
   - 검증 명령
   - mismatch 목록
   - known limitation
   - 다음 작업 제안
7. reviewer/QA 단계 전에는 current 승격 금지.
8. 외부 공식 사이트 자동 다운로드는 별도 승인 없이는 금지.

---

## 15. 구현 전 확인 질문

실제 구현에 들어가기 전 결정할 사항은 3개다.

1. 변환 output을 CSV 중심으로 유지할지, SQLite/Parquet도 병행할지.
   - 추천: 1차는 CSV + metadata/report. SQLite는 이후.
2. raw 원본 파일을 repo에 보존할지, 별도 storage에 두고 checksum만 repo에 둘지.
   - 추천: 현재는 repo 내 `data/raw/` 보존. 용량이 커지면 storage 분리.
3. current asset 승격을 자동으로 할지 수동 승인으로 할지.
   - 추천: 수동 승인.

---

## 16. 결론

원자료 자동변환 시스템 구축은 가능하며, 현재 프로젝트에는 필요성이 높다. 다만 전체 지표를 한 번에 자동화하면 리스크가 크다.

가장 안전한 접근은 다음 순서다.

1. 학교명/학교코드/캠퍼스 정규화 기반 구축.
2. `student_recruitment`를 파일럿 converter로 구현.
3. metadata/report/test 체계를 고정.
4. KASFO, RINFO, KCUE, 기타 대학알리미 지표로 확장.
5. candidate→validated→current 승격 체계를 도입.

이 방식이면 단순 데이터 변환이 아니라, 원자료 일치성·검증 가능성·재현성을 갖춘 운영형 데이터 파이프라인으로 발전시킬 수 있다.
