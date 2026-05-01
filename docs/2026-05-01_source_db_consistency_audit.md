# 2026-05-01 원자료-시스템 DB 일치성 통합 감사 보고서

대상 프로젝트: 4주기 대학기관평가인증 정량지표 시각화 대시보드

대상 경로: `/Users/mortarteam81/Documents/Codex/2026-04-25/users-mortarteam81-visualization-14-ba-2/visualization_14_ba_2`

작업 목적: 공식 원자료 및 로컬 raw 파일과 시스템 구현에 사용된 processed DB/CSV/SQLite/loader가 일치하는지 검증하고, 불일치·부분검증·수정 우선순위를 정리한다.

검증 방식: 내부 isolated sub-agent 5개 병렬 read-only 감사 결과를 통합했다. 파일 수정, 원본 데이터 변경, 대량 자동 다운로드는 수행하지 않았다. 공식 사이트는 공개 페이지 확인 및 로컬 raw 파일 대조 중심으로 사용했다.

공식 원자료 출처:

- 대학알리미: <https://academyinfo.go.kr/main/main0830/main0830.do>
- 사학재정알리미/KASFO: <https://uniarlimi.kasfo.or.kr/knowledge/data2Room>
- 한국대학평가원/KCUE: <https://aims.kcue.or.kr/EgovPageLink.do?subMenu=5020000>

관련 선행 보고서:

- `docs/2026-05-01_data_source_validation_audit.md`
- `docs/2026-04-30_data_inventory_audit.md`

---

## 1. 종합 판정

| 소스군 | 판정 | 요약 |
|---|---:|---|
| KCUE/한국대학평가원 대학현황지표 | verified | raw XLSX 11개와 processed wide/long CSV 대조 결과 mismatch 0건. 비교대학·위험학교·이상치 학교 모두 일치. |
| 대학알리미 student_recruitment | high/blocker | 신입생충원율·경쟁률·재학생수는 원자료와 일치. 그러나 `재학생충원율`이 processed 전 행 공백이고 원자료에는 값이 있음. |
| 대학알리미 기숙사/강사료 | partial | processed 내부 산식/loader는 검증 가능. 원본 XLSX 부재로 원자료 직접 대조 제한. |
| KASFO 결산 | partial with high-risk issues | raw finance 자료와 대부분 일치하나 2022년 `기타국고지원[1514]` 누락, 음수 부호 차이, 일부 학교/법인명 불일치 존재. |
| KASFO 교육비 환원율 | partial | 산식 재계산은 전 행 일치. 원본 XLSX, `source_file_name`, 원자료 비율 컬럼이 없어 원자료 직접 일치 선언 불가. |
| 법정부담금 | verified with metadata gaps | 루트 원본성 CSV와 data CSV가 의미상 일치. 학교코드 leading zero 및 숫자 표현 차이만 있음. |
| RINFO 학술정보통계 | partial with high-risk issues | 산식 재현 가능하나 원본 xls/xlsx 부재. `inf` 발생, 자료구입비 세부 컬럼 매핑 의심. |
| 학교명/코드/scope | high priority structural risk | 비교대학 11개는 안정적이나 부분검색·괄호 제거·leading zero 소실·캠퍼스 혼재 위험이 큼. |
| SQLite DB | not operational | `pending_metrics.sqlite`의 `metric_values`가 0행이므로 운영 DB 일치성 검증 대상으로 보기 어려움. |

### 최종 결론

현재 대시보드는 **비교대학 11개 중심의 processed 분석**은 상당 부분 가능하다. 그러나 “공식 원자료와 시스템 DB가 완전히 일치한다”고 선언하려면 아직 부족하다.

즉시 수정해야 할 핵심은 다음 4개다.

1. `student_recruitment_2026_candidate.csv`의 `재학생충원율` 전 행 공백 문제 보정.
2. 학교명/학교코드/캠퍼스 정규화 모듈과 테스트 고정.
3. KASFO 결산의 2022년 `기타국고지원[1514]` 누락 및 음수 부호 차이 확인.
4. 원본 XLSX 미보존 데이터셋의 raw 보존/metadata/report 보강.

---

## 2. 검증 기준

원자료와 시스템 DB 일치성은 다음 항목 기준으로 판단했다.

1. 원자료 보존
   - raw file 존재 여부
   - 공식 URL
   - 다운로드일/수집일
   - 원본 파일명
   - checksum/hash 여부

2. 처리 추적성
   - source metadata
   - schema 문서
   - processing report
   - row count/year count/school count
   - 필터 전후 count

