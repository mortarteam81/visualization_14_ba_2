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
    build_budam_validation_status,
    build_dormitory_shadow_status,
    build_gyeolsan_validation_status,
    build_gyowon_validation_status,
    build_jirosung_validation_status,
    build_mismatch_review_frame,
    build_paper_validation_status,
    build_research_validation_status,
    build_review_completion_status,
    build_student_recruitment_validation_status,
    load_budam_candidate_frame,
    load_budam_mismatch_frame,
    load_budam_processing_report,
    load_budam_review_decisions,
    load_budam_source_acquisition,
    load_dormitory_candidate_frame,
    load_dormitory_mismatch_frame,
    load_dormitory_processing_report,
    load_dormitory_review_decisions,
    load_dormitory_source_acquisition,
    load_gyeolsan_candidate_frame,
    load_gyeolsan_mismatch_frame,
    load_gyeolsan_processing_report,
    load_gyeolsan_review_decisions,
    load_gyeolsan_source_acquisition,
    load_gyowon_candidate_frame,
    load_gyowon_mismatch_frame,
    load_gyowon_processing_report,
    load_gyowon_review_decisions,
    load_gyowon_source_acquisition,
    load_jirosung_candidate_frame,
    load_jirosung_mismatch_frame,
    load_jirosung_processing_report,
    load_jirosung_review_decisions,
    load_jirosung_source_acquisition,
    load_paper_candidate_frame,
    load_paper_mismatch_frame,
    load_paper_processing_report,
    load_paper_review_decisions,
    load_paper_source_acquisition,
    load_research_candidate_frame,
    load_research_mismatch_frame,
    load_research_processing_report,
    load_research_review_decisions,
    load_research_source_acquisition,
    load_student_recruitment_candidate_frame,
    load_student_recruitment_current_frame,
    load_student_recruitment_mismatch_frame,
    load_student_recruitment_processing_report,
    load_student_recruitment_review_decisions,
    load_student_recruitment_source_metadata,
    review_decisions_from_frame,
    save_budam_review_decisions,
    save_dormitory_review_decisions,
    save_gyeolsan_review_decisions,
    save_gyowon_review_decisions,
    save_jirosung_review_decisions,
    save_paper_review_decisions,
    save_research_review_decisions,
    save_student_recruitment_review_decisions,
)
from utils.query import get_dataset
from utils.theme import apply_app_theme


DORMITORY_PAGE = get_metric("dormitory_rate")
BUDAM_PAGE = get_metric("budam")
GYOWON_PAGE = get_metric("gyowon")
RESEARCH_PAGE = get_metric("research")
PAPER_PAGE = get_metric("paper")
JIROSUNG_PAGE = get_metric("jirosung")
TUITION_PAGE = get_metric("tuition")
DONATION_PAGE = get_metric("donation")
YEAR_COL = "기준년도"
SCHOOL_COL = "학교명"
RATE_COL = "기숙사수용률"
BUDAM_VALUE_COL = "부담율"
GYOWON_QUOTA_COL = "전임교원 확보율(학생정원 기준)"
GYOWON_ENROLLED_COL = "전임교원 확보율(재학생 기준)"
RESEARCH_IN_COL = "전임교원 1인당 연구비(교내)"
RESEARCH_OUT_COL = "전임교원 1인당 연구비(교외)"
PAPER_DOMESTIC_COL = "전임교원1인당논문실적(국내, 연구재단등재지(후보포함))"
PAPER_SCI_COL = "전임교원1인당논문실적(국제, SCI급/SCOPUS학술지)"
JIROSUNG_VALUE_COL = "졸업생_진로_성과"
TUITION_VALUE_COL = "등록금비율"
DONATION_VALUE_COL = "기부금비율"
STUDENT_YEAR_COL = "공시연도"
STUDENT_VALUE_COL = "재학생충원율"


