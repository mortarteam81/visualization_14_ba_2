"""
전임교원 1인당 논문실적 페이지
- 등재(후보지) 논문: 전임교원1인당논문실적(국내, 연구재단등재지(후보포함))
- SCI급/SCOPUS 논문: 전임교원1인당논문실적(국제, SCI급/SCOPUS학술지)
- 4주기 대학기관평가인증 정량지표
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.config import (
    APP_ICON,
    PAPER_COL_JAEJI,
    PAPER_COL_SCI,
    PAPER_DEFAULT_SCHOOL,
    PAPER_PAGE_ICON,
    PAPER_PAGE_TITLE,
    PAPER_THRESHOLD_JAEJI,
    PAPER_THRESHOLD_SCI,
)
from utils.chart_utils import add_threshold_hline, create_trend_line_chart
from utils.data_loader import load_paper_data

# ── 페이지 설정 ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=f"{PAPER_PAGE_TITLE} | 교육여건 지표",
    page_icon=PAPER_PAGE_ICON,
    layout="wide",
)

# ── 데이터 로딩 ───────────────────────────────────────────────────────────────
try:
    df_all  = load_paper_data(bonkyo_only=False)
    df_bon  = load_paper_data(bonkyo_only=True)
except (FileNotFoundError, ValueError) as e:
    st.error(f"데이터 로딩 오류: {e}")
    st.stop()

# ── 사이드바 ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 필터 설정")

    include_branch = st.toggle("분교 포함", value=False)
    df = df_all if include_branch else df_bon

    years    = sorted(df["기준년도"].unique())
    schools  = sorted(df["학교명"].unique())

    # 연도 범위
    year_range = st.slider(
        "기준년도 범위",
        min_value=int(years[0]),
        max_value=int(years[-1]),
        value=(int(years[0]), int(years[-1])),
        step=1,
    )

    # 학교 선택
    default_sel = (
        [PAPER_DEFAULT_SCHOOL]
        if PAPER_DEFAULT_SCHOOL in schools
        else schools[:1]
    )
    selected_schools = st.multiselect(
        "학교 선택",
        options=schools,
        default=default_sel,
    )

# ── 데이터 필터링 ─────────────────────────────────────────────────────────────
df_filtered = df[
    (df["기준년도"] >= year_range[0]) &
    (df["기준년도"] <= year_range[1])
].copy()

if selected_schools:
    df_chart = df_filtered[df_filtered["학교명"].isin(selected_schools)].copy()
else:
    df_chart = df_filtered.copy()

# 최근연도 기준 데이터
latest_year = df_filtered["기준년도"].max()
df_latest   = df_filtered[df_filtered["기준년도"] == latest_year]

# ── 페이지 헤더 ───────────────────────────────────────────────────────────────
st.title(f"{PAPER_PAGE_ICON} {PAPER_PAGE_TITLE}")
st.caption(
    f"대학알리미 공시자료 | 4주기 대학기관평가인증 정량지표 "
    f"| 기준: 등재(후보지) **{PAPER_THRESHOLD_JAEJI}편/인** · "
    f"SCI급 **{PAPER_THRESHOLD_SCI}편/인** *(확인 필요)*"
)
st.divider()

# ── KPI 요약 (6컬럼) ──────────────────────────────────────────────────────────
k1, k2, k3, k4, k5, k6 = st.columns(6)

# 등재(후보지) KPI
jaeji_mean  = df_latest[PAPER_COL_JAEJI].mean()
jaeji_max   = df_latest[PAPER_COL_JAEJI].max()
jaeji_min   = df_latest[PAPER_COL_JAEJI].min()
jaeji_max_s = df_latest.loc[df_latest[PAPER_COL_JAEJI].idxmax(), "학교명"]
jaeji_meet  = int((df_latest[PAPER_COL_JAEJI] >= PAPER_THRESHOLD_JAEJI).sum())

# SCI급 KPI
sci_mean  = df_latest[PAPER_COL_SCI].mean()
sci_max   = df_latest[PAPER_COL_SCI].max()
sci_min   = df_latest[PAPER_COL_SCI].min()
sci_max_s = df_latest.loc[df_latest[PAPER_COL_SCI].idxmax(), "학교명"]
sci_meet  = int((df_latest[PAPER_COL_SCI] >= PAPER_THRESHOLD_SCI).sum())
n_schools = df_latest["학교명"].nunique()

with k1:
    st.metric(
        f"📘 등재논문 평균 ({latest_year})",
        f"{jaeji_mean:.2f} 편/인",
    )
with k2:
    st.metric(
        "최고 (등재)",
        f"{jaeji_max:.2f}",
        help=jaeji_max_s,
    )
with k3:
    st.metric(
        f"기준충족 (등재, ≥{PAPER_THRESHOLD_JAEJI}편)",
        f"{jaeji_meet} / {n_schools} 교",
    )
with k4:
    st.metric(
        f"📗 SCI급 평균 ({latest_year})",
        f"{sci_mean:.2f} 편/인",
    )
with k5:
    st.metric(
        "최고 (SCI급)",
        f"{sci_max:.2f}",
        help=sci_max_s,
    )
with k6:
    st.metric(
        f"기준충족 (SCI급, ≥{PAPER_THRESHOLD_SCI}편)",
        f"{sci_meet} / {n_schools} 교",
    )

st.divider()

# ── 탭 구성 ──────────────────────────────────────────────────────────────────
single_school = len(selected_schools) == 1
tab_labels = ["📘 등재(후보지) 논문", "📗 SCI급/SCOPUS 논문"]
if single_school:
    tab_labels.append("📊 두 지표 비교")

tabs = st.tabs(tab_labels)

# ── Tab 1: 등재(후보지) 논문 ─────────────────────────────────────────────────
with tabs[0]:
    st.subheader("전임교원 1인당 등재(후보지) 논문")

    fig_j = create_trend_line_chart(
        df       = df_chart,
        x        = "기준년도",
        y        = PAPER_COL_JAEJI,
        color    = "학교명",
        title    = "전임교원 1인당 등재(후보지) 논문 추이",
        x_label  = "기준년도",
        y_label  = "논문 수 (편/인)",
    )
    add_threshold_hline(
        fig       = fig_j,
        threshold = PAPER_THRESHOLD_JAEJI,
        label     = f"기준값 {PAPER_THRESHOLD_JAEJI}편/인",
        color     = "red",
        dash      = "dash",
    )
    st.plotly_chart(fig_j, use_container_width=True)

    # 연도별 통계
    with st.expander("📊 연도별 통계 테이블"):
        stat_j = (
            df_filtered
            .groupby("기준년도")[PAPER_COL_JAEJI]
            .agg(
                평균="mean",
                최고="max",
                최저="min",
                학교수="count",
            )
            .reset_index()
        )
        stat_j.columns = ["기준년도", "평균 (편/인)", "최고 (편/인)", "최저 (편/인)", "학교수"]
        st.dataframe(
            stat_j.style.format({
                "평균 (편/인)": "{:.4f}",
                "최고 (편/인)": "{:.4f}",
                "최저 (편/인)": "{:.4f}",
            }),
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("📋 학교별 피벗 테이블"):
        pivot_j = df_filtered.pivot_table(
            index="기준년도",
            columns="학교명",
            values=PAPER_COL_JAEJI,
            aggfunc="mean",
        ).round(4)
        st.dataframe(pivot_j, use_container_width=True)

# ── Tab 2: SCI급/SCOPUS 논문 ──────────────────────────────────────────────────
with tabs[1]:
    st.subheader("전임교원 1인당 SCI급/SCOPUS 논문")

    fig_s = create_trend_line_chart(
        df       = df_chart,
        x        = "기준년도",
        y        = PAPER_COL_SCI,
        color    = "학교명",
        title    = "전임교원 1인당 SCI급/SCOPUS 논문 추이",
        x_label  = "기준년도",
        y_label  = "논문 수 (편/인)",
    )
    add_threshold_hline(
        fig       = fig_s,
        threshold = PAPER_THRESHOLD_SCI,
        label     = f"기준값 {PAPER_THRESHOLD_SCI}편/인",
        color     = "red",
        dash      = "dash",
    )
    st.plotly_chart(fig_s, use_container_width=True)

    # 연도별 통계
    with st.expander("📊 연도별 통계 테이블"):
        stat_s = (
            df_filtered
            .groupby("기준년도")[PAPER_COL_SCI]
            .agg(
                평균="mean",
                최고="max",
                최저="min",
                학교수="count",
            )
            .reset_index()
        )
        stat_s.columns = ["기준년도", "평균 (편/인)", "최고 (편/인)", "최저 (편/인)", "학교수"]
        st.dataframe(
            stat_s.style.format({
                "평균 (편/인)": "{:.4f}",
                "최고 (편/인)": "{:.4f}",
                "최저 (편/인)": "{:.4f}",
            }),
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("📋 학교별 피벗 테이블"):
        pivot_s = df_filtered.pivot_table(
            index="기준년도",
            columns="학교명",
            values=PAPER_COL_SCI,
            aggfunc="mean",
        ).round(4)
        st.dataframe(pivot_s, use_container_width=True)

# ── Tab 3: 두 지표 비교 (단일 학교 선택 시만 표시) ──────────────────────────
if single_school:
    with tabs[2]:
        school_name = selected_schools[0]
        st.subheader(f"{school_name} — 등재(후보지) vs SCI급 비교")

        df_one = df_chart.copy()

        # 두 지표를 long 형태로 변환
        df_melt = df_one.melt(
            id_vars    = "기준년도",
            value_vars = [PAPER_COL_JAEJI, PAPER_COL_SCI],
            var_name   = "지표",
            value_name = "논문수 (편/인)",
        )
        label_map = {
            PAPER_COL_JAEJI: "등재(후보지) 논문",
            PAPER_COL_SCI:   "SCI급/SCOPUS 논문",
        }
        df_melt["지표"] = df_melt["지표"].map(label_map)

        fig_cmp = px.line(
            df_melt,
            x          = "기준년도",
            y          = "논문수 (편/인)",
            color      = "지표",
            markers    = True,
            title      = f"{school_name} 논문실적 두 지표 비교",
            template   = "plotly_white",
            color_discrete_sequence=["#1f77b4", "#2ca02c"],
        )
        fig_cmp.update_traces(mode="lines+markers")
        fig_cmp.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(tickmode="linear", dtick=1),
            hovermode="x unified",
        )

        # 각 기준선을 다른 스타일로 구분
        add_threshold_hline(
            fig_cmp, PAPER_THRESHOLD_JAEJI,
            label=f"등재(후보지) 기준 {PAPER_THRESHOLD_JAEJI}편/인",
            color="#1f77b4", dash="dot",
        )
        add_threshold_hline(
            fig_cmp, PAPER_THRESHOLD_SCI,
            label=f"SCI급 기준 {PAPER_THRESHOLD_SCI}편/인",
            color="#2ca02c", dash="dash",
        )
        st.plotly_chart(fig_cmp, use_container_width=True)

        # 최근 연도 수치 테이블
        st.markdown("#### 최근 연도별 수치")
        recent_years = sorted(df_one["기준년도"].unique())[-5:]
        df_recent = df_one[df_one["기준년도"].isin(recent_years)][
            ["기준년도", PAPER_COL_JAEJI, PAPER_COL_SCI]
        ].copy()
        df_recent.columns = ["기준년도", "등재(후보지) (편/인)", "SCI급 (편/인)"]
        st.dataframe(
            df_recent.style.format({
                "등재(후보지) (편/인)": "{:.4f}",
                "SCI급 (편/인)": "{:.4f}",
            }),
            use_container_width=True,
            hide_index=True,
        )

# ── 지표 설명 ─────────────────────────────────────────────────────────────────
with st.expander("ℹ️ 지표 설명"):
    st.markdown(f"""
**전임교원 1인당 등재(후보지) 논문**
- 산출: 연구재단 등재지(후보 포함) 게재 논문 수 ÷ 전임교원 수
- 4주기 인증 기준: **{PAPER_THRESHOLD_JAEJI}편/인** *(확인 필요 — config.py에서 수정)*

**전임교원 1인당 SCI급/SCOPUS 논문**
- 산출: SCI급 또는 SCOPUS 등재 국제학술지 게재 논문 수 ÷ 전임교원 수
- 4주기 인증 기준: **{PAPER_THRESHOLD_SCI}편/인** *(확인 필요 — config.py에서 수정)*

**출처**: 대학알리미 공시자료 / 단위: 편/인
    """)
