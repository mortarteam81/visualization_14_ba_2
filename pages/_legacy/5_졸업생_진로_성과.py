"""
졸업생 진로 성과 — 서울 소재 사립대학교
"""

import streamlit as st

from utils.config import (
    APP_SUBTITLE,
    DATA_UPDATED,
    JIROSUNG_DEFAULT_SCHOOL,
    JIROSUNG_PAGE_ICON,
    JIROSUNG_PAGE_TITLE,
    JIROSUNG_THRESHOLD,
)
from utils.chart_utils import add_threshold_hline, create_trend_line_chart
from utils.data_loader import load_jirosung_data

st.set_page_config(
    page_title=f"{JIROSUNG_PAGE_TITLE} | 교육여건 지표",
    page_icon=JIROSUNG_PAGE_ICON,
    layout="wide",
)

# ── 헤더 ─────────────────────────────────────────────────────────────────────
st.title(f"{JIROSUNG_PAGE_ICON} {JIROSUNG_PAGE_TITLE}")
st.caption(APP_SUBTITLE)

# ── 사이드바: 필터 ───────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔍 필터")

    include_branch = st.toggle(
        "분교 포함",
        value=False,
        help="분교 데이터를 포함합니다.",
    )

    st.divider()

# ── 데이터 로드 ───────────────────────────────────────────────────────────────
try:
    df = load_jirosung_data(bonkyo_only=not include_branch)
except (FileNotFoundError, ValueError) as e:
    st.error(f"❌ 데이터 오류\n\n{e}")
    st.stop()

schools     = sorted(df["학교명"].unique())
years       = sorted(df["기준년도"].unique())
latest_year = max(years)

# ── 사이드바: 학교 선택 ───────────────────────────────────────────────────────
with st.sidebar:
    default_selection = (
        [JIROSUNG_DEFAULT_SCHOOL] if JIROSUNG_DEFAULT_SCHOOL in schools else schools[:1]
    )
    selected_schools = st.multiselect(
        "학교 선택",
        schools,
        default=default_selection,
        help=f"전체 {len(schools)}개 학교 중 선택",
    )

    st.caption(f"📅 기준일: {DATA_UPDATED}")
    st.caption(f"🏫 전체 학교 수: {len(schools)}개")
    st.caption(f"📆 수록 기간: {min(years)} ~ {latest_year}년")

if not selected_schools:
    st.info("👈 사이드바에서 학교를 선택하세요.")
    st.stop()

# ── 필터링 ────────────────────────────────────────────────────────────────────
filtered_df = df[df["학교명"].isin(selected_schools)].copy()

if filtered_df.empty:
    st.error("선택된 학교에 데이터가 없습니다.")
    st.stop()

# 최신 연도 KPI
latest_df   = filtered_df[filtered_df["기준년도"] == latest_year]
above_count = (latest_df["졸업생_진로_성과"] >= JIROSUNG_THRESHOLD).sum()
total_count = len(latest_df)
idx_max     = latest_df["졸업생_진로_성과"].idxmax()
idx_min     = latest_df["졸업생_진로_성과"].idxmin()

# ── KPI 메트릭 ────────────────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)

m1.metric(f"{latest_year}년 선택교 평균", f"{latest_df['졸업생_진로_성과'].mean():.1f}%")
m2.metric(
    "최고 진로 성과율",
    f"{latest_df['졸업생_진로_성과'].max():.1f}%",
    latest_df.loc[idx_max, "학교명"],
    delta_color="off",
)
m3.metric(
    "최저 진로 성과율",
    f"{latest_df['졸업생_진로_성과'].min():.1f}%",
    latest_df.loc[idx_min, "학교명"],
    delta_color="off",
)
m4.metric(
    f"{JIROSUNG_THRESHOLD}% 이상 (인증 기준 충족)",
    f"{above_count} / {total_count}개",
    help=f"{latest_year}년 기준, 학교 단위 집계",
)

st.divider()

# ── 메인 시각화 ───────────────────────────────────────────────────────────────
col_chart, col_stats = st.columns([2, 1])

with col_chart:
    st.subheader("졸업생 진로 성과 연도별 추이")

    fig = create_trend_line_chart(
        filtered_df,
        x="기준년도",
        y="졸업생_진로_성과",
        color="학교명",
        title=f"선택 학교 ({len(selected_schools)}개) 졸업생 진로 성과 변화",
        x_label="기준연도",
        y_label="진로 성과율 (%)",
    )
    fig = add_threshold_hline(
        fig,
        threshold=JIROSUNG_THRESHOLD,
        label=f"{JIROSUNG_THRESHOLD}% 기준선 (4주기 인증)",
    )
    st.plotly_chart(fig, use_container_width=True)

with col_stats:
    st.subheader("연도별 통계")

    yearly_stats = (
        filtered_df
        .groupby("기준년도")["졸업생_진로_성과"]
        .agg(평균="mean", 최고="max", 최저="min", 학교수="count")
        .round(1)
    )
    st.dataframe(yearly_stats, use_container_width=True)

# ── 하단 확장 패널 ────────────────────────────────────────────────────────────
with st.expander("📊 연도 × 학교 교차표"):
    pivot = (
        filtered_df
        .pivot_table(index="기준년도", columns="학교명", values="졸업생_진로_성과", aggfunc="mean")
        .round(1)
    )
    st.dataframe(pivot, use_container_width=True)

with st.expander("ℹ️ 지표 설명"):
    st.markdown(f"""
| 항목 | 내용 |
|------|------|
| **출처** | 대학알리미 공시자료 (서울 소재 사립대학교) |
| **기준년도** | 실제 기준년도 (공시연도 − 1) |
| **산식** | (취업자 + 진학자) ÷ (졸업자 − (입대자 + 취업불가능자 + 외국인유학생 + 건강보험직장가입제외대상)) × 100 (%) |
| **4주기 인증 기준** | **{JIROSUNG_THRESHOLD}% 이상** |
| **분교 처리** | 기본값: 본교만 표시 / 사이드바에서 분교 포함 선택 가능 |
| **데이터 기준일** | {DATA_UPDATED} |
""")

st.markdown("---")
st.caption(f"📈 데이터 출처: 대학알리미 | 기준일: {DATA_UPDATED}")
