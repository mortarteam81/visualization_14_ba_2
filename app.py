"""
서울 소재 사립대학교 교육여건 지표 시각화 — 홈 페이지
사이드바에서 지표별 페이지로 이동하세요.
"""

import streamlit as st
from utils.config import (
    APP_ICON, APP_SUBTITLE, APP_TITLE, DATA_UPDATED,
    RESEARCH_THRESHOLD_IN, RESEARCH_THRESHOLD_OUT,
    PAPER_THRESHOLD_JAEJI, PAPER_THRESHOLD_SCI,
    JIROSUNG_THRESHOLD,
    TUITION_THRESHOLD,
    DONATION_THRESHOLD,
)

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
)

st.title(f"{APP_ICON} {APP_TITLE}")
st.caption(APP_SUBTITLE)
st.divider()

st.markdown("#### 📋 수록 지표")

col1, col2 = st.columns(2)
col3, col4 = st.columns(2)
col5, col6 = st.columns(2)
col7, col8 = st.columns(2)

with col1:
    st.info(
        "**🛡️ 법정부담금 부담율**\n\n"
        "설립자가 법정기준액 대비 실제 부담한 비율\n\n"
        "4주기 인증 기준: **10% 이상**"
    )

with col2:
    st.info(
        "**👨‍🏫 전임교원 확보율**\n\n"
        "법정기준 교원 수 대비 실제 전임교원 수의 비율\n\n"
        "4주기 인증 기준: **61% 이상** (학생정원 기준)"
    )

with col3:
    st.info(
        "**🔬 전임교원 1인당 연구비**\n\n"
        "전임교원 1인당 교내·교외 연구비 수혜 실적\n\n"
        f"4주기 인증 기준: 교내 **{RESEARCH_THRESHOLD_IN:,.0f}천원** / "
        f"교외 **{RESEARCH_THRESHOLD_OUT:,.0f}천원** 이상"
    )

with col4:
    st.info(
        "**📄 전임교원 1인당 논문실적**\n\n"
        "등재(후보지) 논문 및 SCI급/SCOPUS 국제 논문 실적\n\n"
        f"4주기 인증 기준: 등재 **{PAPER_THRESHOLD_JAEJI}편/인** / "
        f"SCI급 **{PAPER_THRESHOLD_SCI}편/인** *(확인 필요)*"
    )

with col5:
    st.info(
        "**🎓 졸업생 진로 성과**\n\n"
        "취업자·진학자 합산 비율 (입대자·취업불가능자 등 제외)\n\n"
        f"4주기 인증 기준: **{JIROSUNG_THRESHOLD:.0f}% 이상**"
    )

with col7:
    st.info(
        "**💰 세입 중 등록금 비율**\n\n"
        "교비 회계 운영수입 대비 등록금수입의 비율\n\n"
        f"4주기 인증 기준: **{TUITION_THRESHOLD:.0f}% 이하**"
    )

with col8:
    st.info(
        "**🤝 세입 중 기부금 비율**\n\n"
        "교비 회계 운영수입 대비 기부금수입의 비율\n\n"
        f"4주기 인증 기준: **{DONATION_THRESHOLD:.1f}% 이상**"
    )

st.divider()
st.markdown(
    f"📅 데이터 기준일: **{DATA_UPDATED}** | "
    "출처: [대학알리미](https://www.academyinfo.go.kr) | "
    "대상: 서울 소재 사립 4년제 대학교"
)