3. 키 일치성
   - 학교코드
   - 대표학교코드
   - 학교명
   - 본분교/캠퍼스명
   - 구명칭 alias
   - 서울 사립 4년제 본교 scope 포함 여부

4. 값 일치성
   - 원자료값
   - processed 값
   - long metric 값
   - SQLite/운영 DB 값
   - 분자/분모
   - 최종 지표값
   - 단위 변환
   - 반올림 기준
   - 결측/0/`-`/분모 0/`inf` 처리

5. 사용자 지정 필수 검증 학교
   - 비교대학 11개
   - 캠퍼스/분교 위험학교
   - old-name alias 학교
   - 이상치/분모효과 학교

---

## 3. 필수 검증 학교 목록

### 3.1 비교대학 11개

- 성신여자대학교
- 숙명여자대학교
- 덕성여자대학교
- 서울여자대학교
- 동덕여자대학교
- 이화여자대학교
- 한성대학교
- 서경대학교
- 광운대학교
- 세종대학교
- 숭실대학교

### 3.2 학교명/캠퍼스 위험학교

- 가톨릭대학교
- 건국대학교 / 건국대학교(글로컬)
- 고려대학교 / 고려대학교(세종)
- 동국대학교 / 동국대학교(WISE)
- 연세대학교 / 연세대학교(미래)
- 한양대학교 / 한양대학교(ERICA)
- 강서대학교 / 케이씨대학교 / 그리스도대학교
- 서울한영대학교 / 한영신학대학교

### 3.3 이상치/분모효과 관찰 학교

- 감리교신학대학교
- 서울기독대학교
- 대전가톨릭대학교
- 영산선학대학교
- 칼빈대학교

---

## 4. 소스별 상세 결과

## 4.1 KCUE/한국대학평가원 대학현황지표

### 검증 대상

- `data/raw/kcue_university_indicators/original/*.xlsx`
- `data/processed/kcue_university_indicators/kcue_university_indicators_2015_2025_v1_utf8.csv`
- `data/processed/kcue_university_indicators/kcue_university_metric_values_2015_2025_v1_utf8.csv`
- `data/metadata/kcue_university_indicators_v1.*`
- `scripts/build_kcue_university_indicators.py`
- `registry/metadata.py`
- `registry/raw_schemas.py`

공식 URL:

- <https://aims.kcue.or.kr/EgovPageLink.do?subMenu=5020000>

### 대조 결과

| 항목 | 결과 |
|---|---:|
| raw XLSX 파일 수 | 11개 |
| raw 연도 | 2015~2025 |
| raw 정리 후 컬럼 수 | 2015~2024: 69개, 2025: 70개 |
| 필수 학교 raw→wide 대조 | 297개 학교-연도 row |
| raw→wide 비교 cell | 32,967개 |
| raw→wide mismatch | 0건 |
| 필수 학교 wide→long 대조 | 6,204개 metric row |
| wide→long mismatch | 0건 |

### 판단

KCUE 계열은 원자료 XLSX와 processed DB 일치성이 높다. raw XLSX에서 wide CSV로의 컬럼 매핑, 2015~2017년 `천원 → 원` 환산, wide CSV에서 long metric CSV로의 변환이 모두 검증되었다.

비교대학 11개, 캠퍼스 위험학교, 이상치 학교 모두 2015~2025 전 연도에서 exact match로 확인되었다.

### 주의 사항

일부 4주기 지표는 분자/분모가 없어 원자료값 일치 여부만 검증 가능하다.

- `research_performance_vs_standard`
- 2025 `full_time_faculty_rate`
- 2025 `adjunct_faculty_rate`
- 2025 `faculty_combined_rate`
- 2025 `student_recruitment_performance`

권고:

- UI/metadata에 “분자/분모 없음, 원자료값 사용” 표시.
- KCUE source metadata의 URL을 사용자 지정 공식 URL과 현재 metadata URL 중 실제 다운로드 경로 기준으로 정리.
- KCUE wide/long schema contract 보강.

판정: **verified**

---

## 4.2 대학알리미 - student_recruitment

### 검증 대상

- `data/raw/pending_manual/academyinfo/academyinfo_2025_27_freshman_fill_school.xlsx`
- `data/raw/pending_manual/academyinfo/academyinfo_2025_29_student_fill_school.xlsx`
- `data/raw/pending_manual/academyinfo/academyinfo_2025_31_enrolled_students_school.xlsx`
- `data/processed/student_recruitment/student_recruitment_2026_candidate.csv`
- `scripts/fetch_academyinfo_key_indicators.py`

공식 URL:

- <https://academyinfo.go.kr/main/main0830/main0830.do>

