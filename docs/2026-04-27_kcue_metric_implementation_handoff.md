# KCUE 기반 지표 구현 작업 인수인계

작성일: 2026-04-27

## 현재 상태

- 프로젝트: `visualization_14_ba_2`
- 앱 성격: Streamlit 기반 대학 경영 인사이트 대시보드
- 현재 브랜치: `main`
- 현재 원격 동기화 상태: `main`과 `origin/main` 동기화 완료
- 최신 커밋: `39ab790 Implement corporate transfer ratio metric`
- 직전 주요 커밋:
  - `d7f421a Implement scholarship ratio metric`
  - `d8cba91 Add staff per student threshold`
  - `d09d75b Implement staff per student metric`
  - `3addf30 Add KCUE university indicator dataset`
  - `f9dc30e Add runtime dependency guidance`

## 관련 선행 문서

- `docs/2026-04-26_auth_neon_handoff.md`
  - Google OIDC, Neon DB, 권한 모델, Streamlit Cloud 배포 주의사항 정리
- `docs/2026-04-27_kcue_university_indicators_handoff.md`
  - 한국대학평가원 대학현황지표 원본/가공 CSV/long CSV/메타데이터/재생성 스크립트 정리

## 이번 세션에서 완료한 작업

### 1. KCUE 산출물 커밋 및 푸쉬

- 한국대학평가원 대학현황지표 원본/가공 산출물을 커밋하고 GitHub `main`에 푸쉬했다.
- 커밋: `3addf30 Add KCUE university indicator dataset`
- 포함 범위:
  - `data/raw/kcue_university_indicators/`
  - `data/processed/kcue_university_indicators/`
  - `data/metadata/kcue_university_indicators_v1.*`
  - `scripts/build_kcue_university_indicators.py`
  - `docs/2026-04-27_kcue_university_indicators_handoff.md`
  - `requirements.txt`의 `openpyxl`
  - `registry/raw_schemas.py` allowlist 조정

### 2. 직원 1인당 학생수 구현

- 커밋:
  - `d09d75b Implement staff per student metric`
  - `d8cba91 Add staff per student threshold`
- 데이터:
  - KCUE long CSV의 `students_per_staff`
  - 파일: `data/processed/kcue_university_indicators/kcue_university_metric_values_2015_2025_v1_utf8.csv`
- 페이지:
  - `pages/13_직원_1인당_학생수.py`
- 기준값:
  - `70명 이하`
- 해석 방향:
  - 낮을수록 좋음
- 처리 내용:
  - `registry/metadata.py`에서 구현 완료 지표로 전환
  - `utils/data_pipeline.py`에 KCUE 공통 long CSV 로더와 `prepare_staff_per_student_frame()` 추가
  - `utils/query.py`, `utils/data_loader.py`, `utils/config.py` 연결
  - `registry/raw_schemas.py`에 구현 지표 스키마 등록
  - `registry/pending_metrics.py`, `tests/contracts/test_pending_metric_plans.py`에서 pending 제외
  - `utils/management_insights.py`에 교육여건 지표로 포함, lower-is-better 반영

### 3. 장학금 비율 구현

- 커밋: `d7f421a Implement scholarship ratio metric`
- 데이터:
  - KCUE long CSV의 `scholarship_ratio`
- 페이지:
  - `pages/14_장학금_비율.py`
- 기준값:
  - `12% 이상`
- 해석 방향:
  - 높을수록 좋음
- 처리 내용:
  - 구현 완료 지표로 전환
  - `prepare_scholarship_ratio_frame()` 및 loader/query/config 연결
  - raw schema 등록
  - pending 목록과 pending source acquisition 목록에서 제거
  - 경영 인사이트의 `재정` 그룹 지표로 포함

### 4. 세입 중 법인전입금 비율 구현

- 커밋: `39ab790 Implement corporate transfer ratio metric`
- 데이터:
  - KCUE long CSV의 `corporate_transfer_ratio`
- 페이지:
  - `pages/15_세입_중_법인전입금_비율.py`
- 기준값:
  - `0.4% 이상`
- 해석 방향:
  - 높을수록 좋음
- 처리 내용:
  - 구현 완료 지표로 전환
  - `prepare_corp_transfer_ratio_frame()` 및 loader/query/config 연결
  - raw schema 등록
  - pending 목록과 pending source acquisition 목록에서 제거
  - 경영 인사이트의 `재정` 그룹 지표로 포함

## 현재 구현된 KCUE 기반 신규 지표

| 지표 | KCUE metric_id | 페이지 | 기준값 | 방향 |
| --- | --- | --- | --- | --- |
| 직원 1인당 학생수 | `students_per_staff` | `pages/13_직원_1인당_학생수.py` | 70명 이하 | 낮을수록 좋음 |
| 장학금 비율 | `scholarship_ratio` | `pages/14_장학금_비율.py` | 12% 이상 | 높을수록 좋음 |
| 세입 중 법인전입금 비율 | `corporate_transfer_ratio` | `pages/15_세입_중_법인전입금_비율.py` | 0.4% 이상 | 높을수록 좋음 |

## 테스트 상태

마지막 전체 테스트:

```bash
.venv/bin/python -m pytest
```

결과:

- `238 passed, 1 warning`
- warning은 urllib3/OpenSSL 관련 기존 환경 경고다.

## 현재 로컬 실행 메모

- 권장 실행 명령:

