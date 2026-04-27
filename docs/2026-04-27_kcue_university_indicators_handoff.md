# 한국대학평가원 대학현황지표 가공 작업 인수인계

작성일: 2026-04-27

## 작업 목적

한국대학평가원 대학통계에서 내려받은 2015~2025년 대학현황지표 엑셀 원자료를 기존 구현 지표(예: 교육비 환원율)와 유사한 구조로 정리했다.

핵심 목표는 준비중 지표 DB 구축에 바로 쓸 수 있도록 다음을 갖춘 형태로 만드는 것이었다.

- 원본 보존
- UTF-8 CSV 변환본
- DB 적재형 long CSV
- 스키마 문서
- 출처 메타데이터
- 처리 리포트
- 재생성 스크립트

## 최종 파일 위치

원본 엑셀은 루트 폴더에서 아래 raw 디렉토리로 이동했다.

- `data/raw/kcue_university_indicators/original/`

원본 설명 문서:

- `data/raw/kcue_university_indicators/README.md`

가공 CSV:

- `data/processed/kcue_university_indicators/kcue_university_indicators_2015_2025_v1_utf8.csv`
- `data/processed/kcue_university_indicators/kcue_university_metric_values_2015_2025_v1_utf8.csv`

메타데이터:

- `data/metadata/kcue_university_indicators_v1.source.json`
- `data/metadata/kcue_university_indicators_v1_schema.md`
- `data/metadata/kcue_university_indicators_v1.processing_report.json`

재생성 스크립트:

- `scripts/build_kcue_university_indicators.py`

관련 코드 변경:

- `registry/raw_schemas.py`
  - 새 가공 CSV 2개를 unregistered CSV allowlist에 추가했다.
- `requirements.txt`
  - XLSX 재처리를 위해 `openpyxl>=3.1.0`을 추가했다.

## 산출물 구조

### Wide CSV

파일:

- `data/processed/kcue_university_indicators/kcue_university_indicators_2015_2025_v1_utf8.csv`

성격:

- 대학-연도 1행 구조
- 2015~2025년 전체 원자료를 하나의 표준 영문 컬럼으로 통합
- 원자료값(`*_original`)과 분자/분모 기반 재계산값(`*_recalculated`)을 함께 보존
- 2주기, 3주기, 4주기의 컬럼 순서 차이를 스크립트에서 명시적으로 매핑

생성 당시 크기:

- 2,054행
- 111컬럼

### Long CSV

파일:

- `data/processed/kcue_university_indicators/kcue_university_metric_values_2015_2025_v1_utf8.csv`

성격:

- DB 적재에 가까운 metric-values 구조
- 주요 컬럼:
  - `metric_id`
  - `metric_label_ko`
  - `reference_year`
  - `evaluation_cycle`
  - `university_name`
  - `founding_type`
  - `region_name`
  - `value`
  - `value_original`
  - `value_recalculated`
  - `numerator`
  - `denominator`
  - `unit`
  - `source_file_name`

생성 당시 크기:

- 43,184행

## 처리 로직 요약

스크립트:

- `scripts/build_kcue_university_indicators.py`

주요 처리 단계:

1. `data/raw/kcue_university_indicators/original/`에서 `*.xlsx` 파일을 읽는다.
2. 파일명에서 기준연도와 평가 주기를 추출한다.
3. 각 파일의 `대학현황지표` 시트를 읽는다.
4. 2016년 파일의 빈 보조 컬럼 3개를 제거한다.
5. 2주기, 3주기, 4주기의 컬럼 배치 차이를 각각 별도 매핑 함수로 처리한다.
6. 2015~2017년 재정 관련 천원 단위 원자료는 wide CSV의 `*_krw` 컬럼에서 원 단위로 환산한다.
7. 가능한 지표는 원자료 지표값과 분자/분모 기반 재계산값을 함께 생성한다.
8. wide CSV, long CSV, source metadata, schema markdown, processing report, raw README를 생성한다.

재생성 명령 예시:

```bash
/Users/mortarteam81/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/build_kcue_university_indicators.py --project-root /Users/mortarteam81/Documents/Codex/2026-04-25/users-mortarteam81-visualization-14-ba-2/visualization_14_ba_2 --patch-allowlist
```

## 생성 당시 검증 메모

사용자가 최종 검증은 별도로 진행한다고 했지만, 생성 직후 아래 수준의 sanity check는 수행했다.

- wide CSV: 2,054행 x 111컬럼
- long CSV: 43,184행
- 학교명+연도 중복: 0건
- 주요 산식 재계산 검증: 비교 가능한 지표에서 오차 0.05 초과 0건
- raw schema inventory 계약 테스트: `6 passed`

실행했던 테스트:

```bash
.venv/bin/python -m pytest tests/contracts/test_raw_schema_inventory.py
```

주의:

- 이후 사용자가 “검증은 별도로 하겠다”고 했으므로, 원본 이동 뒤에는 별도 전체 검증을 다시 돌리지 않았다.

## 객관적 판단과 주의사항

이 데이터는 준비중 지표 DB의 골격을 빠르게 만드는 데 매우 유용하다.

장점:

- 2015~2025년을 한 번에 연결할 수 있다.
- 교육비 환원율처럼 이미 구현된 항목과 유사하게 원자료값과 재계산값을 함께 둘 수 있다.
- 2025년 4주기 신규 지표 일부도 포함되어 있어 준비중 지표 후보 탐색에 좋다.

단점 및 리스크:

- 한국대학평가원 자료는 1차 공시 원자료가 아니라 평가용 2차 집계 자료다.
- 대학알리미, 대학재정알리미, RINFO 등 1차 출처와 최종 대조가 필요하다.
- 2025년 4주기부터 지표 구성이 바뀌어 장기 추세 분석 시 정의 변경을 표시해야 한다.
- 원자료에는 대학알리미 학교 ID, 캠퍼스 코드, 본분교 코드가 없다. 학교명 기반 매칭만 가능하므로 통폐합/명칭 변경/캠퍼스 분리 이슈는 별도 매핑이 필요하다.
- 4주기에는 일부 2~3주기 지표가 사라지고, `법정부담금 부담률`, `법인 재정규모 대비 법인전입금 비율`, `학생 충원 성과`, `졸업생 진로 성과`, `기숙사 수용률 II` 같은 신규 지표가 들어간다.

## 다음 세션에서 확인하면 좋은 것

1. `data/metadata/kcue_university_indicators_v1.processing_report.json`의 `missing_by_column`과 `metric_counts`를 보고 지표별 연도 커버리지를 확인한다.
2. 서비스에 실제 반영할 지표를 고른 뒤, 해당 지표만 1차 출처와 대조한다.
3. 학교명 매칭 테이블을 추가할지 결정한다.
4. 이미 구현된 개별 지표 CSV와 이 통합 CSV의 값 차이를 비교한다.
5. 장기 추세 화면에서 2주기/3주기/4주기 구간을 시각적으로 구분할지 결정한다.

## 현재 git 상태상 새/수정 파일 범위

주요 신규 파일:

- `data/raw/kcue_university_indicators/README.md`
- `data/raw/kcue_university_indicators/original/*.xlsx`
- `data/processed/kcue_university_indicators/*.csv`
- `data/metadata/kcue_university_indicators_v1.source.json`
- `data/metadata/kcue_university_indicators_v1_schema.md`
- `data/metadata/kcue_university_indicators_v1.processing_report.json`
- `scripts/build_kcue_university_indicators.py`
- `docs/2026-04-27_kcue_university_indicators_handoff.md`

수정 파일:

- `registry/raw_schemas.py`
- `requirements.txt`