def _target_config(target_key: str) -> dict[str, object]:
    if target_key == "budam":
        return {
            "target_key": "budam",
            "title": "법정부담금 부담율",
            "pilot_note": "대학알리미 원자료에서 재가공한 법정부담금 부담율 후보 데이터입니다. 운영 CSV는 이 화면에서 변경되지 않습니다.",
            "goal_text": "이 화면은 법정부담금 부담율 후보 데이터가 운영 화면에 반영 가능한지 판단하기 위한 운영자용 검증 콘솔입니다.",
            "status_loader": build_budam_validation_status,
            "mismatch_loader": load_budam_mismatch_frame,
            "decisions_loader": load_budam_review_decisions,
            "decisions_saver": save_budam_review_decisions,
            "report_loader": load_budam_processing_report,
            "source_loader": load_budam_source_acquisition,
            "operating_loader": lambda: get_dataset(BUDAM_PAGE.dataset_key),
            "candidate_loader": load_budam_candidate_frame,
            "year_col": YEAR_COL,
            "school_col": SCHOOL_COL,
            "value_col": BUDAM_VALUE_COL,
            "value_label": "법정부담금 부담율(%)",
            "chart_title": "운영 CSV와 Candidate CSV 비교",
            "promotion_button_label": "운영 CSV로 승격",
            "current_label": "운영 CSV",
            "candidate_label": "Candidate CSV",
        }
    if target_key == "gyowon":
        return {
            "target_key": "gyowon",
            "title": "전임교원 확보율",
            "pilot_note": "대학알리미 원자료에서 재가공한 전임교원 확보율 후보 데이터입니다. 운영 CSV는 이 화면에서 변경되지 않습니다.",
            "goal_text": "이 화면은 전임교원 확보율 후보 데이터가 운영 화면에 반영 가능한지 판단하기 위한 운영자용 검증 콘솔입니다.",
            "status_loader": build_gyowon_validation_status,
            "mismatch_loader": load_gyowon_mismatch_frame,
            "decisions_loader": load_gyowon_review_decisions,
            "decisions_saver": save_gyowon_review_decisions,
            "report_loader": load_gyowon_processing_report,
            "source_loader": load_gyowon_source_acquisition,
            "operating_loader": lambda: get_dataset(GYOWON_PAGE.dataset_key),
            "candidate_loader": load_gyowon_candidate_frame,
            "year_col": YEAR_COL,
            "school_col": SCHOOL_COL,
            "value_col": GYOWON_QUOTA_COL,
            "value_options": {
                "학생정원 기준": GYOWON_QUOTA_COL,
                "재학생 기준": GYOWON_ENROLLED_COL,
            },
            "value_label": "전임교원 확보율(%)",
            "chart_title": "운영 CSV와 Candidate CSV 비교",
            "promotion_button_label": "운영 CSV로 승격",
            "current_label": "운영 CSV",
            "candidate_label": "Candidate CSV",
        }
    if target_key == "research":
        return {
            "target_key": "research",
            "title": "연구비 수혜 실적",
            "pilot_note": "대학알리미 원자료에서 재가공한 연구비 후보 데이터입니다. 운영 CSV는 이 화면에서 변경되지 않습니다.",
            "goal_text": "이 화면은 연구비 수혜 실적 후보 데이터가 운영 화면에 반영 가능한지 판단하기 위한 운영자용 검증 콘솔입니다.",
            "status_loader": build_research_validation_status,
            "mismatch_loader": load_research_mismatch_frame,
            "decisions_loader": load_research_review_decisions,
            "decisions_saver": save_research_review_decisions,
            "report_loader": load_research_processing_report,
            "source_loader": load_research_source_acquisition,
            "operating_loader": lambda: get_dataset(RESEARCH_PAGE.dataset_key),
            "candidate_loader": load_research_candidate_frame,
            "year_col": YEAR_COL,
            "school_col": SCHOOL_COL,
            "value_col": RESEARCH_OUT_COL,
            "value_options": {
                "교외 연구비": RESEARCH_OUT_COL,
                "교내 연구비": RESEARCH_IN_COL,
            },
            "value_label": "전임교원 1인당 연구비(천원)",
            "chart_title": "운영 CSV와 Candidate CSV 비교",
            "promotion_button_label": "운영 CSV로 승격",
            "current_label": "운영 CSV",
            "candidate_label": "Candidate CSV",
        }
    if target_key == "paper":
        return {
            "target_key": "paper",
            "title": "논문실적",
            "pilot_note": "대학알리미 원자료에서 재가공한 논문실적 후보 데이터입니다. 운영 CSV는 이 화면에서 변경되지 않습니다.",
            "goal_text": "이 화면은 논문실적 후보 데이터가 운영 화면에 반영 가능한지 판단하기 위한 운영자용 검증 콘솔입니다.",
            "status_loader": build_paper_validation_status,
            "mismatch_loader": load_paper_mismatch_frame,
            "decisions_loader": load_paper_review_decisions,
            "decisions_saver": save_paper_review_decisions,
            "report_loader": load_paper_processing_report,
            "source_loader": load_paper_source_acquisition,
            "operating_loader": lambda: get_dataset(PAPER_PAGE.dataset_key),
            "candidate_loader": load_paper_candidate_frame,
            "year_col": YEAR_COL,
            "school_col": SCHOOL_COL,
            "value_col": PAPER_DOMESTIC_COL,
            "value_options": {
                "국내 등재지 논문": PAPER_DOMESTIC_COL,
                "SCI급·SCOPUS 논문": PAPER_SCI_COL,
            },
            "value_label": "전임교원 1인당 논문실적",
            "chart_title": "운영 CSV와 Candidate CSV 비교",
            "promotion_button_label": "운영 CSV로 승격",
            "current_label": "운영 CSV",
            "candidate_label": "Candidate CSV",
        }
    if target_key == "jirosung":
        return {
            "target_key": "jirosung",
            "title": "졸업생 진로 성과",
            "pilot_note": "대학알리미 원자료에서 재가공한 졸업생 진로 성과 후보 데이터입니다. 운영 CSV는 이 화면에서 변경되지 않습니다.",
            "goal_text": "이 화면은 졸업생 진로 성과 후보 데이터가 운영 화면에 반영 가능한지 판단하기 위한 운영자용 검증 콘솔입니다.",
            "status_loader": build_jirosung_validation_status,
            "mismatch_loader": load_jirosung_mismatch_frame,
            "decisions_loader": load_jirosung_review_decisions,
            "decisions_saver": save_jirosung_review_decisions,
            "report_loader": load_jirosung_processing_report,
            "source_loader": load_jirosung_source_acquisition,
            "operating_loader": lambda: get_dataset(JIROSUNG_PAGE.dataset_key),
            "candidate_loader": load_jirosung_candidate_frame,
            "year_col": YEAR_COL,
            "school_col": SCHOOL_COL,
            "value_col": JIROSUNG_VALUE_COL,
            "value_label": "졸업생 진로 성과(%)",
            "chart_title": "운영 CSV와 Candidate CSV 비교",
            "promotion_button_label": "운영 CSV로 승격",
            "current_label": "운영 CSV",
            "candidate_label": "Candidate CSV",
        }
    if target_key == "tuition":
        return {
            "target_key": "tuition",
            "title": "세입 중 등록금 비율",
            "pilot_note": "사학재정알리미 통합 결산 원자료에서 재가공한 세입 중 등록금 비율 후보 데이터입니다. 운영 CSV는 이 화면에서 변경되지 않습니다.",
            "goal_text": "이 화면은 세입 중 등록금 비율 후보 데이터가 운영 화면에 반영 가능한지 판단하기 위한 운영자용 검증 콘솔입니다.",
            "status_loader": build_gyeolsan_validation_status,
            "mismatch_loader": load_gyeolsan_mismatch_frame,
            "decisions_loader": load_gyeolsan_review_decisions,
            "decisions_saver": save_gyeolsan_review_decisions,
            "report_loader": load_gyeolsan_processing_report,
            "source_loader": load_gyeolsan_source_acquisition,
            "operating_loader": lambda: get_dataset(TUITION_PAGE.dataset_key),
            "candidate_loader": load_gyeolsan_candidate_frame,
            "year_col": YEAR_COL,
            "school_col": SCHOOL_COL,
            "value_col": TUITION_VALUE_COL,
            "value_label": "등록금 비율(%)",
            "chart_title": "운영 CSV와 Candidate CSV 비교",
            "promotion_button_label": "운영 CSV로 승격",
            "current_label": "운영 CSV",
            "candidate_label": "Candidate CSV",
        }
    if target_key == "donation":
        return {
            "target_key": "donation",
            "title": "세입 중 기부금 비율",
            "pilot_note": "사학재정알리미 통합 결산 원자료에서 재가공한 세입 중 기부금 비율 후보 데이터입니다. 운영 CSV는 이 화면에서 변경되지 않습니다.",
            "goal_text": "이 화면은 세입 중 기부금 비율 후보 데이터가 운영 화면에 반영 가능한지 판단하기 위한 운영자용 검증 콘솔입니다.",
            "status_loader": build_gyeolsan_validation_status,
            "mismatch_loader": load_gyeolsan_mismatch_frame,
            "decisions_loader": load_gyeolsan_review_decisions,
            "decisions_saver": save_gyeolsan_review_decisions,
            "report_loader": load_gyeolsan_processing_report,
            "source_loader": load_gyeolsan_source_acquisition,
            "operating_loader": lambda: get_dataset(DONATION_PAGE.dataset_key),
            "candidate_loader": load_gyeolsan_candidate_frame,
            "year_col": YEAR_COL,
            "school_col": SCHOOL_COL,
            "value_col": DONATION_VALUE_COL,
            "value_label": "기부금 비율(%)",
            "chart_title": "운영 CSV와 Candidate CSV 비교",
            "promotion_button_label": "운영 CSV로 승격",
            "current_label": "운영 CSV",
            "candidate_label": "Candidate CSV",
        }
    if target_key == "student_recruitment":
        return {
            "target_key": "student_recruitment",
            "title": "학생 충원 성과",
            "pilot_note": "대학알리미 원자료 3종을 병합한 학생 충원 후보 데이터입니다. 운영 CSV는 이 화면에서 변경되지 않습니다.",
            "goal_text": "이 화면은 학생 충원 성과 후보 데이터가 다음 검증 단계로 넘어갈 수 있는지 판단하기 위한 운영자용 검증 콘솔입니다.",
            "status_loader": build_student_recruitment_validation_status,
            "mismatch_loader": load_student_recruitment_mismatch_frame,
            "decisions_loader": load_student_recruitment_review_decisions,
            "decisions_saver": save_student_recruitment_review_decisions,
            "report_loader": load_student_recruitment_processing_report,
            "source_loader": load_student_recruitment_source_metadata,
            "operating_loader": load_student_recruitment_current_frame,
            "candidate_loader": load_student_recruitment_candidate_frame,
            "year_col": STUDENT_YEAR_COL,
            "school_col": SCHOOL_COL,
            "value_col": STUDENT_VALUE_COL,
            "value_label": "재학생 충원율(%)",
            "chart_title": "기존 후보 CSV와 원자료 병합 Candidate CSV 비교",
            "promotion_button_label": "다음 단계로 승격",
            "current_label": "기존 후보 CSV",
            "candidate_label": "Candidate CSV",
        }
    return {
        "target_key": "dormitory_accommodation_status",
        "title": "기숙사 수용률",
        "pilot_note": "현재 파일럿 대상은 기숙사 수용률입니다. 운영 CSV는 이 화면에서 변경되지 않습니다.",
        "goal_text": "이 화면은 기숙사 수용률 후보 데이터가 운영 화면에 반영 가능한지 판단하기 위한 운영자용 검증 콘솔입니다.",
        "status_loader": build_dormitory_shadow_status,
        "mismatch_loader": load_dormitory_mismatch_frame,
        "decisions_loader": load_dormitory_review_decisions,
        "decisions_saver": save_dormitory_review_decisions,
        "report_loader": load_dormitory_processing_report,
        "source_loader": load_dormitory_source_acquisition,
        "operating_loader": lambda: get_dataset(DORMITORY_PAGE.dataset_key),
        "candidate_loader": load_dormitory_candidate_frame,
        "year_col": YEAR_COL,
        "school_col": SCHOOL_COL,
        "value_col": RATE_COL,
        "value_label": "기숙사 수용률(%)",
        "chart_title": "운영 CSV와 Candidate CSV 비교",
        "promotion_button_label": "운영 CSV로 승격",
        "current_label": "운영 CSV",
        "candidate_label": "Candidate CSV",
    }


