# 2026-05-01 원자료-시스템 DB 교차검증 메모

대상 문서: `docs/2026-05-01_source_db_consistency_audit.md`

목적: 기존 감사 문서의 주요 주장과 우선순위를 공식 출처 접근, 로컬 raw/processed 파일, metadata manifest, 테스트 결과로 교차 확인한다.

작업 방식:

- 공식 출처 접근성 확인: 대학알리미, 대학재정알리미/KASFO, KCUE/한국대학평가원, RINFO.
- 병렬 read-only 감사: Academyinfo/scope, KCUE/faculty, KASFO finance, RINFO library, metadata/SQLite.
- 로컬 raw/processed 표본 대조: 항목별 가능한 범위에서 5개 이상 대학과 복수 연도 확인.
- 파일 수정 및 원자료 변경 없음.

## 1. 종합 판단

기존 감사 문서의 핵심 결론은 대체로 타당하다. 특히 `student_recruitment` 재학생충원율 결측, KASFO 2022 기타국고지원 문제, RINFO/원본파일 보존 한계, SQLite 비운영 상태는 독립 검증에서도 재현되었다.

추가로 다음 3개 리스크는 기존 문서보다 더 강하게 관리해야 한다.

1. RINFO `재학생 1000명당 도서관 직원수` 2025년 산식 가중치가 공식 RINFO와 충돌한다.
2. 교원확보율 pages 16~18은 default scope 적용 후 2015년 데이터가 화면에서 전부 빠진다.
3. KASFO 2022 `5.기타국고지원[1514]`는 단순 공백이 아니라 `5.타기관[1314]` 쪽으로 값이 들어간 컬럼 밀림 가능성이 높다.

## 2. 공식 출처 접근 확인

- 대학알리미 공시항목 페이지에서 `신입생 충원 현황`, `재학생 충원율`, `재적 학생 현황`, 전임교원/연구/재정 항목의 공시기관 및 기준일을 확인했다.
- KASFO 대학재정알리미에서 `2024회계연도 법인일반회계 및 교비회계 결산` 게시물과 첨부파일 존재를 확인했다.
- KCUE/한국대학평가원 사이트에서 4주기 대학기관평가인증 운영 및 대학통계/정량 데이터 제공 맥락을 확인했다.
- RINFO에서 `재학생 1,000명당 도서관 직원수`, `재학생 1인당 자료구입비(결산)` 계열 지표가 공식 주요지표로 제공되는 것을 확인했다.

## 3. 교차검증 결과

### 3.1 대학알리미 student_recruitment

판정: `blocker`

확인 결과:

- `student_recruitment_2026_candidate.csv`: 489행.
- `재학생충원율`: 489/489행 공백.
- raw item 29 `academyinfo_2025_29_student_fill_school.xlsx`에는 2025 상반기 값 존재.
- raw item 27/31과 processed의 신입생충원율, 신입생경쟁률, 재학생수는 표본 11개 비교대학에서 mismatch 0.

표본:

| 학교 | raw 재학생충원율 | processed |
|---|---:|---:|
| 성신여자대학교 | 110.0 | 공백 |
| 숙명여자대학교 | 117.0 | 공백 |
| 덕성여자대학교 | 120.2 | 공백 |
| 서울여자대학교 | 117.2 | 공백 |
| 동덕여자대학교 | 101.3 | 공백 |
| 이화여자대학교 | 127.2 | 공백 |
| 세종대학교 | 133.4 | 공백 |

추가 판단:

- 기존 감사 문서의 `high/blocker` 판정은 맞다.
- 이미 결측 상태를 확인하는 테스트는 존재하지만, 원자료 item 29 병합 후 non-empty를 보장하는 테스트로 전환해야 한다.

### 3.2 기본 분석 scope와 alias

판정: `high structural risk`

확인 결과:

- `seoul_private_four_year_universities.json`은 34개 학교를 정의한다.
- `alias_groups`는 2개: 강서대학교, 서울한영대학교.
- 2026 key-indicator/student_recruitment에는 34/34 scope가 정확히 적용된다.
- 그러나 기숙사 등 historical 데이터에서는 그리스도대학교/케이씨대학교/강서대학교, 한영신학대학교/서울한영대학교가 별도 학교명으로 남아 trend continuity가 깨질 수 있다.
- RINFO loader는 scope manifest가 아니라 단순 `서울/사립/대학/no "_"` 조건을 사용해 42개 학교를 반환한다.

추가 포함 위험 학교:

