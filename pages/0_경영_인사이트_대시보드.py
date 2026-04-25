"""Management insight dashboard prototype."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.ai_providers import LMStudioError
from utils.config import APP_ICON, APP_TITLE
from utils.management_ai import (
    analyze_management_insight_with_lmstudio,
    filter_payload_for_question,
    get_question_by_label,
    questions_for_mode,
)
from utils.management_insights import (
    QUADRANT_PRESETS,
    build_range_management_ai_payload,
    build_single_year_management_ai_payload,
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


def render_management_ai_list(title: str, items: list[str]) -> None:
    st.markdown(f"**{title}**")
    if not items:
        st.caption("생성된 내용이 없습니다.")
        return
    for item in items:
        st.markdown(f"- {item}")


def render_management_ai_result(result: dict, context: dict | None = None) -> None:
    st.markdown("#### 요약")
    st.write(result["summary"] or "요약이 생성되지 않았습니다.")

    col1, col2 = st.columns(2)
    with col1:
        render_management_ai_list("근거", result["evidence"])
        render_management_ai_list("정책 시사점", result["management_implications"])
        render_management_ai_list("권고 액션", result["recommended_actions"])
    with col2:
        render_management_ai_list("위험", result["risks"])
        render_management_ai_list("해석 유의사항", result["caveats"])

    with st.expander("사용 데이터 범위", expanded=True):
        data_used = result.get("data_used") or context or {}
        if data_used:
            st.json(data_used)
        else:
            st.caption("AI 응답에 사용 데이터 범위가 포함되지 않았습니다.")


def render_management_ai_panel(
    *,
    dataset,
    available_years: list[int],
    selected_year: int,
    focus_school: str,
    comparison_schools: list[str],
    selected_groups: list[str],
    quadrant_preset: tuple[str, str, str],
) -> None:
    st.caption("질문 pool 기반으로 대시보드 요약 데이터를 해석합니다. 자유 질문은 v1 범위에서 제공하지 않습니다.")

    result_key = "management_dashboard_ai_result"
    error_key = "management_dashboard_ai_error"
    context_key = "management_dashboard_ai_context"

    default_start_year = 2020 if 2020 in available_years else min(available_years)
    default_end_year = 2024 if 2024 in available_years else max(available_years)

    mode_col, range_col1, range_col2, tone_col = st.columns([1.1, 0.9, 0.9, 1])
    with mode_col:
        mode_label = st.radio(
            "분석 기준",
            ["연도 범위", "선택 연도"],
            horizontal=True,
            key="management_ai_mode_label",
        )
    mode = "year_range" if mode_label == "연도 범위" else "single_year"

    start_year = default_start_year
    end_year = default_end_year
    with range_col1:
        if mode == "year_range":
            start_year = st.selectbox(
                "시작 연도",
                available_years,
                index=available_years.index(default_start_year),
                key="management_ai_start_year",
            )
        else:
            st.metric("분석 연도", f"{selected_year}년")
    with range_col2:
        if mode == "year_range":
            end_year = st.selectbox(
                "종료 연도",
                available_years,
                index=available_years.index(default_end_year),
                key="management_ai_end_year",
            )
        else:
            st.metric("기준 대학", focus_school)
    with tone_col:
        tone = st.selectbox(
            "분석 톤",
            ["전략 제안형", "실무 보고형"],
            key="management_ai_tone",
        )

    question_options = questions_for_mode(mode)
    question_labels = [question.label for question in question_options]
    selected_question_label = st.selectbox(
        "분석 질문",
        question_labels,
        key="management_ai_question",
    )
    selected_question = get_question_by_label(selected_question_label, mode=mode)

    if mode == "year_range":
        base_payload = build_range_management_ai_payload(
            dataset,
            start_year=start_year,
            end_year=end_year,
            focus_school=focus_school,
            comparison_schools=comparison_schools,
            groups=selected_groups,
        )
        if start_year > end_year:
            st.warning("시작 연도가 종료 연도보다 큽니다. 분석에서는 두 값을 자동으로 정렬해 사용합니다.")
    else:
        base_payload = build_single_year_management_ai_payload(
            dataset,
            year=selected_year,
            focus_school=focus_school,
            comparison_schools=comparison_schools,
            groups=selected_groups,
            quadrant_preset=quadrant_preset,
        )

    coverage_warnings = base_payload.get("coverage", {}).get("warnings", [])
    if coverage_warnings:
        st.warning("\n".join(f"- {warning}" for warning in coverage_warnings))

    filtered_payload = filter_payload_for_question(base_payload, selected_question)
    run_analysis = st.button(
        "AI 경영 분석 실행",
        type="primary",
        width="stretch",
        key="management_ai_run",
    )

    if run_analysis:
        try:
            with st.spinner("LM Studio로 경영 인사이트 분석을 생성하고 있습니다..."):
                st.session_state[result_key] = analyze_management_insight_with_lmstudio(
                    filtered_payload,
                    question=selected_question,
                    mode=mode,
                    tone=tone,
                )
                st.session_state[error_key] = ""
                st.session_state[context_key] = {
                    "질문": selected_question.label,
                    "분석 기준": mode_label,
                    "기준 대학": focus_school,
                    "비교 대학": comparison_schools,
                    "분석 기간": f"{start_year}-{end_year}" if mode == "year_range" else str(selected_year),
                    "포함 지표 수": filtered_payload.get("included_series_count"),
                    "미포함 지표 수": filtered_payload.get("excluded_pending_metric_count"),
                }
        except LMStudioError as exc:
            st.session_state[result_key] = None
            st.session_state[error_key] = str(exc)
        except Exception as exc:  # pragma: no cover - defensive UI fallback
            st.session_state[result_key] = None
            st.session_state[error_key] = f"AI 분석 중 예상하지 못한 오류가 발생했습니다: {exc}"

    error_message = st.session_state.get(error_key, "")
    if error_message:
        st.error(error_message)
        st.caption("LM Studio 연결 상태, 모델 설정, base URL을 확인해 주세요.")
        return

    result = st.session_state.get(result_key)
    if not result:
        st.info("분석 질문을 선택한 뒤 `AI 경영 분석 실행`을 누르면 근거 명시형 해석을 볼 수 있습니다.")
        return

    context = st.session_state.get(context_key)
    if context:
        st.caption(
            f"{context['분석 기준']} · {context['분석 기간']} · {context['기준 대학']} · "
            f"계산 포함 {context['포함 지표 수']}개 / 미포함 {context['미포함 지표 수']}개"
        )
    render_management_ai_result(result, context=context)


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

selected_quadrant_preset = QUADRANT_PRESETS[0]
tabs = st.tabs(["강점/약점", "정책 사분면", "상관관계", "AI 분석", "지표 로드맵"])

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
    selected_preset_label = st.selectbox(
        "사분면 프리셋",
        preset_labels,
        key="management_quadrant_preset",
    )
    selected_quadrant_preset = next(preset for preset in QUADRANT_PRESETS if preset[0] == selected_preset_label)
    _, x_key, y_key = selected_quadrant_preset
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
    render_management_ai_panel(
        dataset=dataset,
        available_years=available_years,
        selected_year=selected_year,
        focus_school=focus_school,
        comparison_schools=comparison_schools,
        selected_groups=selected_groups,
        quadrant_preset=selected_quadrant_preset,
    )

with tabs[4]:
    st.dataframe(
        pending_metric_roadmap_frame().drop(columns=["metric_id"]),
        width="stretch",
        hide_index=True,
    )
