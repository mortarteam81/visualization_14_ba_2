from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from registry import get_metric
from utils.auth import require_authenticated_user
from utils.config import APP_ICON, APP_SUBTITLE
from utils.data_validation_modes import (
    DECISION_ACCEPT_RAW,
    DECISION_KEEP_CURRENT,
    DECISION_NEEDS_CHECK,
    DECISION_PENDING,
    REVIEW_DECISIONS,
    build_dormitory_shadow_status,
    build_mismatch_review_frame,
    build_review_completion_status,
    load_dormitory_candidate_frame,
    load_dormitory_mismatch_frame,
    load_dormitory_processing_report,
    load_dormitory_review_decisions,
    load_dormitory_source_acquisition,
    review_decisions_from_frame,
    save_dormitory_review_decisions,
)
from utils.query import get_dataset
from utils.theme import apply_app_theme


DORMITORY_PAGE = get_metric("dormitory_rate")
YEAR_COL = "기준년도"
SCHOOL_COL = "학교명"
RATE_COL = "기숙사수용률"


def _build_context() -> dict[str, object]:
    status = build_dormitory_shadow_status()
    mismatch = load_dormitory_mismatch_frame()
    decisions = load_dormitory_review_decisions()
    review_status = build_review_completion_status(
        mismatch,
        decisions,
        base_ready=status.ready_for_preview,
        high_mismatches=status.high_mismatches,
        dataset_id=status.dataset_id,
    )
    return {
        "status": status,
        "mismatch": mismatch,
        "decisions": decisions,
        "review_status": review_status,
    }


def _render_goal() -> None:
    st.markdown("#### 이번 검증의 목표")
    st.write(
        "이 화면은 기숙사 수용률 후보 데이터가 운영 화면에 반영 가능한지 판단하기 위한 운영자용 검증 콘솔입니다."
    )
    st.markdown(
        "- 원자료가 보존되어 있는지 확인합니다.\n"
        "- 원자료 기반 후보 데이터가 생성되었는지 확인합니다.\n"
        "- 현재 운영값과 후보값의 차이를 검토합니다.\n"
        "- 승격 가능 여부와 보류 사유를 확인합니다."
    )


def _render_status_cards(status: object, review_status: object) -> None:
    cols = st.columns(4)
    cols[0].metric("원자료 확보", "완료" if status.raw_preserved else "확인 필요")
    cols[1].metric("후보 데이터", "완료" if status.ready_for_preview else "확인 필요")
    cols[2].metric("운영값과 차이", f"{status.mismatch_rows:,}건")
    cols[3].metric("승격 판단", "가능" if review_status.ready_for_promotion else "보류")


def _render_review_summary(review_status: object) -> None:
    st.caption(
        f"검토 진행: {review_status.reviewed:,}/{review_status.total:,}건 완료 "
        f"| 미검토 {review_status.pending:,}건 "
        f"| 추가 확인 {review_status.needs_followup:,}건"
    )
    if review_status.ready_for_promotion:
        st.success("모든 차이 항목이 검토되어 승격 준비 조건을 충족했습니다.")
    else:
        for reason in review_status.reasons:
            st.warning(reason)


def _render_auto_check(context: dict[str, object]) -> None:
    status = context["status"]
    review_status = context["review_status"]
    report = load_dormitory_processing_report()
    acquisition = load_dormitory_source_acquisition()

    _render_goal()
    _render_status_cards(status, review_status)

    st.markdown("#### 자동 점검 결과")
    checks = [
        ("원자료 XLSX 보존", status.raw_preserved, "원자료 파일과 획득 기록이 보존되어 있습니다."),
        ("후보 CSV 생성", status.candidate_exists, f"후보 데이터 {status.candidate_rows:,}행이 생성되어 있습니다."),
        ("처리 보고서 생성", status.report_exists, "원자료 처리 보고서가 생성되어 있습니다."),
        ("high mismatch 없음", status.high_mismatches == 0, f"high mismatch {status.high_mismatches:,}건"),
        ("운영자 검토 완료", review_status.ready_for_promotion, "모든 차이 항목 검토가 완료되어야 합니다."),
    ]
    for label, passed, detail in checks:
        if passed:
            st.success(f"{label}: {detail}")
        else:
            st.warning(f"{label}: {detail}")

    with st.expander("상세 기술 정보", expanded=False):
        st.markdown("##### 원자료 획득 기록")
        st.json(acquisition)
        st.markdown("##### 처리 보고서")
        st.json(report)


