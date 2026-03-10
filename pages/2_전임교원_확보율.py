"""
전임교원 확보율 — 서울 소재 사립대학교
"""

import streamlit as st

from utils.config import (
    APP_SUBTITLE,
    DATA_UPDATED,
    GYOWON_COL_JAEHAK,
    GYOWON_COL_JEONGWON,
    GYOWON_DEFAULT_SCHOOL,
    GYOWON_PAGE_ICON,
    GYOWON_PAGE_TITLE,
    GYOWON_THRESHOLD,
)
from utils.chart_utils import add_threshold_hline, create_trend_line_chart
from utils.data_loader import load_gyowon_data

st.set_page_config(
    page_title=f"{GYOWON_PAGE_TITLE} | 교육여건 지표",
    page_icon=GYOWON_PAGE_ICON,
    layout="wide",
)

# ── 헤더 ─────────────────────────────────────────────────────────────────────
st.title(f"{GYOWON_PAGE_ICON} {GYOWON_PAGE_TITLE}")
st.caption(APP_SUBTITLE)

# ── 사이드바: 필터 ───────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔍 필터")

    # 분교 포함 여부
    include_branch = st.toggle(
        "분교 포함",
        value=False,
        help="가톨릭대 제2·3캠퍼스 등 분교 데이터를 포함합니다.",
    )

    # 기준 선택
    criterion = st.radio(
        "확보율 기준",
        options=["학생정원 기준", "재학생 기준"],
        index=0,
        help=(
            "**학생정원 기준**: 4주기 인증 주요 기준 (입학정원 기반)\n\n"
            "**재학생 기준**: 실제 재학생 수 기반"
        ),
    )

    st.divider()

# ── 데이터 로드 ───────────────────────────────────────────────────────────────
try:
    df = load_gyowon_data(bonkyo_only=not include_branch)
except (FileNotFoundError, ValueError) as e:
    st.error(f"❌ 데이터 오류\n\n{e}")
    st.stop()

# 선택 기준에 따른 컬럼 지정
y_col = GYOWON_COL_JEONGWON if criterion == "학생정원 기준" else GYOWON_COL_JAEHAK
y_label = f"확보율 (%) — {criterion}"

schools     = sorted(df["학교명"].unique())
years       = sorted(df["기준년도"].unique())
latest_year = max(years)

# ── 사이드바: 학교 선택 ───────────────────────────────────────────────────────
with st.sidebar:
    default_selection = (
        [GYOWON_DEFAULT_SCHOOL] if GYOWON_DEFAULT_SCHOOL in schools else schools[:1]
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

# 최신 연도 KPI (학생정원 기준으로 고정 — 인증 주요 기준)
latest_df   = filtered_df[filtered_df["기준년도"] == latest_year]
above_count = (latest_df[y_col] >= GYOWON_THRESHOLD).sum()
total_count = len(latest_df)
idx_max     = latest_df[y_col].idxmax()
idx_min     = latest_df[y_col].idxmin()

# ── KPI 메트릭 ────────────────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)

m1.metric(
    f"{latest_year}년 선택교 평균 ({criterion})",
    f"{latest_df[y_col].mean():.1f}%",
)
m2.metric(
    "최고 확보율",
    f"{latest_df[y_col].max():.1f}%",
    latest_df.loc[idx_max, "학교명"],
    delta_color="off",
)
m3.metric(
    "최저 확보율",
    f"{latest_df[y_col].min():.1f}%",
    latest_df.loc[idx_min, "학교명"],
    delta_color="off",
)
m4.metric(
    f"{GYOWON_THRESHOLD}% 이상 (인증 기준 충족)",
    f"{above_count} / {total_count}개",
    help=f"{latest_year}년 기준, {criterion}, 학교 단위 집계",
)

st.divider()

# ── 메인 시각화 ───────────────────────────────────────────────────────────────
col_chart, col_stats = st.columns([2, 1])

with col_chart:
    st.subheader(f"전임교원 확보율 연도별 추이 ({criterion})")

    fig = create_trend_line_chart(
        filtered_df,
        x="기준년도",
        y=y_col,
        color="학교명",
        title=f"선택 학교 ({len(selected_schools)}개) 전임교원 확보율 변화 ({criterion})",
        x_label="기준연도",
        y_label=y_label,
    )
    fig = add_threshold_hline(
        fig,
        threshold=GYOWON_THRESHOLD,
        label=f"{GYOWON_THRESHOLD}% 기준선 (4주기 인증, 학생정원 기준)",
    )
    st.plotly_chart(fig, use_container_width=True)

with col_stats:
    st.subheader("연도별 통계")

    yearly_stats = (
        filtered_df
        .groupby("기준년도")[y_col]
        .agg(평균="mean", 최고="max", 최저="min", 학교수="count")
        .round(1)
    )
    st.dataframe(yearly_stats, use_container_width=True)

# ── 두 기준 비교 차트 (학교를 1개만 선택한 경우) ─────────────────────────────
if len(selected_schools) == 1:
    with st.expander("📊 학생정원 기준 vs 재학생 기준 비교", expanded=True):
        compare_df = filtered_df[["기준년도", GYOWON_COL_JEONGWON, GYOWON_COL_JAEHAK]].copy()
        compare_df = compare_df.rename(columns={
            GYOWON_COL_JEONGWON: "학생정원 기준",
            GYOWON_COL_JAEHAK:   "재학생 기준",
        })
        compare_melt = compare_df.melt(
            id_vars="기준년도",
            value_vars=["학생정원 기준", "재학생 기준"],
            var_name="기준",
            value_name="확보율 (%)",
        )

        import plotly.express as px
        fig2 = px.line(
            compare_melt,
            x="기준년도",
            y="확보율 (%)",
            color="기준",
            markers=True,
            template="plotly_white",
            title=f"{selected_schools[0]} — 기준별 전임교원 확보율 비교",
        )
        fig2.add_hline(
            y=GYOWON_THRESHOLD,
            line_dash="dash",
            line_color="red",
            annotation_text=f"{GYOWON_THRESHOLD}% 기준선",
            annotation_position="top right",
        )
        fig2.update_layout(hovermode="x unified", height=400)
        st.plotly_chart(fig2, use_container_width=True)

# ── 교차표 ────────────────────────────────────────────────────────────────────
with st.expander("📊 연도 × 학교 교차표"):
    pivot = (
        filtered_df
        .pivot_table(index="기준년도", columns="학교명", values=y_col, aggfunc="mean")
        .round(1)
    )
    st.dataframe(pivot, use_container_width=True)

# ── 지표 설명 ─────────────────────────────────────────────────────────────────
with st.expander("ℹ️ 지표 설명"):
    st.markdown(f"""
| 항목 | 내용 |
|------|------|
| **출처** | 대학알리미 공시자료 (서울 소재 사립대학교) |
| **기준년도** | 실제 기준년도 (공시연도와 동일) |
| **산식 (학생정원 기준)** | 전임교원 수 ÷ 교원법정정원(학생정원 기준) × 100 (%) |
| **산식 (재학생 기준)** | 전임교원 수 ÷ 교원법정정원(재학생 기준) × 100 (%) |
| **4주기 인증 기준** | **{GYOWON_THRESHOLD}% 이상** (학생정원 기준) |
| **분교 처리** | 기본값: 본교만 표시 / 사이드바에서 분교 포함 선택 가능 |
| **데이터 기준일** | {DATA_UPDATED} |
""")

st.markdown("---")
st.caption(f"📈 데이터 출처: 대학알리미 | 기준일: {DATA_UPDATED}")