- 고려사이버대학교
- 디지털서울문화예술대학교
- 명지대학교
- 서울디지털대학교
- 서울사이버대학교
- 숭실사이버대학교
- 태재대학교
- 한국열린사이버대학교

### 3.3 KCUE 대학현황지표

판정: `verified for raw->processed pipeline`

확인 결과:

- raw XLSX 11개.
- wide CSV: 2,054행 x 111열.
- long CSV: 43,184행 x 14열.
- 27개 학교, 2015~2025 표본 기준 raw→wide, wide→long mismatch 0.
- strict numeric compare에서 22건의 초미세 float delta가 있었으나 최대 차이 0.000122 수준이라 실질 불일치가 아니다.

주의:

- KCUE 전체 pipeline은 신뢰 가능하지만 manifest는 모두 `verified`가 아니다.
- `corp_transfer_ratio`, `staff_per_student`는 `verified`, `scholarship_ratio`는 `partial`.
- `research_performance_vs_standard`와 일부 2025 4주기 지표는 분자/분모가 없고 원자료값 중심이다.

### 3.4 교원확보율 pages 16~18

판정: `high`

확인 결과:

- faculty raw XLSX 11개와 processed detail/total/long 값 대조는 mismatch 0.
- 그러나 pages 16~18에서 default scope 적용 후 2015년 데이터가 화면에서 빠진다.
- 원인: 2015년 학교명에 `성신여자대학교 본교` 같은 suffix가 포함되어 canonical `성신여자대학교`와 매칭되지 않는다.

영향:

- 원자료/processed 값 자체는 신뢰 가능하다.
- 화면 표시/연도 추세는 2015년이 누락되어 사용자가 장기 추이를 볼 때 왜곡될 수 있다.

### 3.5 KASFO 결산

판정: `partial with high-risk issues`

확인 결과:

- `data/결산(22,23,24).csv`: 1,870행 x 341열.
- KASFO 5년 ZIP의 자금계산서 2022~2024 subset: 1,870행 x 340열.
- 2024 standalone XLSX는 processed 2024와 624행, 주요 322개 coded column mismatch 0.
- 2022 `5.기타국고지원[1514]` mismatch는 295건이며 모두 2022년이다.

중요 보정:

- 이 문제는 단순 누락이라기보다 raw `5기타국고지원(1514)` 값이 processed `5.기타국고지원[1514]`가 아니라 `5.타기관[1314]` 쪽에 들어간 컬럼 매핑 오류 가능성이 높다.

표본:

| 학교 | 회계 | 2022 raw `1514` | processed `1514` |
|---|---|---:|---:|
| 성신여자대학교 | 교비 | 1,220,420 | 공백 |
| 숙명여자대학교 | 교비 | 2,091,445 | 공백 |
| 이화여자대학교 | 교비 | 4,110,269 | 공백 |
| 세종대학교 | 교비 | 1,699,176 | 공백 |
| 숭실대학교 | 교비 | 1,237,964 | 공백 |

음수 이월자금:

- 5년 ZIP과 processed 사이에는 sign-only mismatch가 많다.
- 다만 2024 standalone XLSX는 processed의 음수 부호와 일치한다.
- 따라서 2022~2023 standalone 원본이 확보되기 전까지는 ZIP 기준/standalone 기준 중 무엇이 authoritative인지 확정하면 안 된다.

### 3.6 교육비 환원율

판정: `partial`

확인 결과:

- 1,975행.
- 산식 재계산 finite row 기준 mismatch 0.
- `source_file_name`: 전 행 공백.
- `education_cost_return_rate_original_pct`: 전 행 공백.
- raw 원본 XLSX는 보존되어 있지 않다.

판단:

- 시스템 산식은 맞지만, 공식 원자료 비율과 일치한다고 말할 수는 없다.
- 분모 0/극소 분모 outlier는 quality flag가 필요하다.

### 3.7 법정부담금

판정: `formula-valid with metadata/key gaps`

확인 결과:

- 475행.
- `법정부담금부담액 / 법정부담금기준액 * 100` mismatch 0.
- 학교코드 7자리 zero-padding은 모두 소실되어 있다.
- `공시연도 2025 = 기준년도 2024` 구조이므로 UI/metadata에서 혼동 방지가 필요하다.

### 3.8 RINFO 학술정보통계

판정: `partial with high-risk issues`

도서관 직원수:

- 8,215행, 2008~2025.
- `inf` 94건, `enrolled_students=0` 923건.
- loader는 `inf`를 drop하도록 되어 있어 UI 노출 위험은 낮아졌지만, 원자료 quality flag는 필요하다.
- 2025년 산식 가중치가 공식 RINFO와 충돌한다.