```bash
cd /Users/mortarteam81/Documents/Codex/2026-04-25/users-mortarteam81-visualization-14-ba-2/visualization_14_ba_2
.venv/bin/streamlit run app.py
```

- 전역 `streamlit run app.py`를 사용하면 `/opt/homebrew/bin/streamlit` 전역 환경을 탈 수 있다.
- 전역 환경에는 필요한 의존성이 없을 수 있으므로 프로젝트 `.venv/bin/streamlit` 사용이 안전하다.
- 이번 세션 중 로컬 서버는 `http://localhost:8501`에서 확인했다.

## 다음 작업 후보

### 추천 1순위: 학생 충원율 계열

KCUE long CSV에 다년 데이터가 있는 항목:

- `freshman_fill_rate`
  - 정원내 신입생 충원율
  - 2015~2024
- `student_fill_rate`
  - 정원내 재학생 충원율
  - 2015~2024

주의:

- KCUE의 `student_recruitment_performance`는 2025년 단년 4주기 지표다.
- 사용자는 단년 지표는 제외하라고 했다.
- 따라서 다음 세션에서 학생 충원 관련 작업을 한다면 `student_recruitment_performance` 단년 지표가 아니라, 2015~2024의 `freshman_fill_rate`와 `student_fill_rate` 2개 시리즈 페이지로 설계하는 것이 좋다.
- 기준값은 아직 사용자가 명시하지 않았다. 구현 전 기준값을 확인하는 것이 좋다.

### 보류 후보

- `corp_finance_ratio`
  - KCUE에는 `corporate_finance_transfer_ratio`가 있으나 2025년 단년이다.
  - 사용자 지시상 단년 지표 제외.
- `adjunct_faculty`
  - KCUE에는 `adjunct_faculty_rate`가 있으나 2025년 단년이다.
  - 사용자 지시상 단년 지표 제외.
- `classroom_area`, `lab_area`, `lab_equipment`
  - 현재 KCUE 통합 산출물에 직접 구현 가능한 다년 metric_id가 없다.
  - 별도 1차 출처/정의 확정 필요.

## 반드시 지켜야 할 사항

1. 작업 시작 전 항상 `git status --short --branch`를 확인한다.
2. 기존 변경사항을 되돌리지 않는다. 사용자가 만든 변경이 있을 수 있으므로 무단 revert 금지.
3. 실제 OAuth secrets, Google client secret, cookie secret, Neon URL, 사용자 이메일 원문, raw logs, cookies, tokens는 프롬프트/문서/커밋에 포함하지 않는다.
4. `.streamlit/secrets.toml`과 `.streamlit/comparison_profile.local.json`은 Git에 포함하지 않는다.
5. OpenClaw 관련 작업이 나오면 먼저 아래 파일을 읽는다.
   - `/Users/mortarteam81/.openclaw/shared/OPENCLAW_AGENTIC_PROFILE.md`
   - `/Users/mortarteam81/.openclaw/shared/CODEX_BRIDGE.md`
6. Streamlit entrypoint를 추가하면 `st.set_page_config()` 직후 `require_authenticated_user()`를 호출해야 한다.
7. 새 구현 지표는 최소한 아래를 함께 맞춘다.
   - `registry/metadata.py`
   - `utils/config.py`
   - `utils/data_pipeline.py`
   - `utils/query.py`
   - `utils/data_loader.py`
   - `registry/raw_schemas.py`
   - pending 관련 registry/test 정리
   - `utils/management_insights.py`
   - page smoke test 통과
8. 새 페이지는 기존 비교군 UX 패턴을 유지한다.
   - `render_school_sidebar`
   - `build_group_definitions`
   - `build_chart_frame`
   - `render_single_metric_page`
   - focus chart, heatmap, bump chart
   - AI analysis panel
9. 기준값과 방향은 사용자가 알려준 값을 우선한다.
10. 구현 후 전체 테스트를 돌린다.

## 반드시 하지 말아야 할 사항

1. secrets, token, OAuth 값, Neon connection string, 사용자 이메일 원문을 문서나 커밋에 남기지 않는다.
2. GitHub에 민감정보가 들어갈 수 있는 로컬 파일을 stage하지 않는다.
3. 단년 지표를 사용자가 별도로 허용하기 전에는 구현하지 않는다.
4. KCUE 평가용 2차 집계 자료를 1차 공시 원자료와 동일하다고 단정하지 않는다.
5. 학교명 기반 데이터 매칭의 한계를 숨기지 않는다.
6. 전체 UI 패턴과 다른 임의의 새 디자인 패턴을 도입하지 않는다.
7. 전역 Streamlit 실행을 기본값으로 안내하지 않는다.
8. 테스트 실패 상태로 커밋/푸쉬하지 않는다.

## 다음 세션 시작 추천 순서

1. `git status --short --branch`
2. 이 문서와 아래 문서 2개 확인
   - `docs/2026-04-26_auth_neon_handoff.md`
   - `docs/2026-04-27_kcue_university_indicators_handoff.md`
3. 사용자가 다음 지표 기준값을 정했는지 확인
4. `student_recruitment`를 구현한다면 단년 `student_recruitment_performance`는 제외하고, `freshman_fill_rate`와 `student_fill_rate` 중심으로 설계
5. 구현 후 관련 테스트 먼저 실행
6. 전체 테스트 실행
7. 커밋/푸쉬 여부를 사용자와 맞춘다.
