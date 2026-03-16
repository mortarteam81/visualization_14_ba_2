"""
앱 전역 설정 및 상수 중앙 관리
- 기준값·임계치 등 변경이 필요한 값은 이 파일에서만 수정
- API 연동 설정은 .env 파일에서 관리 (이 파일에는 기본값만 기재)
"""

import os

# ── 앱 기본 정보 ─────────────────────────────────────────────────────────────
APP_TITLE    = "서울 소재 사립대학교 교육여건 지표 시각화"
APP_SUBTITLE = "대학알리미 공시자료 기반 대학기관평가인증 정량지표 추이 분석"
APP_ICON     = "🎓"
DATA_UPDATED = "2026-03-09"

# ── 법정부담금 부담율 ─────────────────────────────────────────────────────────
BUDAM_CSV            = "법정부담금_부담율.csv"
BUDAM_CSV_ENCODING   = "utf-8-sig"
BUDAM_THRESHOLD      = 10.0          # 4주기 인증 기준 (%)
BUDAM_DEFAULT_SCHOOL = "성신여자대학교"
BUDAM_PAGE_TITLE     = "법정부담금 부담율"
BUDAM_PAGE_ICON      = "🛡️"

# ── 전임교원 확보율 ───────────────────────────────────────────────────────────
GYOWON_CSV            = "전임교원_확보율.csv"
GYOWON_CSV_ENCODING   = "utf-8-sig"
GYOWON_THRESHOLD      = 61.0         # 4주기 인증 기준 (학생정원 기준, %)
GYOWON_DEFAULT_SCHOOL = "성신여자대학교"
GYOWON_PAGE_TITLE     = "전임교원 확보율"
GYOWON_PAGE_ICON      = "👨‍🏫"

# 전임교원 확보율 컬럼명 매핑
GYOWON_COL_JEONGWON   = "전임교원 확보율(학생정원 기준)"
GYOWON_COL_JAEHAK     = "전임교원 확보율(재학생 기준)"

# ── 연구비 수혜실적 ───────────────────────────────────────────────────────────
RESEARCH_CSV            = "연구비_수혜실적.csv"
RESEARCH_CSV_ENCODING   = "utf-8-sig"
RESEARCH_THRESHOLD_IN   = 1_000.0    # 교내 기준 (천원, 4주기 인증 기준)
RESEARCH_THRESHOLD_OUT  = 10_000.0   # 교외 기준 (천원, 4주기 인증 기준)
RESEARCH_DEFAULT_SCHOOL = "성신여자대학교"
RESEARCH_PAGE_TITLE     = "전임교원 1인당 연구비"
RESEARCH_PAGE_ICON      = "🔬"

# 연구비 컬럼명
RESEARCH_COL_IN         = "전임교원 1인당 연구비(교내)"
RESEARCH_COL_OUT        = "전임교원 1인당 연구비(교외)"

# ── 전임교원 1인당 논문실적 ──────────────────────────────────────────────────
PAPER_CSV            = "전임교원_논문실적.csv"
PAPER_CSV_ENCODING   = "utf-8-sig"
# TODO: 4주기 인증 기준값 확인 후 수정 필요, 처리완료(2026.3.10)
PAPER_THRESHOLD_JAEJI = 0.35          # 등재(후보지) 논문 기준 (편/인)
PAPER_THRESHOLD_SCI   = 0.05          # SCI급/SCOPUS 논문 기준 (편/인)
PAPER_DEFAULT_SCHOOL  = "성신여자대학교"
PAPER_PAGE_TITLE      = "전임교원 1인당 논문실적"
PAPER_PAGE_ICON       = "📄"

# 논문실적 컬럼명
PAPER_COL_JAEJI = "전임교원1인당논문실적(국내, 연구재단등재지(후보포함))"
PAPER_COL_SCI   = "전임교원1인당논문실적(국제, SCI급/SCOPUS학술지)"

# ── 졸업생 진로 성과 ─────────────────────────────────────────────────────────
JIROSUNG_CSV            = "졸업생_취업률.csv"
JIROSUNG_CSV_ENCODING   = "utf-8-sig"
JIROSUNG_THRESHOLD      = 55.0        # 4주기 인증 기준 (%)
JIROSUNG_DEFAULT_SCHOOL = "성신여자대학교"
JIROSUNG_PAGE_TITLE     = "졸업생 진로 성과"
JIROSUNG_PAGE_ICON      = "🎓"

# ── 세입 중 등록금 비율 ───────────────────────────────────────────────────────
GYEOLSAN_CSV             = "결산(22,23,24).csv"
GYEOLSAN_CSV_ENCODING    = "utf-8-sig"
TUITION_THRESHOLD        = 72.0          # 4주기 인증 기준 (%)
TUITION_DEFAULT_SCHOOL   = "성신여자대학교"
TUITION_PAGE_TITLE       = "세입 중 등록금 비율"
TUITION_PAGE_ICON        = "💰"

# ── 세입 중 기부금 비율 ───────────────────────────────────────────────────────
DONATION_THRESHOLD       = 0.4           # 4주기 인증 기준 (%)
DONATION_DEFAULT_SCHOOL  = "성신여자대학교"
DONATION_PAGE_TITLE      = "세입 중 기부금 비율"
DONATION_PAGE_ICON       = "🤝"

# ── 차트 공통 설정 ───────────────────────────────────────────────────────────
CHART_HEIGHT          = 500
CHART_THRESHOLD_COLOR = "red"
CHART_TEMPLATE        = "plotly_white"

# ── data.go.kr API 연동 설정 ─────────────────────────────────────────────────
# 실제 인증키와 데이터 소스 선택은 .env 파일에서 관리합니다.
# .env.example 파일을 복사하여 .env를 생성하고 값을 입력하세요.

# 데이터 소스: "csv" (기본값, 오프라인 가능) | "api" (실시간 data.go.kr 호출)
DATA_SOURCE: str = os.getenv("DATA_SOURCE", "csv")

# data.go.kr 인증키 (Encoding 또는 Decoding 키 중 하나)
# 보안상 이 파일에 직접 입력하지 말고 .env 파일에 입력하세요.
DATAGOKR_API_KEY: str = os.getenv("DATAGOKR_API_KEY", "")
