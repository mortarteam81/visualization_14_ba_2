"""Data validation modes for candidate source pipelines."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DORMITORY_CANDIDATE_PATH = (
    PROJECT_ROOT
    / "data"
    / "conversion_outputs"
    / "academyinfo"
    / "dormitory_accommodation_status"
    / "dormitory_accommodation_status_2025_candidate.csv"
)
DORMITORY_REPORT_PATH = (
    PROJECT_ROOT
    / "data"
    / "validation"
    / "processing_reports"
    / "academyinfo_dormitory_accommodation_status.processing_report.json"
)
DORMITORY_MISMATCH_PATH = (
    PROJECT_ROOT
    / "data"
    / "validation"
    / "mismatch_reports"
    / "academyinfo_dormitory_accommodation_status.mismatch.csv"
)
DORMITORY_SOURCE_ACQUISITION_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "academyinfo"
    / "dormitory_accommodation_status"
    / "source_acquisition.json"
)
DORMITORY_REVIEW_DECISIONS_PATH = (
    PROJECT_ROOT
    / "data"
    / "validation"
    / "review_decisions"
    / "academyinfo_dormitory_accommodation_status.review.json"
)
GYOWON_CANDIDATE_PATH = (
    PROJECT_ROOT
    / "data"
    / "conversion_outputs"
    / "academyinfo"
    / "gyowon"
    / "gyowon_2008_2025_candidate.csv"
)
GYOWON_REPORT_PATH = (
    PROJECT_ROOT
    / "data"
    / "validation"
    / "processing_reports"
    / "academyinfo_gyowon.processing_report.json"
)
GYOWON_MISMATCH_PATH = (
    PROJECT_ROOT
    / "data"
    / "validation"
    / "mismatch_reports"
    / "academyinfo_gyowon.mismatch.csv"
)
GYOWON_SOURCE_ACQUISITION_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "academyinfo"
    / "gyowon"
    / "source_acquisition.json"
)
GYOWON_REVIEW_DECISIONS_PATH = (
    PROJECT_ROOT
    / "data"
    / "validation"
    / "review_decisions"
    / "academyinfo_gyowon.review.json"
)
RESEARCH_CANDIDATE_PATH = (
    PROJECT_ROOT
    / "data"
    / "conversion_outputs"
    / "academyinfo"
    / "research"
    / "research_2007_2024_candidate.csv"
)
RESEARCH_REPORT_PATH = (
    PROJECT_ROOT
    / "data"
    / "validation"
    / "processing_reports"
    / "academyinfo_research.processing_report.json"
)
RESEARCH_MISMATCH_PATH = (
    PROJECT_ROOT
    / "data"
    / "validation"
    / "mismatch_reports"
    / "academyinfo_research.mismatch.csv"
)
RESEARCH_SOURCE_ACQUISITION_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "academyinfo"
    / "research"
    / "source_acquisition.json"
)
RESEARCH_REVIEW_DECISIONS_PATH = (
    PROJECT_ROOT
    / "data"
    / "validation"
    / "review_decisions"
    / "academyinfo_research.review.json"
)
PAPER_CANDIDATE_PATH = (
    PROJECT_ROOT
    / "data"
    / "conversion_outputs"
    / "academyinfo"
    / "paper"
    / "paper_2007_2024_candidate.csv"
)
PAPER_REPORT_PATH = (
    PROJECT_ROOT
    / "data"
    / "validation"
    / "processing_reports"
    / "academyinfo_paper.processing_report.json"
)
PAPER_MISMATCH_PATH = (
    PROJECT_ROOT
    / "data"
    / "validation"
    / "mismatch_reports"
    / "academyinfo_paper.mismatch.csv"
)
PAPER_SOURCE_ACQUISITION_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "academyinfo"
    / "paper"
    / "source_acquisition.json"
)
PAPER_REVIEW_DECISIONS_PATH = (
    PROJECT_ROOT
    / "data"
    / "validation"
    / "review_decisions"
    / "academyinfo_paper.review.json"
)
JIROSUNG_CANDIDATE_PATH = (
    PROJECT_ROOT
    / "data"
    / "conversion_outputs"
    / "academyinfo"
    / "jirosung"
    / "jirosung_2008_2024_candidate.csv"
)
JIROSUNG_REPORT_PATH = (
    PROJECT_ROOT
    / "data"
    / "validation"
    / "processing_reports"
    / "academyinfo_jirosung.processing_report.json"
)
JIROSUNG_MISMATCH_PATH = (
    PROJECT_ROOT
    / "data"
    / "validation"
    / "mismatch_reports"
    / "academyinfo_jirosung.mismatch.csv"
)
JIROSUNG_SOURCE_ACQUISITION_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "academyinfo"
    / "jirosung"
    / "source_acquisition.json"
)
JIROSUNG_REVIEW_DECISIONS_PATH = (
    PROJECT_ROOT
    / "data"
    / "validation"
    / "review_decisions"
    / "academyinfo_jirosung.review.json"
)
STUDENT_RECRUITMENT_CURRENT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "student_recruitment"
    / "student_recruitment_2026_candidate.csv"
)
STUDENT_RECRUITMENT_CANDIDATE_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "student_recruitment"
    / "student_recruitment_2026_candidate_v2.csv"
)
STUDENT_RECRUITMENT_REPORT_PATH = (
    PROJECT_ROOT
    / "data"
    / "validation"
    / "processing_reports"
    / "student_recruitment_2026_v2.processing_report.json"
)
STUDENT_RECRUITMENT_MISMATCH_PATH = (
    PROJECT_ROOT
    / "data"
    / "validation"
    / "mismatch_reports"
    / "student_recruitment_2026_v2.mismatch.csv"
)
STUDENT_RECRUITMENT_SOURCE_PATH = PROJECT_ROOT / "data" / "metadata" / "student_recruitment.source.json"
STUDENT_RECRUITMENT_REVIEW_DECISIONS_PATH = (
    PROJECT_ROOT
    / "data"
    / "validation"
    / "review_decisions"
    / "student_recruitment_2026_v2.review.json"
)

DORMITORY_DATASET_ID = "dormitory_accommodation_status"
GYOWON_DATASET_ID = "gyowon"
RESEARCH_DATASET_ID = "research"
PAPER_DATASET_ID = "paper"
JIROSUNG_DATASET_ID = "jirosung"
STUDENT_RECRUITMENT_DATASET_ID = "student_recruitment"
DECISION_PENDING = "미검토"
DECISION_ACCEPT_RAW = "원자료값 채택"
DECISION_KEEP_CURRENT = "운영값 유지"
DECISION_NEEDS_CHECK = "추가 확인 필요"
REVIEW_DECISIONS = (
    DECISION_PENDING,
    DECISION_ACCEPT_RAW,
    DECISION_KEEP_CURRENT,
    DECISION_NEEDS_CHECK,
)


@dataclass(frozen=True)
class ValidationModeStatus:
    dataset_id: str
    candidate_exists: bool
    report_exists: bool
    mismatch_exists: bool
    raw_preserved: bool
    source_input_kind: str | None
    source_input_rows: int
    candidate_rows: int
    mismatch_rows: int
    high_mismatches: int
    medium_mismatches: int
    ready_for_preview: bool
    ready_for_promotion: bool
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "dataset_id": self.dataset_id,
            "candidate_exists": self.candidate_exists,
            "report_exists": self.report_exists,
            "mismatch_exists": self.mismatch_exists,
            "raw_preserved": self.raw_preserved,
            "source_input_kind": self.source_input_kind,
            "source_input_rows": self.source_input_rows,
            "candidate_rows": self.candidate_rows,
            "mismatch_rows": self.mismatch_rows,
            "high_mismatches": self.high_mismatches,
            "medium_mismatches": self.medium_mismatches,
            "ready_for_preview": self.ready_for_preview,
            "ready_for_promotion": self.ready_for_promotion,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ReviewDecision:
    review_id: str
    dataset_id: str
    school_name: str
    year: int | str
    field: str
    decision: str
    note: str
    updated_at: str

    def to_dict(self) -> dict[str, object]:
        return {
            "review_id": self.review_id,
            "dataset_id": self.dataset_id,
            "school_name": self.school_name,
            "year": self.year,
            "field": self.field,
            "decision": self.decision,
            "note": self.note,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class ReviewCompletionStatus:
    total: int
    reviewed: int
    pending: int
    needs_followup: int
    missing_required_notes: int
    ready_for_promotion: bool
    reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "total": self.total,
            "reviewed": self.reviewed,
            "pending": self.pending,
            "needs_followup": self.needs_followup,
            "missing_required_notes": self.missing_required_notes,
            "ready_for_promotion": self.ready_for_promotion,
            "reasons": list(self.reasons),
        }


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _clean_text(value: object) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()


def _clean_year(value: object) -> int | str:
    if value is None:
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return _clean_text(value)
    if pd.isna(number):
        return ""
    if number.is_integer():
        return int(number)
    return _clean_text(value)


def _numeric_difference(raw_value: object, processed_value: object) -> float | str:
    try:
        raw_number = float(raw_value)
        processed_number = float(processed_value)
    except (TypeError, ValueError):
        return ""
    if pd.isna(raw_number) or pd.isna(processed_number):
        return ""
    return round(raw_number - processed_number, 6)


def normalize_review_decision(value: object) -> str:
    decision = _clean_text(value)
    if decision in REVIEW_DECISIONS:
        return decision
    return DECISION_PENDING


def build_mismatch_review_id(
    *,
    dataset_id: str = DORMITORY_DATASET_ID,
    school_name: object,
    year: object,
    field: object,
) -> str:
    return "::".join(
        [
            _clean_text(dataset_id) or DORMITORY_DATASET_ID,
            _clean_text(school_name),
            str(_clean_year(year)),
            _clean_text(field),
        ]
    )


def load_dormitory_candidate_frame() -> pd.DataFrame:
    return pd.read_csv(DORMITORY_CANDIDATE_PATH, encoding="utf-8-sig")


def load_gyowon_candidate_frame() -> pd.DataFrame:
    return pd.read_csv(GYOWON_CANDIDATE_PATH, encoding="utf-8-sig")


def load_research_candidate_frame() -> pd.DataFrame:
    return pd.read_csv(RESEARCH_CANDIDATE_PATH, encoding="utf-8-sig")


def load_paper_candidate_frame() -> pd.DataFrame:
    return pd.read_csv(PAPER_CANDIDATE_PATH, encoding="utf-8-sig")


def load_jirosung_candidate_frame() -> pd.DataFrame:
    return pd.read_csv(JIROSUNG_CANDIDATE_PATH, encoding="utf-8-sig")


def load_student_recruitment_current_frame() -> pd.DataFrame:
    return pd.read_csv(STUDENT_RECRUITMENT_CURRENT_PATH, encoding="utf-8-sig")


def load_student_recruitment_candidate_frame() -> pd.DataFrame:
    return pd.read_csv(STUDENT_RECRUITMENT_CANDIDATE_PATH, encoding="utf-8-sig")


def load_dormitory_mismatch_frame() -> pd.DataFrame:
    if not DORMITORY_MISMATCH_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(DORMITORY_MISMATCH_PATH, encoding="utf-8-sig")


def load_gyowon_mismatch_frame() -> pd.DataFrame:
    if not GYOWON_MISMATCH_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(GYOWON_MISMATCH_PATH, encoding="utf-8-sig")


def load_research_mismatch_frame() -> pd.DataFrame:
    if not RESEARCH_MISMATCH_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(RESEARCH_MISMATCH_PATH, encoding="utf-8-sig")


def load_paper_mismatch_frame() -> pd.DataFrame:
    if not PAPER_MISMATCH_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(PAPER_MISMATCH_PATH, encoding="utf-8-sig")


def load_jirosung_mismatch_frame() -> pd.DataFrame:
    if not JIROSUNG_MISMATCH_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(JIROSUNG_MISMATCH_PATH, encoding="utf-8-sig")


def load_student_recruitment_mismatch_frame() -> pd.DataFrame:
    if not STUDENT_RECRUITMENT_MISMATCH_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(STUDENT_RECRUITMENT_MISMATCH_PATH, encoding="utf-8-sig")


def load_dormitory_processing_report() -> dict[str, Any]:
    return _read_json(DORMITORY_REPORT_PATH)


def load_gyowon_processing_report() -> dict[str, Any]:
    return _read_json(GYOWON_REPORT_PATH)


def load_research_processing_report() -> dict[str, Any]:
    return _read_json(RESEARCH_REPORT_PATH)


def load_paper_processing_report() -> dict[str, Any]:
    return _read_json(PAPER_REPORT_PATH)


def load_jirosung_processing_report() -> dict[str, Any]:
    return _read_json(JIROSUNG_REPORT_PATH)


def load_student_recruitment_processing_report() -> dict[str, Any]:
    return _read_json(STUDENT_RECRUITMENT_REPORT_PATH)


def load_dormitory_source_acquisition() -> dict[str, Any]:
    return _read_json(DORMITORY_SOURCE_ACQUISITION_PATH)


def load_gyowon_source_acquisition() -> dict[str, Any]:
    return _read_json(GYOWON_SOURCE_ACQUISITION_PATH)


def load_research_source_acquisition() -> dict[str, Any]:
    return _read_json(RESEARCH_SOURCE_ACQUISITION_PATH)


def load_paper_source_acquisition() -> dict[str, Any]:
    return _read_json(PAPER_SOURCE_ACQUISITION_PATH)


def load_jirosung_source_acquisition() -> dict[str, Any]:
    return _read_json(JIROSUNG_SOURCE_ACQUISITION_PATH)


def load_student_recruitment_source_metadata() -> dict[str, Any]:
    return _read_json(STUDENT_RECRUITMENT_SOURCE_PATH)


def _source_raw_files_exist(source_payload: Mapping[str, Any]) -> bool:
    raw_files = source_payload.get("raw_files", [])
    if not isinstance(raw_files, list) or not raw_files:
        return False
    for item in raw_files:
        if not isinstance(item, Mapping):
            return False
        relative_path = _clean_text(item.get("path"))
        if not relative_path or not (PROJECT_ROOT / relative_path).exists():
            return False
    return True


def review_decision_from_dict(payload: Mapping[str, object]) -> ReviewDecision | None:
    dataset_id = _clean_text(payload.get("dataset_id")) or DORMITORY_DATASET_ID
    school_name = _clean_text(payload.get("school_name"))
    year = _clean_year(payload.get("year"))
    field = _clean_text(payload.get("field"))
    review_id = _clean_text(payload.get("review_id")) or build_mismatch_review_id(
        dataset_id=dataset_id,
        school_name=school_name,
        year=year,
        field=field,
    )
    if not school_name or not field:
        return None
    return ReviewDecision(
        review_id=review_id,
        dataset_id=dataset_id,
        school_name=school_name,
        year=year,
        field=field,
        decision=normalize_review_decision(payload.get("decision")),
        note=_clean_text(payload.get("note")),
        updated_at=_clean_text(payload.get("updated_at")),
    )


def load_dormitory_review_decisions(
    path: Path | str = DORMITORY_REVIEW_DECISIONS_PATH,
) -> dict[str, ReviewDecision]:
    payload = _read_json(Path(path))
    raw_decisions = payload.get("decisions", []) if isinstance(payload, dict) else []
    if not isinstance(raw_decisions, list):
        return {}

    decisions: dict[str, ReviewDecision] = {}
    for item in raw_decisions:
        if not isinstance(item, dict):
            continue
        decision = review_decision_from_dict(item)
        if decision is not None:
            decisions[decision.review_id] = decision
    return decisions


def load_student_recruitment_review_decisions(
    path: Path | str = STUDENT_RECRUITMENT_REVIEW_DECISIONS_PATH,
) -> dict[str, ReviewDecision]:
    return load_dormitory_review_decisions(path)


def load_gyowon_review_decisions(
    path: Path | str = GYOWON_REVIEW_DECISIONS_PATH,
) -> dict[str, ReviewDecision]:
    return load_dormitory_review_decisions(path)


def load_research_review_decisions(
    path: Path | str = RESEARCH_REVIEW_DECISIONS_PATH,
) -> dict[str, ReviewDecision]:
    return load_dormitory_review_decisions(path)


def load_paper_review_decisions(
    path: Path | str = PAPER_REVIEW_DECISIONS_PATH,
) -> dict[str, ReviewDecision]:
    return load_dormitory_review_decisions(path)


def load_jirosung_review_decisions(
    path: Path | str = JIROSUNG_REVIEW_DECISIONS_PATH,
) -> dict[str, ReviewDecision]:
    return load_dormitory_review_decisions(path)


def save_dormitory_review_decisions(
    decisions: Mapping[str, ReviewDecision],
    path: Path | str = DORMITORY_REVIEW_DECISIONS_PATH,
    *,
    dataset_id: str = DORMITORY_DATASET_ID,
) -> None:
    target = Path(path)
    payload = {
        "dataset_id": dataset_id,
        "updated_at": _utc_timestamp(),
        "decisions": [
            decision.to_dict()
            for _, decision in sorted(decisions.items(), key=lambda item: item[0])
        ],
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def save_student_recruitment_review_decisions(
    decisions: Mapping[str, ReviewDecision],
    path: Path | str = STUDENT_RECRUITMENT_REVIEW_DECISIONS_PATH,
) -> None:
    save_dormitory_review_decisions(
        decisions,
        path=path,
        dataset_id=STUDENT_RECRUITMENT_DATASET_ID,
    )


def save_gyowon_review_decisions(
    decisions: Mapping[str, ReviewDecision],
    path: Path | str = GYOWON_REVIEW_DECISIONS_PATH,
) -> None:
    save_dormitory_review_decisions(
        decisions,
        path=path,
        dataset_id=GYOWON_DATASET_ID,
    )


def save_research_review_decisions(
    decisions: Mapping[str, ReviewDecision],
    path: Path | str = RESEARCH_REVIEW_DECISIONS_PATH,
) -> None:
    save_dormitory_review_decisions(
        decisions,
        path=path,
        dataset_id=RESEARCH_DATASET_ID,
    )


def save_paper_review_decisions(
    decisions: Mapping[str, ReviewDecision],
    path: Path | str = PAPER_REVIEW_DECISIONS_PATH,
) -> None:
    save_dormitory_review_decisions(
        decisions,
        path=path,
        dataset_id=PAPER_DATASET_ID,
    )


def save_jirosung_review_decisions(
    decisions: Mapping[str, ReviewDecision],
    path: Path | str = JIROSUNG_REVIEW_DECISIONS_PATH,
) -> None:
    save_dormitory_review_decisions(
        decisions,
        path=path,
        dataset_id=JIROSUNG_DATASET_ID,
    )


def build_mismatch_review_frame(
    mismatch: pd.DataFrame,
    decisions: Mapping[str, ReviewDecision] | None = None,
    *,
    dataset_id: str = DORMITORY_DATASET_ID,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    decisions = decisions or {}
    for _, row in mismatch.iterrows():
        review_id = build_mismatch_review_id(
            dataset_id=dataset_id,
            school_name=row.get("school_name"),
            year=row.get("year"),
            field=row.get("field"),
        )
        saved = decisions.get(review_id)
        rows.append(
            {
                "검토키": review_id,
                "학교": _clean_text(row.get("school_name")),
                "기준년도": _clean_year(row.get("year")),
                "확인항목": _clean_text(row.get("field")),
                "현재 운영값": row.get("processed_value"),
                "원자료 재가공값": row.get("raw_value"),
                "차이": _numeric_difference(row.get("raw_value"), row.get("processed_value")),
                "검토 상태": saved.decision if saved else DECISION_PENDING,
                "검토 메모": saved.note if saved else "",
            }
        )
    return pd.DataFrame(rows)


def review_decisions_from_frame(
    frame: pd.DataFrame,
    *,
    dataset_id: str = DORMITORY_DATASET_ID,
    now: str | None = None,
) -> dict[str, ReviewDecision]:
    updated_at = now or _utc_timestamp()
    decisions: dict[str, ReviewDecision] = {}
    for _, row in frame.iterrows():
        school_name = _clean_text(row.get("학교"))
        year = _clean_year(row.get("기준년도"))
        field = _clean_text(row.get("확인항목"))
        review_id = _clean_text(row.get("검토키")) or build_mismatch_review_id(
            dataset_id=dataset_id,
            school_name=school_name,
            year=year,
            field=field,
        )
        if not school_name or not field:
            continue
        decisions[review_id] = ReviewDecision(
            review_id=review_id,
            dataset_id=dataset_id,
            school_name=school_name,
            year=year,
            field=field,
            decision=normalize_review_decision(row.get("검토 상태")),
            note=_clean_text(row.get("검토 메모")),
            updated_at=updated_at,
        )
    return decisions


def build_review_completion_status(
    mismatch: pd.DataFrame,
    decisions: Mapping[str, ReviewDecision] | None = None,
    *,
    base_ready: bool,
    high_mismatches: int = 0,
    dataset_id: str = DORMITORY_DATASET_ID,
) -> ReviewCompletionStatus:
    decisions = decisions or {}
    total = int(len(mismatch))
    pending = 0
    needs_followup = 0
    missing_required_notes = 0

    for _, row in mismatch.iterrows():
        review_id = build_mismatch_review_id(
            dataset_id=dataset_id,
            school_name=row.get("school_name"),
            year=row.get("year"),
            field=row.get("field"),
        )
        saved = decisions.get(review_id)
        decision = saved.decision if saved else DECISION_PENDING
        note = saved.note if saved else ""
        if decision == DECISION_PENDING:
            pending += 1
        if decision == DECISION_NEEDS_CHECK:
            needs_followup += 1
        if decision == DECISION_KEEP_CURRENT and not note:
            missing_required_notes += 1

    reviewed = total - pending
    reasons: list[str] = []
    if not base_ready:
        reasons.append("원자료 보존 또는 candidate/report 생성이 아직 완료되지 않았습니다.")
    if high_mismatches:
        reasons.append("high mismatch가 있어 운영 반영 전 원인 확인이 필요합니다.")
    if pending:
        reasons.append(f"미검토 차이 항목이 {pending}건 남아 있습니다.")
    if needs_followup:
        reasons.append(f"추가 확인 필요로 표시된 항목이 {needs_followup}건 있습니다.")
    if missing_required_notes:
        reasons.append(f"운영값 유지 선택 항목 중 메모가 없는 항목이 {missing_required_notes}건 있습니다.")

    return ReviewCompletionStatus(
        total=total,
        reviewed=reviewed,
        pending=pending,
        needs_followup=needs_followup,
        missing_required_notes=missing_required_notes,
        ready_for_promotion=not reasons,
        reasons=tuple(reasons),
    )


def build_dormitory_shadow_status() -> ValidationModeStatus:
    report = load_dormitory_processing_report()
    candidate_exists = DORMITORY_CANDIDATE_PATH.exists()
    report_exists = DORMITORY_REPORT_PATH.exists()
    mismatch_exists = DORMITORY_MISMATCH_PATH.exists()
    mismatch = load_dormitory_mismatch_frame()

    row_counts = report.get("row_counts", {}) if isinstance(report, dict) else {}
    source_preservation_status = report.get("source_preservation_status") if isinstance(report, dict) else None
    source_input_kind = report.get("source_input_kind") if isinstance(report, dict) else None

    high_mismatches = int((mismatch.get("severity") == "high").sum()) if not mismatch.empty else 0
    medium_mismatches = int((mismatch.get("severity") == "medium").sum()) if not mismatch.empty else 0
    mismatch_rows = int(len(mismatch)) if mismatch_exists else int(row_counts.get("mismatch_rows", 0) or 0)
    raw_preserved = source_preservation_status == "raw_preserved"
    ready_for_preview = candidate_exists and report_exists and raw_preserved and source_input_kind == "raw_xlsx"
    review_status = build_review_completion_status(
        mismatch,
        load_dormitory_review_decisions(),
        base_ready=ready_for_preview,
        high_mismatches=high_mismatches,
        dataset_id=str(report.get("dataset_id") or DORMITORY_DATASET_ID),
    )
    ready_for_promotion = review_status.ready_for_promotion

    if not ready_for_preview:
        reason = "원자료 기반 candidate/report가 아직 완성되지 않았습니다."
    elif not ready_for_promotion:
        reason = "Preview 가능. 단, 운영 CSV와 candidate 차이에 대한 운영자 검토가 필요합니다."
    else:
        reason = "Preview 가능하며 승격 전 검토 기준을 충족했습니다."

    return ValidationModeStatus(
        dataset_id=str(report.get("dataset_id") or DORMITORY_DATASET_ID),
        candidate_exists=candidate_exists,
        report_exists=report_exists,
        mismatch_exists=mismatch_exists,
        raw_preserved=raw_preserved,
        source_input_kind=str(source_input_kind) if source_input_kind else None,
        source_input_rows=int(row_counts.get("source_input_rows", 0) or 0),
        candidate_rows=int(row_counts.get("candidate_rows", 0) or 0),
        mismatch_rows=mismatch_rows,
        high_mismatches=high_mismatches,
        medium_mismatches=medium_mismatches,
        ready_for_preview=ready_for_preview,
        ready_for_promotion=ready_for_promotion,
        reason=reason,
    )


def build_gyowon_validation_status() -> ValidationModeStatus:
    report = load_gyowon_processing_report()
    candidate_exists = GYOWON_CANDIDATE_PATH.exists()
    report_exists = GYOWON_REPORT_PATH.exists()
    mismatch_exists = GYOWON_MISMATCH_PATH.exists()
    mismatch = load_gyowon_mismatch_frame()

    row_counts = report.get("row_counts", {}) if isinstance(report, dict) else {}
    source_preservation_status = report.get("source_preservation_status") if isinstance(report, dict) else None
    source_input_kind = report.get("source_input_kind") if isinstance(report, dict) else None

    high_mismatches = int((mismatch.get("severity") == "high").sum()) if not mismatch.empty else 0
    medium_mismatches = int((mismatch.get("severity") == "medium").sum()) if not mismatch.empty else 0
    mismatch_rows = int(len(mismatch)) if mismatch_exists else int(row_counts.get("mismatch_rows", 0) or 0)
    raw_preserved = source_preservation_status == "raw_preserved"
    ready_for_preview = candidate_exists and report_exists and raw_preserved and source_input_kind == "raw_xlsx"
    review_status = build_review_completion_status(
        mismatch,
        load_gyowon_review_decisions(),
        base_ready=ready_for_preview,
        high_mismatches=high_mismatches,
        dataset_id=str(report.get("dataset_id") or GYOWON_DATASET_ID),
    )

    if not ready_for_preview:
        reason = "원자료 기반 전임교원 확보율 candidate/report가 아직 완성되지 않았습니다."
    elif not review_status.ready_for_promotion:
        reason = "Preview 가능. 단, 운영 CSV와 candidate 차이에 대한 운영자 검토가 필요합니다."
    else:
        reason = "Preview 가능하며 승격 전 검토 기준을 충족했습니다."

    return ValidationModeStatus(
        dataset_id=str(report.get("dataset_id") or GYOWON_DATASET_ID),
        candidate_exists=candidate_exists,
        report_exists=report_exists,
        mismatch_exists=mismatch_exists,
        raw_preserved=raw_preserved,
        source_input_kind=str(source_input_kind) if source_input_kind else None,
        source_input_rows=int(row_counts.get("source_input_rows", 0) or 0),
        candidate_rows=int(row_counts.get("candidate_rows", 0) or 0),
        mismatch_rows=mismatch_rows,
        high_mismatches=high_mismatches,
        medium_mismatches=medium_mismatches,
        ready_for_preview=ready_for_preview,
        ready_for_promotion=review_status.ready_for_promotion,
        reason=reason,
    )


def build_research_validation_status() -> ValidationModeStatus:
    report = load_research_processing_report()
    candidate_exists = RESEARCH_CANDIDATE_PATH.exists()
    report_exists = RESEARCH_REPORT_PATH.exists()
    mismatch_exists = RESEARCH_MISMATCH_PATH.exists()
    mismatch = load_research_mismatch_frame()

    row_counts = report.get("row_counts", {}) if isinstance(report, dict) else {}
    source_preservation_status = report.get("source_preservation_status") if isinstance(report, dict) else None
    source_input_kind = report.get("source_input_kind") if isinstance(report, dict) else None

    high_mismatches = int((mismatch.get("severity") == "high").sum()) if not mismatch.empty else 0
    medium_mismatches = int((mismatch.get("severity") == "medium").sum()) if not mismatch.empty else 0
    mismatch_rows = int(len(mismatch)) if mismatch_exists else int(row_counts.get("mismatch_rows", 0) or 0)
    raw_preserved = source_preservation_status == "raw_preserved"
    ready_for_preview = candidate_exists and report_exists and raw_preserved and source_input_kind == "raw_xlsx"
    review_status = build_review_completion_status(
        mismatch,
        load_research_review_decisions(),
        base_ready=ready_for_preview,
        high_mismatches=high_mismatches,
        dataset_id=str(report.get("dataset_id") or RESEARCH_DATASET_ID),
    )

    if not ready_for_preview:
        reason = "원자료 기반 연구비 candidate/report가 아직 완성되지 않았습니다."
    elif not review_status.ready_for_promotion:
        reason = "Preview 가능. 단, 운영 CSV와 candidate 차이에 대한 운영자 검토가 필요합니다."
    else:
        reason = "Preview 가능하며 승격 전 검토 기준을 충족했습니다."

    return ValidationModeStatus(
        dataset_id=str(report.get("dataset_id") or RESEARCH_DATASET_ID),
        candidate_exists=candidate_exists,
        report_exists=report_exists,
        mismatch_exists=mismatch_exists,
        raw_preserved=raw_preserved,
        source_input_kind=str(source_input_kind) if source_input_kind else None,
        source_input_rows=int(row_counts.get("source_input_rows", 0) or 0),
        candidate_rows=int(row_counts.get("candidate_rows", 0) or 0),
        mismatch_rows=mismatch_rows,
        high_mismatches=high_mismatches,
        medium_mismatches=medium_mismatches,
        ready_for_preview=ready_for_preview,
        ready_for_promotion=review_status.ready_for_promotion,
        reason=reason,
    )


def build_paper_validation_status() -> ValidationModeStatus:
    report = load_paper_processing_report()
    candidate_exists = PAPER_CANDIDATE_PATH.exists()
    report_exists = PAPER_REPORT_PATH.exists()
    mismatch_exists = PAPER_MISMATCH_PATH.exists()
    mismatch = load_paper_mismatch_frame()

    row_counts = report.get("row_counts", {}) if isinstance(report, dict) else {}
    source_preservation_status = report.get("source_preservation_status") if isinstance(report, dict) else None
    source_input_kind = report.get("source_input_kind") if isinstance(report, dict) else None

    high_mismatches = int((mismatch.get("severity") == "high").sum()) if not mismatch.empty else 0
    medium_mismatches = int((mismatch.get("severity") == "medium").sum()) if not mismatch.empty else 0
    mismatch_rows = int(len(mismatch)) if mismatch_exists else int(row_counts.get("mismatch_rows", 0) or 0)
    raw_preserved = source_preservation_status == "raw_preserved"
    ready_for_preview = candidate_exists and report_exists and raw_preserved and source_input_kind == "raw_xlsx"
    review_status = build_review_completion_status(
        mismatch,
        load_paper_review_decisions(),
        base_ready=ready_for_preview,
        high_mismatches=high_mismatches,
        dataset_id=str(report.get("dataset_id") or PAPER_DATASET_ID),
    )

    if not ready_for_preview:
        reason = "원자료 기반 논문실적 candidate/report가 아직 완성되지 않았습니다."
    elif not review_status.ready_for_promotion:
        reason = "Preview 가능. 단, 운영 CSV와 candidate 차이에 대한 운영자 검토가 필요합니다."
    else:
        reason = "Preview 가능하며 승격 전 검토 기준을 충족했습니다."

    return ValidationModeStatus(
        dataset_id=str(report.get("dataset_id") or PAPER_DATASET_ID),
        candidate_exists=candidate_exists,
        report_exists=report_exists,
        mismatch_exists=mismatch_exists,
        raw_preserved=raw_preserved,
        source_input_kind=str(source_input_kind) if source_input_kind else None,
        source_input_rows=int(row_counts.get("source_input_rows", 0) or 0),
        candidate_rows=int(row_counts.get("candidate_rows", 0) or 0),
        mismatch_rows=mismatch_rows,
        high_mismatches=high_mismatches,
        medium_mismatches=medium_mismatches,
        ready_for_preview=ready_for_preview,
        ready_for_promotion=review_status.ready_for_promotion,
        reason=reason,
    )


def build_jirosung_validation_status() -> ValidationModeStatus:
    report = load_jirosung_processing_report()
    candidate_exists = JIROSUNG_CANDIDATE_PATH.exists()
    report_exists = JIROSUNG_REPORT_PATH.exists()
    mismatch_exists = JIROSUNG_MISMATCH_PATH.exists()
    mismatch = load_jirosung_mismatch_frame()

    row_counts = report.get("row_counts", {}) if isinstance(report, dict) else {}
    source_preservation_status = report.get("source_preservation_status") if isinstance(report, dict) else None
    source_input_kind = report.get("source_input_kind") if isinstance(report, dict) else None

    high_mismatches = int((mismatch.get("severity") == "high").sum()) if not mismatch.empty else 0
    medium_mismatches = int((mismatch.get("severity") == "medium").sum()) if not mismatch.empty else 0
    mismatch_rows = int(len(mismatch)) if mismatch_exists else int(row_counts.get("mismatch_rows", 0) or 0)
    raw_preserved = source_preservation_status == "raw_preserved"
    ready_for_preview = candidate_exists and report_exists and raw_preserved and source_input_kind == "raw_xlsx"
    review_status = build_review_completion_status(
        mismatch,
        load_jirosung_review_decisions(),
        base_ready=ready_for_preview,
        high_mismatches=high_mismatches,
        dataset_id=str(report.get("dataset_id") or JIROSUNG_DATASET_ID),
    )

    if not ready_for_preview:
        reason = "원자료 기반 졸업생 진로 성과 candidate/report가 아직 완성되지 않았습니다."
    elif not review_status.ready_for_promotion:
        reason = "Preview 가능. 단, 운영 CSV와 candidate 차이에 대한 운영자 검토가 필요합니다."
    else:
        reason = "Preview 가능하며 승격 전 검토 기준을 충족했습니다."

    return ValidationModeStatus(
        dataset_id=str(report.get("dataset_id") or JIROSUNG_DATASET_ID),
        candidate_exists=candidate_exists,
        report_exists=report_exists,
        mismatch_exists=mismatch_exists,
        raw_preserved=raw_preserved,
        source_input_kind=str(source_input_kind) if source_input_kind else None,
        source_input_rows=int(row_counts.get("source_input_rows", 0) or 0),
        candidate_rows=int(row_counts.get("candidate_rows", 0) or 0),
        mismatch_rows=mismatch_rows,
        high_mismatches=high_mismatches,
        medium_mismatches=medium_mismatches,
        ready_for_preview=ready_for_preview,
        ready_for_promotion=review_status.ready_for_promotion,
        reason=reason,
    )


def build_student_recruitment_validation_status() -> ValidationModeStatus:
    report = load_student_recruitment_processing_report()
    source = load_student_recruitment_source_metadata()
    candidate_exists = STUDENT_RECRUITMENT_CANDIDATE_PATH.exists()
    report_exists = STUDENT_RECRUITMENT_REPORT_PATH.exists()
    mismatch_exists = STUDENT_RECRUITMENT_MISMATCH_PATH.exists()
    current_exists = STUDENT_RECRUITMENT_CURRENT_PATH.exists()
    mismatch = load_student_recruitment_mismatch_frame()

    row_counts = report.get("row_counts", {}) if isinstance(report, dict) else {}
    raw_preserved = _source_raw_files_exist(source)
    high_mismatches = int((mismatch.get("severity") == "high").sum()) if not mismatch.empty else 0
    medium_mismatches = int((mismatch.get("severity") == "medium").sum()) if not mismatch.empty else 0
    mismatch_rows = int(len(mismatch)) if mismatch_exists else int(report.get("mismatch_summary", {}).get("total", 0) or 0)
    source_input_rows = int(
        (row_counts.get("freshman_raw_2025", 0) or 0)
        + (row_counts.get("student_fill_raw_2025_first_half", 0) or 0)
        + (row_counts.get("enrolled_raw_2025", 0) or 0)
    )
    candidate_rows = int(row_counts.get("processed_candidate_v2", 0) or 0)
    ready_for_preview = current_exists and candidate_exists and report_exists and raw_preserved
    review_status = build_review_completion_status(
        mismatch,
        load_student_recruitment_review_decisions(),
        base_ready=ready_for_preview,
        high_mismatches=high_mismatches,
        dataset_id=STUDENT_RECRUITMENT_DATASET_ID,
    )

    if not ready_for_preview:
        reason = "원자료 기반 학생 충원 candidate/report가 아직 완성되지 않았습니다."
    elif not review_status.ready_for_promotion:
        reason = "Preview 가능. 단, 원자료 매칭 실패 항목에 대한 운영자 검토가 필요합니다."
    else:
        reason = "Preview 가능하며 다음 단계 검토 기준을 충족했습니다."

    return ValidationModeStatus(
        dataset_id=STUDENT_RECRUITMENT_DATASET_ID,
        candidate_exists=candidate_exists,
        report_exists=report_exists,
        mismatch_exists=mismatch_exists,
        raw_preserved=raw_preserved,
        source_input_kind="raw_xlsx" if raw_preserved else None,
        source_input_rows=source_input_rows,
        candidate_rows=candidate_rows,
        mismatch_rows=mismatch_rows,
        high_mismatches=high_mismatches,
        medium_mismatches=medium_mismatches,
        ready_for_preview=ready_for_preview,
        ready_for_promotion=review_status.ready_for_promotion,
        reason=reason,
    )
