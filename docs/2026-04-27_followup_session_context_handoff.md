# 2026-04-27 후속 세션 인수인계 메모

## 현재 상태 요약

- 대상 프로젝트: `/Users/mortarteam81/Documents/Codex/2026-04-25/users-mortarteam81-visualization-14-ba-2/visualization_14_ba_2`
- 원격 저장소: `https://github.com/mortarteam81/visualization_14_ba_2.git`
- 현재 브랜치: `main`
- 현재 HEAD: `14dd3d3 Add adjunct faculty securing rate page`
- 현재 `main`은 `origin/main`과 동기화되어 있다.
- 남아 있는 미추적 파일: `docs/2026-04-27_kcue_metric_implementation_handoff.md`
- 이 파일은 이전 세션에서 만들어진 handoff 문서이며, 최근 두 번의 커밋에는 포함하지 않았다. 사용자가 명시적으로 요청하기 전에는 함부로 삭제하거나 커밋하지 말 것.

## 최근 완료된 작업

### 1. 교원확보율 원자료 패키지 구축

커밋: `bc33448 Add faculty securing rate data package`

2015~2025년 `교원확보율.xlsx` 원자료 11개를 표준 데이터 구조로 정리했다.

주요 산출물:

- 원자료: `data/raw/faculty_securing_rate/original/`
- 원자료 README: `data/raw/faculty_securing_rate/README.md`
- 상세 CSV: `data/processed/faculty_securing_rate/faculty_securing_rate_2015_2025_v1_utf8.csv`
- 업로드용 총계 CSV: `data/processed/faculty_securing_rate/faculty_securing_rate_total_2015_2025_v1_utf8.csv`
- Long metric CSV: `data/processed/faculty_securing_rate/faculty_securing_metric_values_2015_2025_v1_utf8.csv`
- 스키마: `data/metadata/faculty_securing_rate_v1_schema.md`
- 출처: `data/metadata/faculty_securing_rate_v1.source.json`
- 처리 리포트: `data/metadata/faculty_securing_rate_v1.processing_report.json`
- 재생성 스크립트: `scripts/build_faculty_securing_rate.py`

핵심 처리 로직:

- 각 XLSX는 1~3행 병합 다단 헤더, 4행부터 데이터 구조다.
- `계열구분`/`구분`, `초빙교원`/`초빙포함`, `편제`/`편제 정원` 표기 차이를 정규화했다.
- 시스템 업로드 기본 파일은 `field_category == "총계"`인 `faculty_securing_rate_total_2015_2025_v1_utf8.csv`다.
- `겸임교원확보율(편제정원) = 교원확보율(겸임포함)(편제정원) - 교원확보율(전임교원)(편제정원)`
- `겸임교원확보율(재학생) = 교원확보율(겸임포함)(재학생) - 교원확보율(전임교원)(재학생)`
- `겸임교원확보율(편제정원_최종) = min(겸임교원확보율(편제정원) * 0.3, 4.0)`
- `겸임교원확보율(재학생_최종) = min(겸임교원확보율(재학생) * 0.3, 4.0)`

검증 결과:

- 상세 CSV: 14,812행
- 총계 CSV: 2,116행
- Long CSV: 148,120행
- 파생 산식 mismatch: 0건
- `tests/contracts/test_raw_schema_inventory.py`: 6 passed

주의사항:

- `겸임교원확보율`은 원자료 직접 항목이 아니라 파생값이다. 원자료 공시값처럼 설명하면 안 된다.
- `4.0`은 인증 기준값이 아니라 최종 인정값의 상한이다.
- 2015년은 지역/설립구분 결측이 있다.
- 2018년은 학교코드 결측이 있다.
- 2016년은 하단에 빈 행 2개와 계열명만 있는 보조 행 7개가 있어 제외 처리했다.

### 2. 겸임교원 확보율 페이지 신설

커밋: `14dd3d3 Add adjunct faculty securing rate page`

기존 전임교원 확보율 페이지를 참고해 `겸임교원 확보율` 항목을 구현 완료 상태로 전환했다.

주요 변경 파일:

- 새 페이지: `pages/16_겸임교원_확보율.py`
- 지표 등록: `registry/metadata.py`
- pending 목록 조정: `registry/pending_metrics.py`
- raw schema 등록: `registry/raw_schemas.py`
- 설정 상수: `utils/config.py`
- 데이터 로더: `utils/data_pipeline.py`, `utils/data_loader.py`, `utils/query.py`
- 경영 인사이트 연결: `utils/management_insights.py`
- 테스트: `tests/contracts/test_pending_metric_plans.py`, `tests/unit/test_kcue_metric_pipeline.py`

구현 내용:

- `adjunct_faculty`를 `implemented=True`로 전환했다.
- 데이터 소스는 `processed/faculty_securing_rate/faculty_securing_rate_total_2015_2025_v1_utf8.csv`다.
- 표시 series는 두 개다.
  - `adjunct_faculty_quota_final`: `겸임교원확보율(편제정원_최종)`
  - `adjunct_faculty_enrolled_final`: `겸임교원확보율(재학생_최종)`