### 검증 결과

신입생충원율, 경쟁률, 재학생수는 비교대학 11개 기준 원자료와 processed DB가 일치했다.

| 학교 | 27번 신입생충원율/경쟁률 | 31번 재학생수 | 판정 |
|---|---:|---:|---|
| 성신여자대학교 | 99.7 / 12.4 | 9,404 | 일치 |
| 숙명여자대학교 | 100.0 / 12.2 | 10,134 | 일치 |
| 덕성여자대학교 | 100.0 / 15.5 | 5,566 | 일치 |
| 서울여자대학교 | 99.9 / 13.2 | 7,692 | 일치 |
| 동덕여자대학교 | 99.9 / 15.8 | 6,392 | 일치 |
| 이화여자대학교 | 99.5 / 9.8 | 16,452 | 일치 |
| 한성대학교 | 100.0 / 10.4 | 7,011 | 일치 |
| 서경대학교 | 100.0 / 18.8 | 6,864 | 일치 |
| 광운대학교 | 99.7 / 14.3 | 8,414 | 일치 |
| 세종대학교 | 100.0 / 16.3 | 13,171 | 일치 |
| 숭실대학교 | 99.8 / 15.4 | 14,738 | 일치 |

### 치명적 불일치

`student_recruitment_2026_candidate.csv`의 `재학생충원율`은 전체 489행이 공백이다.

| 항목 | 결과 |
|---|---:|
| 전체 행 | 489 |
| `재학생충원율` 공백 | 489 |
| `재학생충원율` 비공백 | 0 |

그러나 원자료 29번에는 값이 존재한다.

| 학교 | 원자료 29번 2025 상반기 재학생충원율 | processed |
|---|---:|---:|
| 성신여자대학교 | 110.0 | 공백 |
| 숙명여자대학교 | 117.0 | 공백 |
| 덕성여자대학교 | 120.2 | 공백 |
| 서울여자대학교 | 117.2 | 공백 |
| 동덕여자대학교 | 101.3 | 공백 |
| 이화여자대학교 | 127.2 | 공백 |
| 한성대학교 | 118.6 | 공백 |
| 서경대학교 | 132.1 | 공백 |
| 광운대학교 | 119.6 | 공백 |
| 세종대학교 | 133.4 | 공백 |
| 숭실대학교 | 136.8 | 공백 |

원인 추정:

- `scripts/fetch_academyinfo_key_indicators.py`가 대학주요정보 endpoint 기준으로 candidate를 만들면서 `재학생충원율 = pd.NA`로 처리했다.
- 현재는 원자료 29번 파일이 확보되어 있으므로 병합 보강 가능하다.

### 권고

1. `student_recruitment_2026_candidate.csv`에 29번 원자료의 `재학생충원율` 병합.
2. key는 `학교코드 + 학교명 + 본분교명` 우선.
3. 분교 원자료명 `_(분교/제2캠퍼스)` 정규화.
4. `student_recruitment.source.json`, `student_recruitment.metadata.json`, processing report 추가.
5. 전체 결측 감지 contract test 추가.

판정: **high/blocker**

---

## 4.3 대학알리미 - 기숙사/강사료

### 기숙사

대상:

- `data/processed/dormitory_accommodation_status/dormitory_accommodation_status_v2_utf8.csv`
- `data/metadata/dormitory_accommodation_status_v2.source.json`

결과:

- 원본 XLSX 부재로 원자료 직접 대조는 불가.
- processed 내부 산식은 검증됨.
- 산식: `dormitory_capacity / enrolled_students * 100`
- 4,145행 전부 mismatch 0건.

2025 샘플:

| 학교 | 재학생 | 수용인원 | 수용률 | 재계산 |
|---|---:|---:|---:|---:|
| 성신여자대학교 | 9,761 | 993 | 10.2 | 10.2 |
| 숙명여자대학교 | 10,625 | 1,279 | 12.0 | 12.0 |
| 이화여자대학교 | 20,730 | 4,370 | 21.1 | 21.1 |
| 세종대학교 | 15,333 | 1,751 | 11.4 | 11.4 |
| 서울기독대학교 | 1,404 | 89 | 6.3 | 6.3 |

판정: **partial**

### 강사 강의료

대상:

- `data/processed/lecturer_pay/lecturer_pay_2023_2025_v2_1_utf8.csv`
- `data/metadata/lecturer_pay_v2_1.source.json`
- `utils/data_pipeline.py`

결과:

