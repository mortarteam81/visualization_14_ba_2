from __future__ import annotations

from collections.abc import Sequence

import pandas as pd
import streamlit as st

from ui import MetricSpec
from utils.ai_analysis import analyze_metric_with_lmstudio, build_metric_analysis_payload
from utils.ai_providers import LMStudioError


def _render_analysis_list(title: str, items: list[str]) -> None:
    st.markdown(f"**{title}**")
    if not items:
        st.caption("표시할 내용이 없습니다.")
        return
    for item in items:
        st.markdown(f"- {item}")


def render_metric_ai_analysis_panel(
    *,
    page_key: str,
    df: pd.DataFrame,
    year_col: str,
    school_col: str,
    latest_year: int,
    metrics: Sequence[MetricSpec],
    selected_schools: list[str],
    group_definitions: dict[str, list[str]] | None = None,
) -> None:
    st.subheader("AI 분석")
    st.caption("LM Studio 로컬 모델로 현재 선택 학교와 그룹 비교를 요약합니다.")

    group_definitions = group_definitions or {}
    result_key = f"{page_key}_ai_analysis_result"
    error_key = f"{page_key}_ai_analysis_error"

    metric_options = {metric.label: metric for metric in metrics}
    metric_labels = list(metric_options.keys())

    control_col1, control_col2, control_col3, control_col4 = st.columns([1.1, 1.1, 1.1, 1.2])
    with control_col1:
        selected_metric_label = st.selectbox("분석 지표", metric_labels, key=f"{page_key}_ai_metric")
    with control_col2:
        tone = st.selectbox("분석 톤", ["보고서형", "간결형"], key=f"{page_key}_ai_tone")
    with control_col3:
        focus = st.selectbox("분석 초점", ["선택 학교 중심", "그룹 비교 중심"], key=f"{page_key}_ai_focus")
    with control_col4:
        run_analysis = st.button("AI 분석 실행", width="stretch", type="primary", key=f"{page_key}_ai_run")

    selected_metric = metric_options[selected_metric_label]

    if run_analysis:
        payload = build_metric_analysis_payload(
            df,
            year_col=year_col,
            school_col=school_col,
            value_col=selected_metric.value_col,
            metric_label=selected_metric.label,
            unit=selected_metric.y_axis_label.split("(")[-1].rstrip(")") if "(" in selected_metric.y_axis_label else "",
            selected_schools=selected_schools,
            group_definitions=group_definitions,
            latest_year=latest_year,
            threshold=selected_metric.threshold.value if selected_metric.threshold else None,
            threshold_label=selected_metric.threshold.label if selected_metric.threshold else None,
        )
        try:
            with st.spinner("LM Studio로 분석 결과를 생성하는 중입니다..."):
                st.session_state[result_key] = analyze_metric_with_lmstudio(
                    payload,
                    tone=tone,
                    focus=focus,
                )
                st.session_state[error_key] = ""
        except LMStudioError as exc:
            st.session_state[result_key] = None
            st.session_state[error_key] = str(exc)
        except Exception as exc:  # pragma: no cover - defensive UI fallback
            st.session_state[result_key] = None
            st.session_state[error_key] = f"AI 분석 중 예상하지 못한 오류가 발생했습니다: {exc}"

    error_message = st.session_state.get(error_key, "")
    if error_message:
        st.error(error_message)
        st.caption("LM Studio 서버 주소, 모델 로드 상태, base URL 또는 포트 설정을 확인해 주세요.")
        return

    result = st.session_state.get(result_key)
    if not result:
        st.info("분석 옵션을 선택한 뒤 `AI 분석 실행`을 누르면 현재 선택 학교와 그룹 기준 해석을 볼 수 있습니다.")
        return

    summary_col, threshold_col = st.columns([1.3, 1])
    with summary_col:
        st.markdown("**핵심 요약**")
        st.write(result["summary"] or "요약이 생성되지 않았습니다.")
    with threshold_col:
        st.markdown("**기준 해석**")
        st.write(result["threshold_assessment"] or "기준 해석이 생성되지 않았습니다.")

    detail_col1, detail_col2 = st.columns(2)
    with detail_col1:
        _render_analysis_list("주요 시사점", result["highlights"])
        _render_analysis_list("권고 액션", result["recommended_actions"])
    with detail_col2:
        _render_analysis_list("주의 요소", result["risks"])
        _render_analysis_list("해석 유의사항", result["caveats"])