핵심 문제:

- local v6은 2025년 비정규직 사서 가중치를 1.0으로 쓰고 있다.
- 공식 RINFO 산식과 aggregate는 0.8 가중치와 맞는다.
- local aggregate는 1.3으로 반올림되지만 공식 RINFO aggregate는 1.2다.
- 영향: 2025년 204행, 34 scope 중 26개 학교, 비교대학 11개 모두.

자료구입비:

- 8,226행, 2008~2025.
- 유효 분모 기준 공식 산식과 대체로 일치.
- 그러나 `other_electronic_resources_expense == total_material_purchase_expense`가 전 행 true라 세부 컬럼 mapping은 신뢰하면 안 된다.
- main metric은 사용할 수 있으나 전자자료 세부 분석은 금지해야 한다.

### 3.9 metadata/SQLite

판정: `metadata usable, SQLite not operational`

확인 결과:

- 18개 implemented metric은 17개 dataset manifest로 모두 커버된다.
- 모든 `current_asset`은 존재한다.
- sample/샘플 파일은 current asset으로 쓰이지 않는다.
- `pending_metrics.sqlite`: `raw_sources=10`, `raw_records=489`, `metric_values=0`.

추가 리스크:

- SQLite는 current operational DB가 아니라 stale planning/catalog DB에 가깝다.
- `pending_metric_plans`는 SQLite 9개, 현재 코드 5개로 차이가 있어 운영 기준으로 쓰면 안 된다.
- source metadata가 없는 implemented dataset이 6개 있다: `budam`, `gyeolsan`, `gyowon`, `jirosung`, `paper`, `research`.

## 4. 테스트 결과

실행:

```bash
.venv/bin/python -m pytest \
  tests/contracts/test_dataset_metadata.py \
  tests/contracts/test_academyinfo_key_indicators_outputs.py \
  tests/contracts/test_registry_data_contracts.py \
  tests/unit/test_library_staff_pipeline.py \
  tests/unit/test_library_material_purchase_pipeline.py \
  tests/unit/test_education_return_pipeline.py
```

결과:

- 47 passed
- 1 warning

해석:

- 현재 테스트는 manifest/current asset 연결과 일부 loader 산식은 보장한다.
- 하지만 raw XLSX/ZIP와 processed의 항목별 값 대조, RINFO 2025 공식 산식, KASFO 2022 컬럼 밀림, faculty 2015 scope 누락은 아직 contract test로 고정되어 있지 않다.

## 5. 우선순위 제안

### P0

1. 공통 학교명/학교코드/캠퍼스 정규화 모듈 추가.
2. RINFO loader에 34개 scope manifest 필터 적용.
3. faculty 2015 `본교` suffix canonical 매칭 보정.

### P1

1. `student_recruitment`에 raw item 29 재학생충원율 병합.
2. KASFO 2022 `1514` 컬럼 매핑 오류 수정.
3. RINFO 2025 도서관 직원수 가중치 공식 산식으로 수정.

### P2

1. KASFO 2022~2023 standalone workbook 확보 또는 ZIP authoritative 여부 확정.
2. 교육비 환원율, 기숙사, 강사료, RINFO 원본 XLS/XLSX 보존.
3. source metadata와 processing report 보강.

### P3

1. SQLite를 운영 DB로 쓰지 않는다는 contract test 추가.
2. sample file이 current asset으로 쓰이지 않는다는 contract test 추가.
3. source metadata 없는 6개 dataset 보강.

## 6. 내 의견

여러 차례 검증이 필요하다는 판단에 동의한다. 현재 시스템은 시각화 기능보다 데이터 거버넌스가 더 중요한 단계다.

특히 이 프로젝트는 원자료 출처가 대학알리미, KASFO, KCUE, RINFO로 나뉘고, 일부는 raw 보존이 완전하지 않으며, 일부는 평가용 2차 집계와 원장성 자료가 섞여 있다. 따라서 단일 테스트 통과만으로 신뢰성을 선언하면 위험하다.

가장 안전한 개발 원칙은 다음과 같다.

- 화면에 노출되는 지표는 모두 `source -> raw -> processed -> loader -> UI` 추적 경로를 가져야 한다.
- 원자료 직접 검증이 불가능한 지표는 `partial`로 표시하고 사용자에게 출처 한계를 숨기지 않는다.
- 학교명/캠퍼스/코드는 값 대조보다 먼저 고정해야 한다.
- 공식 출처와 불일치한 값은 UI에서 정상값처럼 표시하지 않고 quality flag 또는 backlog로 격리한다.
