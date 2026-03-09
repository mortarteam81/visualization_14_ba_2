import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '14-ba-2.-beobjeongbudamgeum-budam-hyeonhwang_daehag_beobjeongbudamgeum-budamryul-20260309-seoul-sojae-saribdaehag.csv')

@st.cache_data
def load_data():
    df = pd.read_csv(CSV_PATH, encoding='cp949')
    # 필요한 컬럼만 선택 및 정리
    df = df[['기준년도', '학교명', '부담율']].copy()
    df['부담율'] = pd.to_numeric(df['부담율'], errors='coerce')
    df = df.dropna(subset=['부담율'])
    df['기준년도'] = df['기준년도'].astype(int)
    return df

st.set_page_config(page_title="서울대 대학 부담율 시각화", layout="wide")

st.title("🛡️ 서울 소재 사립대학교 법정부담금 부담율 추이")

# 데이터 로드
df = load_data()

# 학교 목록 (중복 제거, 정렬)
schools = sorted(df['학교명'].unique())

# 사이드바: 학교 선택 (최대 10개)
st.sidebar.header("학교 선택")
selected_schools = st.sidebar.multiselect(
    "최대 60개 학교 선택",
    schools,
    max_selections=60,  # 최대 60개 선택 가능 (전체 학교 수에 따라 조정)
    default=['성신여자대학교'] if '성신여자대학교' in schools else []
)

if not selected_schools:
    st.warning("학교를 선택해주세요.")
    st.stop()

# 필터링된 데이터
filtered_df = df[df['학교명'].isin(selected_schools)]

if filtered_df.empty:
    st.error("선택된 학교에 데이터가 없습니다.")
    st.stop()

# 메인 시각화
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("부담율 추이 (기준연도별)")
    
    # 라인 차트
    fig = px.line(
        filtered_df,
        x='기준년도',
        y='부담율',
        color='학교명',
        title=f"선택 학교 ({len(selected_schools)}개) 부담율 변화",
        labels={'부담율': '부담율 (%)', '기준년도': '기준연도'},
        markers=True
    )
    
    # 10% 기준선 추가
    fig.add_hline(
        y=10,
        line_dash="dash",
        line_color="red",
        annotation_text="10% 기준선",
        annotation_position="top right"
    )
    
    # 레이아웃 개선
    fig.update_layout(
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("통계 요약")
    
    # 연도별 통계
    yearly_stats = filtered_df.groupby('기준년도')['부담율'].agg(['mean', 'max', 'min', 'count']).round(1)
    yearly_stats.columns = ['평균', '최고', '최저', '학교수']
    st.dataframe(yearly_stats, use_container_width=True)
    
    # 전체 통계
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("전체 평균", f"{filtered_df['부담율'].mean():.1f}%")
    with col_b:
        st.metric("최고 부담율", f"{filtered_df['부담율'].max():.1f}%")
    with col_c:
        st.metric("10% 초과 학교", f"{(filtered_df['부담율'] > 10).sum()}/{len(filtered_df)}")

# 하단: 상세 테이블
with st.expander("📊 상세 데이터 보기"):
    st.dataframe(filtered_df.pivot(index='기준년도', columns='학교명', values='부담율').round(1), use_container_width=True)

# 정보 패널
with st.expander("ℹ️ 데이터 정보"):
    st.info("""
    - **데이터 출처**: 업로드된 CSV 파일 (서울 소재 사립대학교 법정부담금 현황)
    - **기준년도**: 실제 기준년도 (공시연도 -1)
    - **부담율**: (법정부담금부담액 / 법정부담금기준액) * 100 (%)
    - **기준선**: 10% (사용자 요청)
    - **공유 방법**: 
      1. `pip install streamlit pandas plotly`
      2. `streamlit run app.py`
      3. Streamlit Cloud에 GitHub 연동으로 배포
    """)

# 푸터
st.markdown("---")
st.caption("📈 Perplexity AI로 생성 | 데이터: 2026-03-09 기준")