- 원본 XLSX 부재로 원자료 직접 대조는 불가.
- processed 구조와 loader 산식은 확인됨.
- 학교-연도별 단일 행이 아니라 지급단가 구간별 다중 행 구조.
- loader는 `시간당 단가 × 총 강의시간` 가중평균으로 학교별 강사료를 산출한다.

2025 가중평균 샘플:

| 학교 | 원자료 rows | 총 강의시간 | 가중평균 강사료 |
|---|---:|---:|---:|
| 성신여자대학교 | 7 | 25,634.1 | 54,439원 |
| 숙명여자대학교 | 4 | 23,294.2 | 53,231원 |
| 이화여자대학교 | 3 | 41,100.6 | 58,184원 |
| 세종대학교 | 1 | 18,056.0 | 54,000원 |
| 서울기독대학교 | 4 | 2,643.0 | 56,745원 |

주의:

- 단순 평균/단순 합계로 시각화하면 오류 가능.
- `lecturer_pay` processed에는 서울 사립 34개 중 `감리교신학대학교`가 없음. 원자료 부재인지 전처리 누락인지 확인 필요.
- TS 타입은 영문 컬럼을 기대하지만 CSV는 한글 컬럼을 유지한다. Python loader는 정상이나 프론트 타입과 불일치 가능성이 있음.

판정: **partial**

---

## 4.4 사학재정알리미/KASFO - 결산

### 검증 대상

- `data/raw/pending_manual/finance/*`
- `data/결산(22,23,24).csv`
- `utils/data_pipeline.py`

공식 URL:

- <https://uniarlimi.kasfo.or.kr/knowledge/data2Room>
- 2024 법인일반회계 및 교비회계 결산 게시물: <https://uniarlimi.kasfo.or.kr/knowledge/data2Room/35283?pageIdx=2>

### 대조 결과

| 항목 | 결과 |
|---|---:|
| 결산 CSV 총 행 수 | 1,870행 |
| KASFO ZIP 자금계산서 2022~2024 행 수 | 1,870행 |
| 학교명 구명칭 제거 후 key 매칭 | 1,866행 |
| key 불일치 | 4행 |

### 일치 사례

필수 비교대학 11개 및 위험/이상치 학교는 2024년 `법인`, `교비` 주요 금액이 대부분 raw와 일치했다.

| 학교 | 회계 | 2024 자금수입총계 data | raw | 판정 |
|---|---|---:|---:|---|
| 성신여자대학교 | 교비 | 134,245,899 | 134245899 | 일치 |
| 숙명여자대학교 | 교비 | 192,641,044 | 192641044 | 일치 |
| 이화여자대학교 | 교비 | 444,441,260 | 444441260 | 일치 |
| 숭실대학교 | 교비 | 251,855,891 | 251855891 | 일치 |
| 강서대학교 | 교비 | 19,334,077 | 19334077 | 일치 |
| 서울한영대학교 | 교비 | 7,317,043 | 7317043 | 일치 |
| 영산선학대학교 | 교비 | 1,461,424 | 1461424 | 일치 |
| 칼빈대학교 | 교비 | 20,705,144 | 20705144 | 일치 |

### 불일치/주의 사례

| 유형 | 사례 | 원인 추정 | severity |
|---|---|---|---:|
| 구명칭 학교명 | `강서대학교(구.케이씨대학교)`, `서울한영대학교(구.한영신학대학교)` | 학교명 alias/구명칭 정규화 필요 | medium |
| 법인명 변경/불일치 | 대신대학교 2024: data는 `대구신학원`, raw는 `대신대학교` | 원자료/가공본 기준 시점 차이 가능 | medium |
| 누락/대체 학교 | data `영남사이버대학교` vs raw `태재대학교` 2023 | 원자료 교체 또는 병합 오류 가능성 | high |
| 계정 누락 | 2022년 다수 학교 `5.기타국고지원[1514]` data 공백, raw 값 존재 | 컬럼 추가/후행 컬럼 처리 누락 가능성 | high |
| 음수 부호 | 서울한영대학교, 세종대학교 등 미사용 이월자금 음수 | data와 raw ZIP 부호 표현 차이 | high |

비교대학 영향:

- 성신여대: 2022 기타국고지원 누락 1건.
- 숙명여대: 음수 이월자금 부호 차이.
- 덕성/서울/동덕/이화/한성/서경/광운/숭실: 2022 기타국고지원 누락.
- 세종대: 2022 음수 이월자금 부호 차이 + 기타국고지원 누락.

### 권고

1. 결산 CSV 전처리 규칙 문서화.
   - `strip()`
   - 쉼표 제거
   - `-` 결측/0 처리
   - 음수 부호 유지
   - 법인/교비 회계 필터 명시