def _render_review_mode(context: dict[str, object]) -> None:
    status = context["status"]
    mismatch = context["mismatch"]
    decisions = context["decisions"]
    review_status = context["review_status"]

    st.markdown("#### 차이 검토")
    st.write(
        "운영 CSV와 원자료 재가공 후보 CSV가 다른 항목을 검토합니다. "
        "각 항목에 검토 상태를 지정하고 필요한 경우 메모를 남겨 주세요."
    )
    _render_review_summary(review_status)

    if mismatch.empty:
        st.success("운영값과 후보값 사이에 검토할 차이가 없습니다.")
        return

    review_frame = build_mismatch_review_frame(mismatch, decisions, dataset_id=status.dataset_id)
    edited = st.data_editor(
        review_frame,
        hide_index=True,
        use_container_width=True,
        disabled=[
            "학교",
            "기준년도",
            "확인항목",
            "현재 운영값",
            "원자료 재가공값",
            "차이",
        ],
        column_config={
            "검토키": None,
            "검토 상태": st.column_config.SelectboxColumn(
                "검토 상태",
                help="운영 반영 전 판단 상태를 선택합니다.",
                options=list(REVIEW_DECISIONS),
                required=True,
            ),
            "검토 메모": st.column_config.TextColumn(
                "검토 메모",
                help="운영값 유지 또는 추가 확인 필요 판단의 근거를 적습니다.",
            ),
        },
        key="dormitory_review_editor",
    )

    st.caption(f"`{DECISION_KEEP_CURRENT}`는 메모가 있어야 검토 완료로 인정됩니다.")
    if st.button("검토 결과 저장", type="primary", key="save_dormitory_review_decisions"):
        save_dormitory_review_decisions(
            review_decisions_from_frame(edited, dataset_id=status.dataset_id),
            dataset_id=status.dataset_id,
        )
        st.success("검토 결과를 저장했습니다. 상단 상태는 페이지 새로고침 후 최신 기준으로 다시 계산됩니다.")


def _mismatch_scope(mismatch: pd.DataFrame) -> tuple[set[str], set[int]]:
    schools = {str(value).strip() for value in mismatch.get("school_name", []) if str(value).strip()}
    years: set[int] = set()
    for value in mismatch.get("year", []):
        try:
            years.add(int(float(value)))
        except (TypeError, ValueError):
            continue
    return schools, years


