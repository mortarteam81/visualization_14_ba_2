"""Management insight dashboard prototype."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.config import APP_ICON, APP_TITLE
from utils.management_insights import (
    QUADRANT_PRESETS,
    build_management_insight_dataset,
    build_percentile_profile,
    build_quadrant_frame,
    build_rank_correlation,
    default_analysis_year,
    filter_metric_keys_by_groups,
    format_metric_value,
    metric_map,
    pending_metric_roadmap_frame,
)
from utils.theme import apply_app_theme


st.set_page_config(
    page_title=f"경영 인사이트 | {APP_TITLE}",
    page_icon=APP_ICON,
    layout="wide",
)
apply_app_theme()


@st.cache_data(show_spinner="분석 데이터 구성 중...")
def load_dashboard_data():
    return build_management_insight_dataset()


def render_profile_chart(profile: pd.DataFrame) -> None:
    chart_df = profile.sort_values("percentile", ascending=True)
    labels = [
        f"{row.metric_label} · {format_metric_value(row.value, row)}"
        for row in chart_df.itertuples(index=False)
    ]
    colors = [
        "#EF4444" if value < 35 else "#F59E0B" if value < 65 else "#4ADE80"
        for value in chart_df["percentile"]
    ]
    fig = go.Figure(
        go.Bar(
            x=chart_df["percentile"],
            y=labels,
            orientation="h",
            marker={"color": colors},
            text=[f"{value:.0f}" for value in chart_df["percentile"]],
            textposition="inside",
            hovertemplate="%{y}<br>분위수=%{x:.1f}<extra></extra>",
        )
    )
    fig.add_vline(
        x=50,
        line_dash="dot",
        line_color="#E5E7EB",
        annotation_text="중위",
        annotation_position="top",
    )
    fig.update_layout(
        height=max(460, len(chart_df) * 34),
        xaxis_title="상대 분위수",
        yaxis_title="",
        xaxis={"range": [0, 100]},
        plot_bgcolor="rgba(15, 23, 42, 0.82)",
        paper_bgcolor="rgba(15, 23, 42, 0.0)",
        font={"color": "#E5EDF7"},
        margin={"l": 40, "r": 24, "t": 32, "b": 48},
        showlegend=False,
    )
    fig.update_xaxes(gridcolor="rgba(148, 163, 184, 0.12)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(148, 163, 184, 0.04)")
    st.plotly_chart(fig, use_container_width=True)


def render_profile_summary(profile: pd.DataFrame) -> None:
    summary_df = profile.copy()
    summary_df["값"] = [
        format_metric_value(row.value, row)
        for row in summary_df.itertuples(index=False)
    ]
    summary_df["분위수"] = summary_df["percentile"].round(1)

    strong_col, weak_col = st.columns(2)
    with strong_col:
        st.markdown("#### 상대 강점")
        st.dataframe(
            summary_df.sort_values("percentile", ascending=False)
            .head(5)[["group", "metric_label", "값", "분위수"]]
            .rename(columns={"group": "영역", "metric_label": "지표"}),
            width="stretch",
            hide_index=True,
        )
    with weak_col:
        st.markdown("#### 보완 후보")
        st.dataframe(
            summary_df.sort_values("percentile", ascending=True)
            .head(5)[["group", "metric_label", "값", "분위수"]]
            .rename(columns={"group": "영역", "metric_label": "지표"}),
            width="stretch",
            hide_index=True,
        )


def render_quadrant_chart(
    frame: pd.DataFrame,
    *,
    x_key: str,
    y_key: str,
    focus_school: str,
    comparison_schools: list[str],
    metrics_by_key: dict,
) -> None:
    x_metric = metrics_by_key[x_key]
    y_metric = metrics_by_key[y_key]
    selected = set(comparison_schools) | {focus_school}
    frame = frame.copy()
    frame["구분"] = "기타 대학"
    frame.loc[frame["school_name"].isin(selected), "구분"] = "비교 대학"
    frame.loc[frame["school_name"] == focus_school, "구분"] = "기준 대학"
    frame["라벨"] = frame["school_name"].where(frame["school_name"].isin(selected), "")

    fig = px.scatter(
        frame,
        x=x_key,
        y=y_key,
        color="구분",
        text="라벨",
        hover_name="school_name",
        color_discrete_map={
            "기준 대학": "#F59E0B",
            "비교 대학": "#6EA8FF",
            "기타 대학": "#64748B",
        },
        labels={
            x_key: f"{x_metric.label} ({x_metric.unit})",
            y_key: f"{y_metric.label} ({y_metric.unit})",
        },
        template="plotly_dark",
        height=620,
    )
    fig.add_vline(x=frame[x_key].median(), line_dash="dot", line_color="#E5E7EB")
    fig.add_hline(y=frame[y_key].median(), line_dash="dot", line_color="#E5E7EB")
    fig.update_traces(
        marker={"size": 11, "line": {"width": 1, "color": "rgba(248, 251, 255, 0.24)"}},
        textposition="top center",
        cliponaxis=False,
    )
    fig.update_layout(
        plot_bgcolor="rgba(15, 23, 42, 0.82)",
        paper_bgcolor="rgba(15, 23, 42, 0.0)",
        font={"color": "#E5EDF7"},
        legend={
            "orientation": "h",
            "yanchor": "top",
            "y": -0.18,
            "xanchor": "left",
            "x": 0,
        },
        margin={"l": 48, "r": 32, "t": 36, "b": 132},
    )
    st.plotly_chart(fig, use_container_width=True)


def render_correlation_heatmap(
    correlation: pd.DataFrame,
    *,
    metrics_by_key: dict,
) -> None:
    labels = [metrics_by_key[key].label for key in correlation.columns]
    values = correlation.values
    text = [
        ["" if pd.isna(value) else f"{value:.2f}" for value in row]
        for row in values
    ]
    fig = go.Figure(
        go.Heatmap(
            z=values,
            x=labels,
            y=labels,
            zmin=-1,
            zmax=1,
            colorscale=[
                [0.0, "#2563EB"],
                [0.5, "#111827"],
                [1.0, "#F59E0B"],
            ],
            text=text,
            texttemplate="%{text}",
            hovertemplate="%{y} × %{x}<br>rank corr=%{z:.2f}<extra></extra>",
            colorbar={"title": "상관"},
        )
    )
    fig.update_layout(
        height=max(620, len(labels) * 34),
        plot_bgcolor="rgba(15, 23, 42, 0.82)",
        paper_bgcolor="rgba(15, 23, 42, 0.0)",
        font={"color": "#E5EDF7"},
        margin={"l": 120, "r": 32, "t": 32, "b": 120},
    )
    fig.update_xaxes(tickangle=35)
    st.plotly_chart(fig, use_container_width=True)


dataset = load_dashboard_data()
metrics_by_key = metric_map(dataset.metrics)
years = default_year = default_analysis_year(dataset.long)

st.title("경영 인사이트 대시보드")
st.caption("구현 완료 지표만 계산에 사용한 정책 가설 탐색용 프로토타입")

if default_year is None:
    st.error("분석 가능한 구현 완료 지표 데이터가 없습니다.")
    st.stop()

available_years = sorted(dataset.long["year"].dropna().astype(int).unique())
group_options = sorted({metric.group for metric in dataset.metrics})

with st.sidebar:
    st.header("필터")
    selected_year = st.selectbox(
        "기준 연도",
        available_years,
        index=available_years.index(default_year),
    )
    year_frame = dataset.long[dataset.long["year"] == selected_year]
    school_options = sorted(year_frame["school_name"].dropna().unique())
    default_school = "성신여자대학교" if "성신여자대학교" in school_options else school_options[0]
    focus_school = st.selectbox(
        "기준 대학",
        school_options,
        index=school_options.index(default_school),
    )
    comparison_defaults = [school for school in ["숙명여자대학교", "덕성여자대학교"] if school in school_options]
    comparison_schools = st.multiselect(
        "비교 대학",
        school_options,
        default=comparison_defaults,
    )
    selected_groups = st.multiselect(
        "지표 영역",
        group_options,
        default=group_options,
    )

included_metric_keys = filter_metric_keys_by_groups(dataset.metrics, selected_groups)
included_year_metric_count = year_frame[year_frame["metric_key"].isin(included_metric_keys)]["metric_key"].nunique()
year_school_count = year_frame["school_name"].nunique()

metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
metric_col1.metric("계산 포함 지표", f"{dataset.included_series_count}개")
metric_col2.metric("구현 완료 항목", f"{dataset.implemented_metric_count}개")
metric_col3.metric("미구현 항목", f"{dataset.pending_metric_count}개")
metric_col4.metric(f"{selected_year}년 분석 범위", f"{included_year_metric_count}개 / {year_school_count}개교")

if dataset.skipped_sources:
    with st.expander("불러오지 못한 구현 완료 지표", expanded=False):
        st.write("\n".join(f"- {item}" for item in dataset.skipped_sources))

tabs = st.tabs(["강점/약점", "정책 사분면", "상관관계", "지표 로드맵"])

with tabs[0]:
    profile = build_percentile_profile(
        dataset.long,
        dataset.metrics,
        year=selected_year,
        school_name=focus_school,
        groups=selected_groups,
    )
    if profile.empty:
        st.info("선택한 조건에서 강점/약점 프로파일을 만들 수 없습니다.")
    else:
        render_profile_chart(profile)
        render_profile_summary(profile)

with tabs[1]:
    preset_labels = [preset[0] for preset in QUADRANT_PRESETS]
    selected_preset_label = st.selectbox("사분면 프리셋", preset_labels)
    _, x_key, y_key = next(preset for preset in QUADRANT_PRESETS if preset[0] == selected_preset_label)
    quadrant_frame = build_quadrant_frame(
        dataset.wide,
        year=selected_year,
        x_metric_key=x_key,
        y_metric_key=y_key,
    )
    if quadrant_frame["school_name"].nunique() < 10:
        st.info("선택한 연도에서 사분면 분석에 필요한 공통 데이터가 부족합니다.")
    else:
        render_quadrant_chart(
            quadrant_frame,
            x_key=x_key,
            y_key=y_key,
            focus_school=focus_school,
            comparison_schools=comparison_schools,
            metrics_by_key=metrics_by_key,
        )

with tabs[2]:
    correlation = build_rank_correlation(
        dataset.wide,
        included_metric_keys,
        year=selected_year,
        min_pair_count=10,
    )
    if correlation.empty:
        st.info("선택한 조건에서 상관관계 히트맵을 만들 수 없습니다.")
    else:
        st.caption("상관관계는 정책 가설 탐색용이며 인과관계를 의미하지 않습니다.")
        render_correlation_heatmap(correlation, metrics_by_key=metrics_by_key)

with tabs[3]:
    st.dataframe(
        pending_metric_roadmap_frame().drop(columns=["metric_id"]),
        width="stretch",
        hide_index=True,
    )