def _build_context(target_key: str) -> dict[str, object]:
    config = _target_config(target_key)
    status = config["status_loader"]()
    mismatch = config["mismatch_loader"]()
    decisions = config["decisions_loader"]()
    review_status = build_review_completion_status(
        mismatch,
        decisions,
        base_ready=status.ready_for_preview,
        high_mismatches=status.high_mismatches,
        dataset_id=status.dataset_id,
    )
    return {
        "config": config,
        "status": status,
        "mismatch": mismatch,
        "decisions": decisions,
        "review_status": review_status,
    }


def _render_goal(context: dict[str, object]) -> None:
    config = context["config"]
    st.markdown("#### 이번 검증의 목표")
    st.write(config["goal_text"])
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
    config = context["config"]
    status = context["status"]
    review_status = context["review_status"]
    report = config["report_loader"]()
    acquisition = config["source_loader"]()

    _render_goal(context)
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
    config = context["config"]
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
        key=f"{config['target_key']}_review_editor",
    )

    st.caption(f"`{DECISION_KEEP_CURRENT}`는 메모가 있어야 검토 완료로 인정됩니다.")
    if st.button("검토 결과 저장", type="primary", key=f"save_{config['target_key']}_review_decisions"):
        config["decisions_saver"](
            review_decisions_from_frame(edited, dataset_id=status.dataset_id),
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


def _filter_preview_frame(
    frame: pd.DataFrame,
    mismatch: pd.DataFrame,
    *,
    school_col: str,
    year_col: str,
) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    schools, years = _mismatch_scope(mismatch)
    if school_col not in frame.columns:
        return frame.copy()
    if schools and years:
        if year_col not in frame.columns:
            return frame[frame[school_col].isin(schools)].copy()
        return frame[frame[school_col].isin(schools) & frame[year_col].isin(years)].copy()
    if schools:
        return frame[frame[school_col].isin(schools)].copy()
    if year_col not in frame.columns:
        return frame.head(50).copy()
    latest_year = int(frame[year_col].max())
    return frame[frame[year_col] == latest_year].copy()


def _build_value_chart_frame(
    operating: pd.DataFrame,
    candidate: pd.DataFrame,
    mismatch: pd.DataFrame,
    *,
    school_col: str,
    year_col: str,
    value_col: str,
    current_label: str,
    candidate_label: str,
) -> pd.DataFrame:
    schools, years = _mismatch_scope(mismatch)
    if not schools:
        schools = set(operating[school_col].dropna().astype(str).head(5))
    if not years:
        years = set(operating[year_col].dropna().astype(int).tail(3)) if year_col in operating.columns else set()

    chart_frames: list[pd.DataFrame] = []
    for label, frame in ((current_label, operating), (candidate_label, candidate)):
        required = {school_col, value_col}
        if not required.issubset(frame.columns):
            continue
        subset = frame[frame[school_col].isin(schools)].copy()
        if years and year_col in subset.columns:
            min_year = min(years) - 1
            max_year = max(years)
            subset = subset[(subset[year_col] >= min_year) & (subset[year_col] <= max_year)].copy()
        if subset.empty:
            continue
        subset["데이터 구분"] = label
        keep_columns = [school_col, value_col, "데이터 구분"]
        if year_col in subset.columns:
            keep_columns.insert(0, year_col)
        chart_frames.append(subset[keep_columns])

    if not chart_frames:
        return pd.DataFrame(columns=[year_col, school_col, value_col, "데이터 구분"])
    return pd.concat(chart_frames, ignore_index=True)


def _render_preview_mode(context: dict[str, object]) -> None:
    config = context["config"]
    mismatch = context["mismatch"]
    operating = config["operating_loader"]()
    candidate = config["candidate_loader"]()
    school_col = str(config["school_col"])
    year_col = str(config["year_col"])
    value_options = config.get("value_options")
    if isinstance(value_options, dict) and value_options:
        selected_value_label = st.selectbox(
            "미리보기 지표",
            list(value_options.keys()),
            key=f"{config['target_key']}_validation_preview_metric",
        )
        value_col = str(value_options[selected_value_label])
    else:
        value_col = str(config["value_col"])

    st.markdown("#### 화면 미리보기")
    st.write("운영 데이터와 후보 데이터를 전체 지표 화면에 반영하기 전에 필요한 범위만 단순 비교합니다.")
    source = st.radio(
        "미리보기 방식",
        [str(config["current_label"]), str(config["candidate_label"]), "차이 발생 항목만 비교"],
        horizontal=True,
        key=f"{config['target_key']}_validation_preview_source",
    )

    if source == config["current_label"]:
        st.caption("현재 기준 데이터 중 차이가 발생한 학교와 연도만 보여줍니다.")
        st.dataframe(
            _filter_preview_frame(operating, mismatch, school_col=school_col, year_col=year_col),
            use_container_width=True,
            hide_index=True,
        )
    elif source == config["candidate_label"]:
        st.caption("원자료에서 재가공한 후보 데이터 중 차이가 발생한 학교와 연도만 보여줍니다.")
        st.dataframe(
            _filter_preview_frame(candidate, mismatch, school_col=school_col, year_col=year_col),
            use_container_width=True,
            hide_index=True,
        )
    else:
        review_frame = build_mismatch_review_frame(mismatch, context["decisions"], dataset_id=context["status"].dataset_id)
        st.dataframe(
            review_frame.drop(columns=["검토키"], errors="ignore"),
            use_container_width=True,
            hide_index=True,
        )

    chart_frame = _build_value_chart_frame(
        operating,
        candidate,
        mismatch,
        school_col=school_col,
        year_col=year_col,
        value_col=value_col,
        current_label=str(config["current_label"]),
        candidate_label=str(config["candidate_label"]),
    )
    if chart_frame.empty:
        st.info("미리보기 차트를 만들 데이터가 없습니다.")
        return

    st.markdown(f"#### {config['title']} 추이 비교")
    figure = px.line(
        chart_frame,
        x=year_col if year_col in chart_frame.columns else "데이터 구분",
        y=value_col,
        color=school_col,
        line_dash="데이터 구분",
        markers=True,
        title=str(config["chart_title"]),
    )
    figure.update_layout(legend_title_text="", yaxis_title=str(config["value_label"]), xaxis_title=year_col)
    st.plotly_chart(figure, use_container_width=True)


def _render_promotion_readiness(context: dict[str, object]) -> None:
    config = context["config"]
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
        str(config["promotion_button_label"]),
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

    st.title("데이터 검증")
    st.caption(f"{APP_SUBTITLE} | 운영자 전용")
    target_label = st.selectbox(
        "검증 대상",
        [
            "기숙사 수용률",
            "법정부담금 부담율",
            "전임교원 확보율",
            "연구비 수혜 실적",
            "논문실적",
            "졸업생 진로 성과",
            "세입 중 등록금 비율",
            "세입 중 기부금 비율",
            "학생 충원 성과",
        ],
        key="data_validation_target_label",
    )
    target_key_map = {
        "기숙사 수용률": "dormitory_accommodation_status",
        "법정부담금 부담율": "budam",
        "전임교원 확보율": "gyowon",
        "연구비 수혜 실적": "research",
        "논문실적": "paper",
        "졸업생 진로 성과": "jirosung",
        "세입 중 등록금 비율": "tuition",
        "세입 중 기부금 비율": "donation",
        "학생 충원 성과": "student_recruitment",
    }
    target_key = target_key_map[target_label]
    context = _build_context(target_key)
    st.info(str(context["config"]["pilot_note"]))
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