def _filter_preview_frame(frame: pd.DataFrame, mismatch: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    schools, years = _mismatch_scope(mismatch)
    if schools and years:
        return frame[frame[SCHOOL_COL].isin(schools) & frame[YEAR_COL].isin(years)].copy()
    latest_year = int(frame[YEAR_COL].max())
    return frame[frame[YEAR_COL] == latest_year].copy()


def _build_rate_chart_frame(operating: pd.DataFrame, candidate: pd.DataFrame, mismatch: pd.DataFrame) -> pd.DataFrame:
    schools, years = _mismatch_scope(mismatch)
    if not schools:
        schools = set(operating[SCHOOL_COL].dropna().astype(str).head(5))
    if not years:
        years = set(operating[YEAR_COL].dropna().astype(int).tail(3))

    chart_frames: list[pd.DataFrame] = []
    for label, frame in (("운영 CSV", operating), ("Candidate CSV", candidate)):
        subset = frame[frame[SCHOOL_COL].isin(schools)].copy()
        if years:
            min_year = min(years) - 1
            max_year = max(years)
            subset = subset[(subset[YEAR_COL] >= min_year) & (subset[YEAR_COL] <= max_year)].copy()
        if subset.empty:
            continue
        subset["데이터 구분"] = label
        chart_frames.append(subset[[YEAR_COL, SCHOOL_COL, RATE_COL, "데이터 구분"]])

    if not chart_frames:
        return pd.DataFrame(columns=[YEAR_COL, SCHOOL_COL, RATE_COL, "데이터 구분"])
    return pd.concat(chart_frames, ignore_index=True)


def _render_preview_mode(context: dict[str, object]) -> None:
    mismatch = context["mismatch"]
    operating = get_dataset(DORMITORY_PAGE.dataset_key)
    candidate = load_dormitory_candidate_frame()

    st.markdown("#### 화면 미리보기")
    st.write("운영 데이터와 후보 데이터를 전체 지표 화면에 반영하기 전에 필요한 범위만 단순 비교합니다.")
    source = st.radio(
        "미리보기 방식",
        ["운영 CSV", "Candidate CSV", "차이 발생 항목만 비교"],
        horizontal=True,
        key="dormitory_validation_preview_source",
    )

    if source == "운영 CSV":
        st.caption("현재 운영 화면에서 사용하는 데이터 중 차이가 발생한 학교와 연도만 보여줍니다.")
        st.dataframe(_filter_preview_frame(operating, mismatch), use_container_width=True, hide_index=True)
    elif source == "Candidate CSV":
        st.caption("원자료에서 재가공한 후보 데이터 중 차이가 발생한 학교와 연도만 보여줍니다.")
        st.dataframe(_filter_preview_frame(candidate, mismatch), use_container_width=True, hide_index=True)
    else:
        review_frame = build_mismatch_review_frame(mismatch, context["decisions"], dataset_id=context["status"].dataset_id)
        st.dataframe(
            review_frame.drop(columns=["검토키"], errors="ignore"),
            use_container_width=True,
            hide_index=True,
        )

    chart_frame = _build_rate_chart_frame(operating, candidate, mismatch)
    if chart_frame.empty:
        st.info("미리보기 차트를 만들 데이터가 없습니다.")
        return

    st.markdown("#### 기숙사 수용률 추이 비교")
    figure = px.line(
        chart_frame,
        x=YEAR_COL,
        y=RATE_COL,
        color=SCHOOL_COL,
        line_dash="데이터 구분",
        markers=True,
        title="운영 CSV와 Candidate CSV 비교",
    )
    figure.update_layout(legend_title_text="", yaxis_title="기숙사 수용률(%)", xaxis_title="기준년도")
    st.plotly_chart(figure, use_container_width=True)


def _render_promotion_readiness(context: dict[str, object]) -> None:
    status = context["status"]
    review_status = context["review_status"]

    st.markdown("#### 승격 준비")
    _render_status_cards(status, review_status)
    st.write("이 단계는 운영 반영 실행이 아니라, 운영 반영을 요청할 수 있는 상태인지 판단하는 화면입니다.")

    criteria = [
        ("원자료 XLSX 보존", status.raw_preserved),
        ("Candidate CSV 생성", status.candidate_exists),
        ("처리 보고서 생성", status.report_exists),
        ("high mismatch 0건", status.high_mismatches == 0),
        ("모든 차이 항목 검토 완료", review_status.pending == 0),
        ("추가 확인 필요 0건", review_status.needs_followup == 0),
        ("운영값 유지 항목 메모 작성", review_status.missing_required_notes == 0),
    ]
    for label, passed in criteria:
        st.write(("완료: " if passed else "확인 필요: ") + label)

    if review_status.ready_for_promotion:
        st.success("승격 준비 조건을 충족했습니다. 실제 운영 반영은 별도 커밋/PR 절차로 진행해야 합니다.")
    else:
        _render_review_summary(review_status)

    st.button(
        "운영 CSV로 승격",
        disabled=True,
        help="현재 단계에서는 실수 방지를 위해 운영 CSV 자동 교체 기능을 제공하지 않습니다.",
    )
    st.caption("이 버튼은 의도적으로 비활성화되어 있으며, 운영 데이터 파일은 이 화면에서 변경되지 않습니다.")


def main() -> None:
    st.set_page_config(
        page_title="데이터 검증 | 대학알리미 시각화 대시보드",
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    auth_user = require_authenticated_user()
    apply_app_theme()

    if not auth_user.is_admin:
        st.title("데이터 검증")
        st.error("데이터 검증 모드는 운영자만 접근할 수 있습니다.")
        st.stop()

    context = _build_context()

    st.title("데이터 검증")
    st.caption(f"{APP_SUBTITLE} | 운영자 전용")
    st.info("현재 파일럿 대상은 기숙사 수용률입니다. 운영 CSV는 이 화면에서 변경되지 않습니다.")
    _render_status_cards(context["status"], context["review_status"])

    tab_check, tab_review, tab_preview, tab_promotion = st.tabs(
        ["자동 점검", "차이 검토", "화면 미리보기", "승격 준비"]
    )
    with tab_check:
        _render_auto_check(context)
    with tab_review:
        _render_review_mode(context)
    with tab_preview:
        _render_preview_mode(context)
    with tab_promotion:
        _render_promotion_readiness(context)


main()