2. 2022년 `5.기타국고지원[1514]` 누락 원인 확인.
3. 음수 이월자금 부호 차이 검증.
4. 학교명/법인명 alias table 적용.
5. raw finance와 processed 결산 CSV의 row/value contract test 추가.

판정: **partial with high-risk issues**

---

## 4.5 사학재정알리미/KASFO - 교육비 환원율

대상:

- `data/processed/education_cost_return_rate/education_cost_return_rate_2020_2025_v2_schema_utf8.csv`
- `data/metadata/education_cost_return_rate.source.json`

결과:

- 1,975행.
- 산식 재계산은 전 행 일치.
- 산식: `(tuition_account_total + industry_account_total) / tuition_revenue * 100`
- `source_file_name`: 전 행 공백.
- `education_cost_return_rate_original_pct`: 전 행 공백.
- 원본 XLSX가 repo에 없음.

중요 판단:

- 시스템 산식 검증은 가능하다.
- 그러나 KASFO 원자료 비율과 직접 일치한다고 선언할 수 없다.
- 영산선학대학교 2024년 1857.6%는 `tuition_revenue=67,000` 대비 교육비가 커서 생긴 분모효과로 판단된다.

권고:

1. 교육비 환원율 원본 XLSX 복원.
2. `source_file_name` 채우기.
3. 원자료 비율 컬럼 복원 또는 “재계산 전용 지표”로 명시.
4. 분모 0 또는 극소 분모 outlier 플래그 추가.

판정: **partial**

---

## 4.6 법정부담금

대상:

- `data/법정부담금_부담율.csv`
- 루트 `14-ba-2.-beobjeongbudamgeum-...csv`

결과:

- 475행 의미상 일치.
- 차이는 학교코드 leading zero와 숫자 표현 차이뿐.
  - 예: `0000136` vs `136`
  - 예: `1448` vs `1448.0`
- 산식: `법정부담금부담액 / 법정부담금기준액 * 100`

주의:

- `공시연도 2025 = 기준년도 2024` 구조다.
- 시각화/검증에서 기준년도와 공시연도를 혼동하면 1년 밀린다.
- 학교코드는 7자리 문자열로 보존해야 한다.

권고:

1. 학교코드 `str.zfill(7)` 적용.
2. source/schema/report metadata 보강.
3. 공시연도/기준년도 차이 명시.

판정: **verified with metadata gaps**

---

## 4.7 KCUE vs KASFO 법인전입금 비율

현재 대시보드의 KCUE `corporate_transfer_ratio`는 평가용 2차 집계 지표다.

반면 KASFO 결산 CSV는 계정 단위 원장성 자료다. `전입금수입`, `법정부담전입금`, `경상비전입금`, `자산전입금` 등 어떤 계정을 분자로 삼는지에 따라 값이 달라진다. 회계도 `법인`/`교비`가 섞여 있어 필터가 필수다.

따라서 KCUE 지표값과 KASFO 결산 직접 계산값을 같은 지표로 단정하면 안 된다.

권고:

- KCUE 법인전입금 비율은 KCUE processed 값을 기준으로 사용.
- KASFO 결산은 원장성 참고/검산용으로 별도 표시.
- 만약 KASFO 기반 지표를 신규 구현하려면 산식 정의를 별도 확정해야 한다.

판정: **partial / conceptual mismatch risk**

---

## 4.8 RINFO 학술정보통계

대상:

- `data/processed/library_staff_per_1000_students/library_staff_per_1000_students_2008_2025_v6_utf8.csv`
- `data/processed/library_material_purchase_per_student/library_material_purchase_per_student_2008_2025_v2_utf8.csv`
- 관련 metadata/schema/guide

### 도서관 직원 수

- 2008~2025, 8,215행.
- 산식 재현 가능.
- 산식: `가중직원수 / 재학생수 * 1000`
- `library_staff_per_1000_students_recalculated`에 literal `inf` 94건.
- `enrolled_students = 0` 행 923건.

### 자료구입비

- 2008~2025, 8,226행.
- 산식 재현 가능.
- 산식: `total_material_purchase_expense / enrolled_students_current_year`
- 전체 mismatch 81건. 대부분 `enrolled_students_current_year = 0`으로 인한 `inf`.
- `other_electronic_resources_expense == total_material_purchase_expense`가 전 행 True.
  - 세부 컬럼 매핑 오류 가능성이 높다.

### 원자료 대조 한계

- 원본 RINFO xls/xlsx 파일이 repo에 없어 원자료 직접 대조 제한.
- README에는 원본 파일명만 남아 있음.

