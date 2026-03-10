"""
전임교원 1인당 연구비 — 서울 소재 사립대학교
교내 연구비 / 교외 연구비 탭 구성
"""

import plotly.express as px
import streamlit as st

from utils.chart_utils import add_threshold_hline, create_trend_line_chart
from utils.config import (
    APP_SUBTITLE,
    DATA_UPDATED,
    RESEARCH_COL_IN,
    RESEARCH_COL_OUT,
    RESEARCH_DEFAULT_SCHOOL,
    RESEARCH_PAGE_ICON,
    RESEARCH_PAGE_TITLE,
    RESEARCH_THRESHOLD_IN,
    RESEARCH_THRESHOLD_OUT,
)
from utils.data_loader import load_research_data

st.set_page_config(
    page_title=f"{RESEARCH_PAGE_TITLE} | 교육여건 지표",
    page_icon=RESEARCH_PAGE_ICON,
    layout="wide",
)

# ── 헤더 ─────────────────────────────────────────────────────────────────────
st.title(f"{RESEARCH_PAGE_ICON} {RESEARCH_PAGE_TITLE}")
st.caption(APP_SUBTITLE)

# ── 사이드바 ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔍 필터")

    include_branch = st.toggle(
        "분교 포함",
        value=False,
        help="가톨릭대 제2·3캠퍼스 등 분교 데이터를 포함합니다.",
    )

    st.divider()

# ── 데이터 로드 ───────────────────────────────────────────────────────────────
try:
    df = load_research_data(bonkyo_only=not include_branch)
except (FileNotFoundError, ValueError) as e:
    st.error(f"❌ 데이터 오류\n\n{e}")
    st.stop()

schools     = sorted(df["학교명"].unique())
years       = sorted(df["기준년도"].unique())
latest_year = max(years)

with st.sidebar:
    default_sel = (
        [RESEARCH_DEFAULT_SCHOOL]
        if RESEARCH_DEFAULT_SCHOOL in schools
        else schools[:1]
    )
    selected_schools = st.multiselect(
        "학교 선택",
        schools,
        default=default_sel,
        help=f"전체 {len(schools)}개 학교 중 선택",
    )
    st.caption(f"📅 기준일: {DATA_UPDATED}")
    st.caption(f"🏫 전체 학교 수: {len(schools)}개")
    st.caption(f"📆 수록 기간: {min(years)} ~ {latest_year}년")
    st.caption("💡 단위: 천원")

if not selected_schools:
    st.info("👈 사이드바에서 학교를 선택하세요.")
    st.stop()

# ── 필터링 ────────────────────────────────────────────────────────────────────
filtered_df = df[df["학교명"].isin(selected_schools)].copy()

if filtered_df.empty:
    st.error("선택된 학교에 데이터가 없습니다.")
    st.stop()

latest_df = filtered_df[filtered_df["기준년도"] == latest_year]

# ── 상단 KPI: 교내·교외 동시 표시 ────────────────────────────────────────────
st.markdown(f"#### {latest_year}년 현황 (단위: 천원)")

k1, k2, k3, k4, k5, k6 = st.columns(6)

# 교내
k1.metric(
    "교내 평균",
    f"{latest_df[RESEARCH_COL_IN].mean():,.0f}",
)
k2.metric(
    "교내 최고",
    f"{latest_df[RESEARCH_COL_IN].max():,.0f}",
    latest_df.loc[latest_df[RESEARCH_COL_IN].idxmax(), "학교명"],
    delta_color="off",
)
k3.metric(
    f"교내 {RESEARCH_THRESHOLD_IN:,.0f}천원↑ (인증 기준)",
    f"{(latest_df[RESEARCH_COL_IN] >= RESEARCH_THRESHOLD_IN).sum()} / {len(latest_df)}개",
)
# 교외
k4.metric(
    "교외 평균",
    f"{latest_df[RESEARCH_COL_OUT].mean():,.0f}",
)
k5.metric(
    "교외 최고",
    f"{latest_df[RESEARCH_COL_OUT].max():,.0f}",
    latest_df.loc[latest_df[RESEARCH_COL_OUT].idxmax(), "학교명"],
    delta_color="off",
)
k6.metric(
    f"교외 {RESEARCH_THRESHOLD_OUT:,.0f}천원↑ (인증 기준)",
    f"{(latest_df[RESEARCH_COL_OUT] >= RESEARCH_THRESHOLD_OUT).sum()} / {len(latest_df)}개",
)

st.divider()

# ── 탭: 교내 / 교외 / 비교(단일 학교) ────────────────────────────────────────
tabs = ["📘 교내 연구비", "📗 교외 연구비"]
if len(selected_schools) == 1:
    tabs.append("📊 교내·교외 비교")

tab_list = st.tabs(tabs)

