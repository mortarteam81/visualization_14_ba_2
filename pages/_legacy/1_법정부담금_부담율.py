"""
법정부담금 부담율 — 서울 소재 사립대학교
"""

import streamlit as st

from utils.config import (
    APP_SUBTITLE,
    BUDAM_DEFAULT_SCHOOL,
    BUDAM_PAGE_ICON,
    BUDAM_PAGE_TITLE,
    BUDAM_THRESHOLD,
    DATA_UPDATED,
)
from utils.chart_utils import add_threshold_hline, create_trend_line_chart
from utils.data_loader import load_budam_data

st.set_page_config(
    page_title=f"{BUDAM_PAGE_TITLE} | 교육여건 지표",
    page_icon=BUDAM_PAGE_ICON,
    layout="wide",
)

# ── 헤더 ─────────────────────────────────────────────────────────────────────
st.title(f"{BUDAM_PAGE_ICON} {BUDAM_PAGE_TITLE}")
st.caption(APP_SUBTITLE)

# ── 데이터 로드 ───────────────────────────────────────────────────────────────
try:
    df = load_budam_data()
except (FileNotFoundError, ValueError) as e:
    st.error(f"❌ 데이터 오류\n\n{e}")
    st.stop()

schools     = sorted(df["학교명"].unique())
years       = sorted(df["기준년도"].unique())
latest_year = max(years)

# ── 사이드바: 필터 ───────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔍 필터")

    default_selection = (
        [BUDAM_DEFAULT_SCHOOL] if BUDAM_DEFAULT_SCHOOL in schools else schools[:1]
    )
    selected_schools = st.multiselect(
        "학교 선택",
        schools,
        default=default_selection,
        help=f"전체 {len(schools)}개 학교 중 선택 (복수 선택 가능)",
    )

    st.divider()
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
above_count = (latest_df["부담율"] >= BUDAM_THRESHOLD).sum()
total_count = len(latest_df)
idx_max     = latest_df["부담율"].idxmax()
idx_min     = latest_df["부담율"].idxmin()

# ── KPI 메트릭 ────────────────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)

m1.metric(f"{latest_year}년 선택교 평균", f"{latest_df['부담율'].mean():.1f}%")
m2.metric(
    "최고 부담율",
    f"{latest_df['부담율'].max():.1f}%",
    latest_df.loc[idx_max, "학교명"],
    delta_color="off",
)
m3.metric(
    "최저 부담율",
    f"{latest_df['부담율'].min():.1f}%",
    latest_df.loc[idx_min, "학교명"],
    delta_color="off",
)
m4.metric(
    f"{BUDAM_THRESHOLD}% 이상 (인증 기준 충족)",
    f"{above_count} / {total_count}개",
    help=f"{latest_year}년 기준, 학교 단위 집계",
)

st.divider()

# ── 메인 시각화 ───────────────────────────────────────────────────────────────
col_chart, col_stats = st.columns([2, 1])

with col_chart:
    st.subheader("부담율 연도별 추이")

    fig = create_trend_line_chart(
        filtered_df,
        x="기준년도",
        y="부담율",
        color="학교명",
        title=f"선택 학교 ({len(selected_schools)}개) 법정부담금 부담율 변화",
        x_label="기준연도",
        y_label="부담율 (%)",
    )
    fig = add_threshold_hline(
        fig,
        threshold=BUDAM_THRESHOLD,
        label=f"{BUDAM_THRESHOLD}% 기준선 (4주기 인증)",
    )
    st.plotly_chart(fig, use_container_width=True)

with col_stats:
    st.subheader("연도별 통계")

    yearly_stats = (
        filtered_df
        .groupby("기준년도")["부담율"]
        .agg(평균="mean", 최고="max", 최저="min", 학교수="count")
        .round(1)
    )
    st.dataframe(yearly_stats, use_container_width=True)

# ── 하단 확장 패널 ────────────────────────────────────────────────────────────
with st.expander("📊 연도 × 학교 교차표"):
    pivot = (
        filtered_df
        .pivot_table(index="기준년도", columns="학교명", values="부담율", aggfunc="mean")
        .round(1)
    )
    st.dataframe(pivot, use_container_width=True)

with st.expander("ℹ️ 지표 설명"):
    st.markdown(f"""
| 항목 | 내용 |
|------|------|
| **출처** | 대학알리미 공시자료 (서울 소재 사립대학교) |
| **기준년도** | 실제 기준년도 (공시연도 − 1) |
| **산식** | 법정부담금부담액 ÷ 법정부담금기준액 × 100 (%) |
| **4주기 인증 기준** | **{BUDAM_THRESHOLD}% 이상** |
| **데이터 기준일** | {DATA_UPDATED} |
""")

st.markdown("---")
st.caption(f"📈 데이터 출처: 대학알리미 | 기준일: {DATA_UPDATED}")