### scope 위험

RINFO 로딩 파이프라인이 `seoul_private_four_year_universities.json`의 34개 scope를 직접 쓰지 않고 단순 `서울/사립/대학` 조건만 쓰면 42개까지 포함될 수 있다.

추가 포함 위험:

- 고려사이버대학교
- 디지털서울문화예술대학교
- 명지대학교
- 서울디지털대학교
- 서울사이버대학교
- 숭실사이버대학교
- 태재대학교
- 한국열린사이버대학교

권고:

1. 원본 RINFO xls/xlsx 복원.
2. `inf`를 `null` 또는 산출불가로 처리.
3. 자료구입비 세부 컬럼 매핑 재검증.
4. RINFO loader에 scope manifest 기반 필터 적용.
5. processing report 추가.

판정: **partial with high-risk issues**

---

## 5. 학교명/학교코드/캠퍼스 매칭 감사

### 5.1 현재 scope 상태

파일:

- `data/metadata/analysis_scopes/seoul_private_four_year_universities.json`

상태:

- 서울 사립 4년제 본교 scope 34개 정의됨.
- `school_id`, `rep_school_id`는 모두 7자리 zero-padding 유지.
- 현재 alias group은 2개.
  - 강서대학교 ← 그리스도대학교, 케이씨대학교
  - 서울한영대학교 ← 한영신학대학교

비교대학 설정:

- `.streamlit/comparison_profile.local.json`
- 비교대학 11개는 모두 canonical exact name으로 저장되어 있음.

### 5.2 processed DB scope 유지

- 대부분 processed CSV에서 34개 scope 학교가 exact name으로 존재.
- 예외:
  - `data/processed/lecturer_pay/lecturer_pay_2023_2025_v2_1_utf8.csv`: 33/34, `감리교신학대학교` 없음.
  - legacy 샘플 `data/전임교원_논문실적.csv`, `data/전임교원 논문실적(샘플).csv`: 3/34만 존재.

### 5.3 위험 매트릭스

| 그룹 | 원자료/DB 표기 | 위험 |
|---|---|---:|
| 비교대학 11개 | canonical exact name | 낮음 |
| 강서대학교 | `강서대학교`, `케이씨대학교`, `그리스도대학교`, `강서대학교(구.케이씨대학교)` | 높음 |
| 서울한영대학교 | `서울한영대학교`, `한영신학대학교`, `서울한영대학교(구.한영신학대학교)`, `한영대학교`, `한영대학` | 높음 |
| 건국대학교 | `건국대학교`, `건국대학교(글로컬)`, `건국대학교(충주)`, `건국대학교 분교1`, `건국대학교(글로컬)_분교` | 매우 높음 |
| 고려대학교 | `고려대학교`, `고려대학교(세종)`, `고려대학교 세종캠퍼스` | 매우 높음 |
| 동국대학교 | `동국대학교`, `동국대학교(WISE)`, `동국대학교(경주)`, `동국대학교 WISE캠퍼스` | 매우 높음 |
| 연세대학교 | `연세대학교`, `연세대학교(미래)`, `연세대학교(원주)`, `연세대학교 미래캠퍼스` | 매우 높음 |
| 한양대학교 | `한양대학교`, `한양대학교(ERICA)`, `한양대학교 분교1`, `한양대학교(ERICA)_분교` | 매우 높음 |
| 가톨릭대학교 | `가톨릭대학교`, `대전가톨릭대학교`, `대구가톨릭대학교`, `부산가톨릭대학교`, `수원가톨릭대학교` 등 | 매우 높음 |

### 5.4 alias table 추가 대상

강서대학교:

- 그리스도대학교
- 케이씨대학교
- 강서대학교(구.케이씨대학교)

서울한영대학교:

- 한영신학대학교
- 서울한영대학교(구.한영신학대학교)
- 한영대학교
- 한영대학

### 5.5 절대 병합 금지 대상

아래는 alias로 합치면 안 된다. 별도 캠퍼스/분교 개체로 유지해야 한다.

- 건국대학교(글로컬), 건국대학교(충주)
- 고려대학교(세종), 고려대학교 세종캠퍼스
- 동국대학교(WISE), 동국대학교(경주), 동국대학교 WISE캠퍼스
- 연세대학교(미래), 연세대학교(원주), 연세대학교 미래캠퍼스
- 한양대학교(ERICA)

### 5.6 금지해야 할 매칭 방식

절대 금지:

