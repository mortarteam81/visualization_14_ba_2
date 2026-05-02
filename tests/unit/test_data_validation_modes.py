from __future__ import annotations

import json

import pandas as pd

from utils.data_validation_modes import (
    DECISION_ACCEPT_RAW,
    DECISION_KEEP_CURRENT,
    DECISION_NEEDS_CHECK,
    DECISION_PENDING,
    ReviewDecision,
    build_gyowon_validation_status,
    build_mismatch_review_frame,
    build_mismatch_review_id,
    build_research_validation_status,
    build_review_completion_status,
    build_student_recruitment_validation_status,
    load_dormitory_review_decisions,
    load_gyowon_review_decisions,
    load_research_review_decisions,
    load_student_recruitment_review_decisions,
    review_decisions_from_frame,
    save_dormitory_review_decisions,
    save_gyowon_review_decisions,
    save_research_review_decisions,
    save_student_recruitment_review_decisions,
)


def _mismatch_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "severity": "medium",
                "field": "기숙사수용률",
                "school_name": "성균관대학교",
                "year": 2025,
                "processed_value": 20.0,
                "raw_value": 20.2,
                "reason": "diff",
                "source_path": "current.csv",
            },
            {
                "severity": "medium",
                "field": "기숙사수용인원",
                "school_name": "홍익대학교",
                "year": 2025,
                "processed_value": 1380,
                "raw_value": 1354,
                "reason": "diff",
                "source_path": "current.csv",
            },
        ]
    )