# ════════════════════════════════════════════════════════════════════════════
# 탭 1 — 교내 연구비
# ════════════════════════════════════════════════════════════════════════════
with tab_list[0]:
    col_chart, col_stats = st.columns([2, 1])

    with col_chart:
        st.subheader(f"전임교원 1인당 교내 연구비 추이 (단위: 천원)")
        fig_in = create_trend_line_chart(
            filtered_df,
            x="기준년도",
            y=RESEARCH_COL_IN,
            color="학교명",
            title=f"선택 학교 ({len(selected_schools)}개) 교내 연구비 변화",
            x_label="기준연도",
            y_label="1인당 교내 연구비 (천원)",
        )
        fig_in = add_threshold_hline(
            fig_in,
            threshold=RESEARCH_THRESHOLD_IN,
            label=f"{RESEARCH_THRESHOLD_IN:,.0f}천원 기준선 (4주기 인증)",
        )
        st.plotly_chart(fig_in, use_container_width=True)

    with col_stats:
        st.subheader("연도별 통계")
        stats_in = (
            filtered_df
            .groupby("기준년도")[RESEARCH_COL_IN]
            .agg(평균="mean", 최고="max", 최저="min", 학교수="count")
            .round(1)
        )
        st.dataframe(stats_in, use_container_width=True)

    with st.expander("📊 연도 × 학교 교차표"):
        pivot_in = (
            filtered_df
            .pivot(index="기준년도", columns="학교명", values=RESEARCH_COL_IN)
            .round(1)
        )
        st.dataframe(pivot_in, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# 탭 2 — 교외 연구비
# ════════════════════════════════════════════════════════════════════════════
with tab_list[1]:
    col_chart2, col_stats2 = st.columns([2, 1])

    with col_chart2:
        st.subheader("전임교원 1인당 교외 연구비 추이 (단위: 천원)")
        fig_out = create_trend_line_chart(
            filtered_df,
            x="기준년도",
            y=RESEARCH_COL_OUT,
            color="학교명",
            title=f"선택 학교 ({len(selected_schools)}개) 교외 연구비 변화",
            x_label="기준연도",
            y_label="1인당 교외 연구비 (천원)",
        )
        fig_out = add_threshold_hline(
            fig_out,
            threshold=RESEARCH_THRESHOLD_OUT,
            label=f"{RESEARCH_THRESHOLD_OUT:,.0f}천원 기준선 (4주기 인증)",
        )
        st.plotly_chart(fig_out, use_container_width=True)

    with col_stats2:
        st.subheader("연도별 통계")
        stats_out = (
            filtered_df
            .groupby("기준년도")[RESEARCH_COL_OUT]
            .agg(평균="mean", 최고="max", 최저="min", 학교수="count")
            .round(1)
        )
        st.dataframe(stats_out, use_container_width=True)

    with st.expander("📊 연도 × 학교 교차표"):
        pivot_out = (
            filtered_df
            .pivot(index="기준년도", columns="학교명", values=RESEARCH_COL_OUT)
            .round(1)
        )
        st.dataframe(pivot_out, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# 탭 3 — 교내·교외 비교 (학교 1개 선택 시만 표시)
# ════════════════════════════════════════════════════════════════════════════
if len(selected_schools) == 1:
    with tab_list[2]:
        school_name = selected_schools[0]
        single_df = filtered_df.copy()

        st.subheader(f"{school_name} — 교내·교외 연구비 비교 (단위: 천원)")

        # 두 지표를 long 형태로 변환
        compare_melt = single_df.melt(
            id_vars="기준년도",
            value_vars=[RESEARCH_COL_IN, RESEARCH_COL_OUT],
            var_name="구분",
            value_name="연구비 (천원)",
        )
        compare_melt["구분"] = compare_melt["구분"].map({
            RESEARCH_COL_IN:  "교내 연구비",
            RESEARCH_COL_OUT: "교외 연구비",
        })

        fig_cmp = px.line(
            compare_melt,
            x="기준년도",
            y="연구비 (천원)",
            color="구분",
            markers=True,
            template="plotly_white",
            title=f"{school_name} 교내·교외 연구비 추이",
            color_discrete_map={
                "교내 연구비": "#1f77b4",
                "교외 연구비": "#ff7f0e",
            },
        )
        # 각 기준선을 색 구분하여 추가
        fig_cmp.add_hline(
            y=RESEARCH_THRESHOLD_IN,
            line_dash="dot",
            line_color="#1f77b4",
            annotation_text=f"교내 기준 {RESEARCH_THRESHOLD_IN:,.0f}천원",
            annotation_position="bottom right",
        )
        fig_cmp.add_hline(
            y=RESEARCH_THRESHOLD_OUT,
            line_dash="dash",
            line_color="#ff7f0e",
            annotation_text=f"교외 기준 {RESEARCH_THRESHOLD_OUT:,.0f}천원",
            annotation_position="top right",
        )
        fig_cmp.update_layout(hovermode="x unified", height=460)
        st.plotly_chart(fig_cmp, use_container_width=True)

        # 최근 5년 수치 테이블
        recent = single_df.sort_values("기준년도", ascending=False).head(5)
        recent_display = recent[["기준년도", RESEARCH_COL_IN, RESEARCH_COL_OUT]].copy()
        recent_display.columns = ["기준년도", "교내 (천원)", "교외 (천원)"]
        st.dataframe(
            recent_display.style.format({"교내 (천원)": "{:,.1f}", "교외 (천원)": "{:,.1f}"}),
            use_container_width=True,
            hide_index=True,
        )

# ── 지표 설명 ─────────────────────────────────────────────────────────────────
with st.expander("ℹ️ 지표 설명"):
    st.markdown(f"""
| 항목 | 교내 연구비 | 교외 연구비 |
|------|------------|------------|
| **산식** | 교내연구비 합계 ÷ 전임교원수 | 교외연구비 합계 ÷ 전임교원수 |
| **4주기 인증 기준** | **{RESEARCH_THRESHOLD_IN:,.0f}천원 이상** | **{RESEARCH_THRESHOLD_OUT:,.0f}천원 이상** |
| **단위** | 천원 | 천원 |

| 공통 항목 | 내용 |
|----------|------|
| **출처** | 대학알리미 공시자료 (서울 소재 사립대학교) |
| **기준년도** | 실제 기준년도 (공시연도 − 1) |
| **분교 처리** | 기본값: 본교만 / 사이드바 토글로 분교 포함 가능 |
| **데이터 기준일** | {DATA_UPDATED} |
""")

st.markdown("---")
st.caption(f"📈 데이터 출처: 대학알리미 | 기준일: {DATA_UPDATED}")