- `name.contains("가톨릭대학교")`
- 괄호 제거 후 비교
  - `건국대학교(글로컬)` → `건국대학교`
  - `고려대학교(세종)` → `고려대학교`
  - `동국대학교(WISE)` → `동국대학교`
  - `연세대학교(미래)` → `연세대학교`
  - `한양대학교(ERICA)` → `한양대학교`
- 캠퍼스 suffix 무조건 제거
  - `고려대학교 세종캠퍼스`
  - `동국대학교 WISE캠퍼스`
  - `연세대학교 미래캠퍼스`
  - `한양대학교(ERICA)_분교`

### 5.7 학교코드 처리

- canonical scope는 `0000136`처럼 7자리 유지.
- `student_recruitment`, `졸업생_취업률` 등 일부 modern processed는 7자리 유지.
- legacy CSV는 `136`, `79`, `205`처럼 leading zero가 소실됨.
- 모든 loader에서 학교코드/대표학교코드는 문자열 7자리로 보정해야 한다.

권고:

- `str.zfill(7)` 적용.
- `school_id`와 `rep_school_id`를 혼용하지 않도록 join key 명시.

---

## 6. SQLite/시스템 DB 상태

대상:

- `data/raw/pending_metrics.sqlite`

상태:

| table | row count |
|---|---:|
| `raw_sources` | 10 |
| `raw_records` | 489 |
| `metric_values` | 0 |

판단:

- 현재 SQLite는 운영 DB 일치성 검증 대상으로 보기 어렵다.
- `metric_values`가 0행이므로 최종 지표 DB로 사용 중이라고 보면 안 된다.
- `raw_records`는 `student_recruitment` 489행 중심이다.
- `raw_sources`는 대부분 planned/acquired 정보가 비어 있음.

권고:

1. `metric_values`가 비어 있는 DB를 운영 DB로 오인하지 않도록 contract test 추가.
2. `raw_sources → raw_records → metric_values` 연결성 테스트 추가.
3. 운영 DB가 CSV current asset인지 SQLite인지 구조를 명확히 문서화.

---

## 7. mismatch severity 기준

### blocker

- 원자료 파일 없음 + 출처/처리 경로도 불명.
- 학교/캠퍼스가 잘못 합쳐져 값이 다른 학교에 귀속됨.
- 운영 DB 최종값이 원자료/processed와 다르고 원인 설명 불가.
- 필수 지표가 전부 결측인데 정상 데이터로 표시됨.

### high

- 비교대학 11개 중 누락 발생.
- 서울 사립 4년제 scope가 지표별로 달라짐.
- 산식 불일치가 핵심 지표/최근연도에 발생.
- `inf`, 분모 0, 단위 변환 오류가 UI에 노출 가능.
- KASFO 결산 핵심 계정 누락 또는 음수 부호 오류 가능성.

### medium

- metadata/schema/report 일부 부재.
- 원자료는 없지만 processed 산식은 재현 가능.
- 구명칭 alias가 수동 확인 필요.
- 결측 사유가 문서화되지 않음.

### low

- 파일명 혼동 위험.
- README는 있으나 checksum 없음.
- 표시 라벨/출처 문구 보강 필요.
- 샘플 파일이 repo에 남아 있으나 current asset은 아님.

---

## 8. 현재 테스트 결과와 공백

관련 contract/unit test 40개 실행 결과는 모두 통과했다.

- 40 passed

그러나 현재 테스트는 다음을 충분히 보장하지 못한다.

- raw XLSX와 processed CSV의 행 단위 대조.
- source metadata의 raw file/checksum/download date 검증.
- 비교대학 11개가 모든 current asset에 존재하는지.
- 위험학교 alias/campus 오염 방지.
- `pending_metrics.sqlite`의 운영 DB 오인 방지.
- `student_recruitment` 재학생충원율 전체 결측 감지.
- `inf`가 UI에 노출되지 않는지.
- sample file이 current asset으로 쓰이지 않는지.

---

## 9. 추가해야 할 테스트

우선순위 높은 테스트:

1. `test_comparison_11_schools_present_in_all_current_assets`
2. `test_default_scope_34_schools_after_loader_filter`
3. `test_risk_school_aliases_do_not_merge_branch_campuses`
4. `test_konkuk_glocal_not_equal_konkuk_main`
5. `test_korea_sejong_not_equal_korea_main`
6. `test_gangseo_alias_group_maps_christian_kc_only_to_canonical`
7. `test_seoul_hanyoung_alias_group_maps_old_name`
8. `test_raw_files_declared_in_source_metadata_exist`
9. `test_processing_report_counts_match_processed_files`
10. `test_processed_formula_recalculation_real_data_sample`
11. `test_no_inf_or_literal_inf_in_display_metric_columns`
12. `test_pending_metrics_db_not_treated_as_operational_when_metric_values_empty`
13. `test_student_recruitment_candidate_all_missing_student_fill_rate_is_flagged`
14. `test_sample_files_not_used_as_current_assets`
15. `test_legacy_school_code_zfill_7_digits`
16. `test_no_partial_name_search_for_catholic_university`
17. `test_kasfo_2022_other_government_support_not_silently_blank`
18. `test_kasfo_negative_carryover_sign_preserved`