def test_review_decision_save_and_load_roundtrip(tmp_path) -> None:
    review_id = build_mismatch_review_id(
        school_name="성균관대학교",
        year=2025,
        field="기숙사수용률",
    )
    path = tmp_path / "review.json"

    save_dormitory_review_decisions(
        {
            review_id: ReviewDecision(
                review_id=review_id,
                dataset_id="dormitory_accommodation_status",
                school_name="성균관대학교",
                year=2025,
                field="기숙사수용률",
                decision=DECISION_ACCEPT_RAW,
                note="원자료 기준으로 후보값 채택",
                updated_at="2026-05-02T00:00:00+00:00",
            )
        },
        path=path,
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert "email" not in json.dumps(payload, ensure_ascii=False).lower()
    loaded = load_dormitory_review_decisions(path)

    assert loaded[review_id].decision == DECISION_ACCEPT_RAW
    assert loaded[review_id].note == "원자료 기준으로 후보값 채택"


def test_mismatch_review_frame_uses_stable_review_key() -> None:
    mismatch = _mismatch_frame()
    review_id = build_mismatch_review_id(
        school_name="성균관대학교",
        year=2025,
        field="기숙사수용률",
    )
    frame = build_mismatch_review_frame(
        mismatch,
        {
            review_id: ReviewDecision(
                review_id=review_id,
                dataset_id="dormitory_accommodation_status",
                school_name="성균관대학교",
                year=2025,
                field="기숙사수용률",
                decision=DECISION_ACCEPT_RAW,
                note="확인 완료",
                updated_at="2026-05-02T00:00:00+00:00",
            )
        },
    )

    assert frame.loc[0, "검토키"] == review_id
    assert frame.loc[0, "검토 상태"] == DECISION_ACCEPT_RAW
    assert frame.loc[0, "차이"] == 0.2
    assert frame.loc[1, "검토 상태"] == DECISION_PENDING


def test_review_completion_requires_every_mismatch_to_be_reviewed() -> None:
    status = build_review_completion_status(_mismatch_frame(), {}, base_ready=True, high_mismatches=0)

    assert status.ready_for_promotion is False
    assert status.pending == 2
    assert "미검토 차이 항목이 2건 남아 있습니다." in status.reasons


def test_review_completion_blocks_followup_and_missing_keep_current_note() -> None:
    mismatch = _mismatch_frame()
    edited = build_mismatch_review_frame(mismatch)
    edited.loc[0, "검토 상태"] = DECISION_NEEDS_CHECK
    edited.loc[1, "검토 상태"] = DECISION_KEEP_CURRENT
    decisions = review_decisions_from_frame(edited, now="2026-05-02T00:00:00+00:00")

    status = build_review_completion_status(mismatch, decisions, base_ready=True, high_mismatches=0)

    assert status.ready_for_promotion is False
    assert status.needs_followup == 1
    assert status.missing_required_notes == 1


def test_review_completion_allows_reviewed_items_with_required_notes() -> None:
    mismatch = _mismatch_frame()
    edited = build_mismatch_review_frame(mismatch)
    edited.loc[0, "검토 상태"] = DECISION_ACCEPT_RAW
    edited.loc[1, "검토 상태"] = DECISION_KEEP_CURRENT
    edited.loc[1, "검토 메모"] = "후속 검토 결과 운영값 유지"
    decisions = review_decisions_from_frame(edited, now="2026-05-02T00:00:00+00:00")

    status = build_review_completion_status(mismatch, decisions, base_ready=True, high_mismatches=0)

    assert status.ready_for_promotion is True
    assert status.pending == 0
    assert status.reasons == ()


def test_student_recruitment_status_uses_preserved_raw_sources() -> None:
    status = build_student_recruitment_validation_status()

    assert status.dataset_id == "student_recruitment"
    assert status.raw_preserved is True
    assert status.candidate_exists is True
    assert status.report_exists is True
    assert status.source_input_kind == "raw_xlsx"
    assert status.candidate_rows > 0
    assert status.mismatch_rows >= status.medium_mismatches


def test_gyowon_status_uses_preserved_raw_source_and_reports_mismatch() -> None:
    status = build_gyowon_validation_status()

    assert status.dataset_id == "gyowon"
    assert status.raw_preserved is True
    assert status.candidate_exists is True
    assert status.report_exists is True
    assert status.source_input_kind == "raw_xlsx"
    assert status.source_input_rows == 4563
    assert status.candidate_rows == 3106
    assert status.mismatch_rows == 1
    assert status.high_mismatches == 0
    assert status.medium_mismatches == 1
    assert status.ready_for_preview is True
    assert status.ready_for_promotion is False


def test_research_status_uses_preserved_raw_source_and_zero_mismatches() -> None:
    status = build_research_validation_status()

    assert status.dataset_id == "research"
    assert status.raw_preserved is True
    assert status.candidate_exists is True
    assert status.report_exists is True
    assert status.source_input_kind == "raw_xlsx"
    assert status.source_input_rows == 4444
    assert status.candidate_rows == 3108
    assert status.mismatch_rows == 0
    assert status.ready_for_preview is True
    assert status.ready_for_promotion is True


def test_student_recruitment_review_decision_save_and_load_roundtrip(tmp_path) -> None:
    review_id = build_mismatch_review_id(
        dataset_id="student_recruitment",
        school_name="성신여자대학교",
        year="",
        field="재학생충원율",
    )
    path = tmp_path / "student_review.json"

    save_student_recruitment_review_decisions(
        {
            review_id: ReviewDecision(
                review_id=review_id,
                dataset_id="student_recruitment",
                school_name="성신여자대학교",
                year="",
                field="재학생충원율",
                decision=DECISION_ACCEPT_RAW,
                note="학생 충원 원자료 기준 확인",
                updated_at="2026-05-02T00:00:00+00:00",
            )
        },
        path=path,
    )

    loaded = load_student_recruitment_review_decisions(path)

    assert loaded[review_id].dataset_id == "student_recruitment"
    assert loaded[review_id].decision == DECISION_ACCEPT_RAW


def test_gyowon_review_decision_save_and_load_roundtrip(tmp_path) -> None:
    review_id = build_mismatch_review_id(
        dataset_id="gyowon",
        school_name="성균관대학교",
        year=2024,
        field="전임교원 확보율(재학생 기준)",
    )
    path = tmp_path / "gyowon_review.json"

    save_gyowon_review_decisions(
        {
            review_id: ReviewDecision(
                review_id=review_id,
                dataset_id="gyowon",
                school_name="성균관대학교",
                year=2024,
                field="전임교원 확보율(재학생 기준)",
                decision=DECISION_ACCEPT_RAW,
                note="전임교원 확보율 원자료 기준 확인",
                updated_at="2026-05-02T00:00:00+00:00",
            )
        },
        path=path,
    )

    loaded = load_gyowon_review_decisions(path)

    assert loaded[review_id].dataset_id == "gyowon"
    assert loaded[review_id].decision == DECISION_ACCEPT_RAW


def test_research_review_decision_save_and_load_roundtrip(tmp_path) -> None:
    review_id = build_mismatch_review_id(
        dataset_id="research",
        school_name="성신여자대학교",
        year=2024,
        field="전임교원 1인당 연구비(교외)",
    )
    path = tmp_path / "research_review.json"

    save_research_review_decisions(
        {
            review_id: ReviewDecision(
                review_id=review_id,
                dataset_id="research",
                school_name="성신여자대학교",
                year=2024,
                field="전임교원 1인당 연구비(교외)",
                decision=DECISION_ACCEPT_RAW,
                note="연구비 원자료 기준 확인",
                updated_at="2026-05-02T00:00:00+00:00",
            )
        },
        path=path,
    )

    loaded = load_research_review_decisions(path)

    assert loaded[review_id].dataset_id == "research"
    assert loaded[review_id].decision == DECISION_ACCEPT_RAW