- 두 series 모두 threshold는 `4.0`, threshold label은 `최대 인정값`이다.
- 페이지에서는 라디오로 `편제정원 기준`과 `재학생 기준`을 전환한다.
- 4% 기준선은 “최대 인정값”으로 표시한다. “기준값 충족” 또는 “인증 기준”이라는 식으로 해석하면 안 된다.
- `adjunct_faculty`는 pending metric 목록에서 제거했다.
- 경영 인사이트 계산 목록에도 `adjunct_faculty_quota_final`, `adjunct_faculty_enrolled_final`을 추가했다.

검증 결과:

- 관련 테스트: 30 passed
- 전체 테스트: 249 passed, 1 warning
- Streamlit 페이지 smoke test에도 `pages/16_겸임교원_확보율.py`가 포함되어 통과했다.
- 확인용 Streamlit 서버는 마지막에 종료했다. 현재 8501 포트에는 서버가 떠 있지 않다.

## 반드시 지켜야 할 것

- 이 프로젝트에서 작업할 때는 `/Users/mortarteam81/Documents/Codex/2026-04-25/users-mortarteam81-visualization-14-ba-2/visualization_14_ba_2`를 기준으로 작업할 것.
- AGENTS.md 지침을 지킬 것. OpenClaw 관련 작업이면 `/Users/mortarteam81/.openclaw/shared/OPENCLAW_AGENTIC_PROFILE.md`, `/Users/mortarteam81/.openclaw/shared/CODEX_BRIDGE.md`를 읽고, Telegram token/OAuth/private memory/raw logs는 복사하지 말 것.
- 사용자가 커밋/푸시를 요청할 때만 커밋/푸시할 것.
- 커밋할 때는 관련 변경만 스테이징하고, 기존 미추적 파일이나 사용자가 만든 파일을 섞지 말 것.
- 새 지표를 구현할 때는 `registry/metadata.py`, `utils/config.py`, `utils/data_pipeline.py`, `utils/query.py`, `registry/raw_schemas.py`, 테스트를 함께 맞출 것.
- 구현 완료 지표로 바꾸면 `tests/contracts/test_raw_schema_inventory.py`, `tests/contracts/test_pending_metric_plans.py`, `tests/contracts/test_registry_data_contracts.py`가 함께 맞아야 한다.
- 페이지 UI는 기존 metric page 패턴을 따를 것. 특히 비교 그룹, heatmap, bump chart, AI analysis panel 패턴을 함부로 깨지 말 것.
- 데이터 해석 문구에서 `겸임교원 확보율`은 파생값이며, `4%`는 최대 인정값이라고 분명히 표현할 것.

## 반드시 하면 안 되는 것

- `git reset --hard`, `git checkout --`, 대량 삭제 등으로 사용자 변경을 되돌리지 말 것.
- 미추적 파일 `docs/2026-04-27_kcue_metric_implementation_handoff.md`를 사용자 요청 없이 삭제하거나 커밋하지 말 것.
- `.streamlit/secrets.toml`, OAuth 정보, API key, private log 등을 읽어 응답에 복사하거나 커밋하지 말 것.
- `겸임교원확보율(편제정원_최종)`과 `겸임교원확보율(재학생_최종)` 대신 원천 차이값 컬럼을 페이지 기본값으로 쓰지 말 것.
- 4% 기준선을 “인증 기준 충족선”으로 설명하지 말 것. 이 항목에서는 “최대 인정값 4%”다.
- 루트에 원자료 XLSX를 다시 방치하지 말 것. 원자료는 `data/raw/faculty_securing_rate/original/`에 위치해야 한다.
- Excel 임시 잠금 파일 `~$...xlsx`를 원자료나 커밋 대상에 포함하지 말 것.
- 기존 전임교원 확보율 `gyowon` 로더/페이지를 겸임교원 로직으로 덮어쓰지 말 것. 겸임교원은 별도 `adjunct_faculty` 항목이다.

## 다음 세션에서 유용한 명령

```bash
cd /Users/mortarteam81/Documents/Codex/2026-04-25/users-mortarteam81-visualization-14-ba-2/visualization_14_ba_2
git status --branch --short
git log --oneline --decorate -5
.venv/bin/python -m pytest
.venv/bin/streamlit run app.py --server.port 8501 --server.address 127.0.0.1
```

## 현재 git 상태

마지막 확인 기준:

```text
## main...origin/main
?? docs/2026-04-27_kcue_metric_implementation_handoff.md
```

즉, 코드와 데이터 변경은 `origin/main`에 반영되어 있고, 남은 것은 미추적 handoff 문서 하나뿐이다. 이 문서(`2026-04-27_followup_session_context_handoff.md`)를 만든 뒤에는 이 문서도 새 미추적 파일로 보일 수 있다.

## 후속 작업 후보

- 사용자가 원하면 이 handoff 문서들을 정리해서 커밋할 수 있다.
- 겸임교원 확보율 페이지의 문구나 시각화 기준은 현재 구현 완료됐으나, 사용자 검토 후 세부 표현을 조정할 수 있다.
- 다음 신규 지표를 추가할 때는 이번 `adjunct_faculty` 구현 방식을 참고하면 된다.