---

## 10. 수정 우선순위

### P0. 학교명/학교코드/캠퍼스 정규화 모듈

목표:

- exact → explicit alias → campus-aware mapping 순서로 안정적 매칭.
- 부분검색 금지.
- 괄호 제거 병합 금지.
- 학교코드/대표학교코드 7자리 문자열 보존.

구현 제안:

- `data/metadata/school_aliases.csv` 또는 JSON 추가.
- `utils/school_normalization.py` 추가.
- 필드 예시:
  - `canonical_school_name`
  - `alias`
  - `school_id`
  - `rep_school_id`
  - `valid_from_year`
  - `valid_to_year`
  - `match_type`
  - `campus_policy`
  - `scope_policy`

### P1. student_recruitment 재학생충원율 보강

목표:

- 원자료 29번의 `재학생충원율`을 candidate CSV에 병합.
- 전 행 공백 상태 해소.
- metadata/report 추가.

주의:

- 키는 `학교코드 + 학교명 + 본분교명` 우선.
- `가톨릭대학교`처럼 동일 학교명 다중 캠퍼스 존재.
- `건국대학교(글로컬)_분교` 같은 suffix 정규화 필요.

### P2. KASFO 결산 정합성 보강

목표:

- 2022년 `5.기타국고지원[1514]` 누락 확인.
- 음수 이월자금 부호 차이 확인.
- 구명칭/법인명 alias 처리.
- 전처리 규칙 문서화.

### P3. raw/metadata/report 보강

우선 대상:

- 기숙사 원본 XLSX
- 강사료 원본 XLSX
- 교육비 환원율 원본 XLSX
- RINFO 원본 xls/xlsx
- `student_recruitment` source/dataset metadata
- `budam`, `gyeolsan`, RINFO processing report

### P4. RINFO/분모 0/inf 처리

목표:

- `inf`를 UI 표시값에서 제거.
- 산출불가 플래그 부여.
- 자료구입비 세부 컬럼 매핑 재검증.
- RINFO loader에 34개 scope manifest 필터 적용.

### P5. SQLite/운영 DB 구조 정리

목표:

- 현재 운영 데이터 소스가 CSV current asset인지 SQLite인지 명확히 문서화.
- `metric_values` 0행 SQLite를 운영 DB로 오인하지 않게 테스트 추가.

---

## 11. 실행 제안

안전한 구현 순서는 다음과 같다.

1. 학교명/학교코드 정규화 모듈 + alias table + 테스트 추가.
2. `student_recruitment` 재학생충원율 병합 스크립트 또는 build script 수정.
3. `student_recruitment` source/dataset metadata 및 processing report 추가.
4. KASFO 결산의 2022 `기타국고지원[1514]` 누락/음수 부호 차이 원인 확인.
5. RINFO `inf` 처리와 scope 필터 적용.
6. raw 파일 보존/metadata/checksum 보강.
7. 원자료-processed-DB 일치성 contract test 추가.
8. 전체 pytest 실행 및 QA 보고서 갱신.

---

## 12. 결론

이번 감사 결과, 시스템 데이터의 핵심 기반은 다음처럼 평가된다.

- **KCUE 계열**: 원자료와 시스템 DB 일치성이 높아 신뢰 가능.
- **대학알리미 student_recruitment**: 일부 값은 일치하나 `재학생충원율` 전 행 공백으로 즉시 수정 필요.
- **KASFO 결산**: 주요 금액은 대체로 일치하나 일부 핵심 계정 누락/부호 차이로 보강 필요.
- **RINFO/기숙사/강사료/교육비 환원율**: 산식 검증은 가능하지만 원본 파일 부재로 partial 상태.
- **학교명/학교코드/scope**: 전체 시스템 안정성을 좌우하는 가장 중요한 구조적 리스크.

따라서 다음 구현의 첫 단계는 **학교명/학교코드/캠퍼스 정규화 체계 구축**이어야 한다. 그 다음 `student_recruitment` 재학생충원율 보강과 KASFO 결산 정합성 보강을 진행하는 것이 가장 안전하다.
