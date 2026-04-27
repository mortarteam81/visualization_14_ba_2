from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Final, Literal

from utils.ai_prompts import build_management_prompts
from utils.ai_providers import LMStudioClient


AnalysisMode = Literal["single_year", "year_range"]

CORE_PAYLOAD_SECTIONS: Final[set[str]] = {
    "analysis_mode",
    "year",
    "start_year",
    "end_year",
    "available_years_in_range",
    "focus_school",
    "comparison_schools",
    "included_series_count",
    "excluded_pending_metric_count",
    "coverage",
    "guardrails",
}

DEFAULT_MANAGEMENT_ANALYSIS_RESULT: Final[dict[str, Any]] = {
    "summary": "",
    "evidence": [],
    "management_implications": [],
    "recommended_actions": [],
    "risks": [],
    "caveats": [],
    "data_used": {},
}

RAW_ARTIFACT_PATTERNS: Final[tuple[str, ...]] = (
    "data/raw/pending_manual/logs",
    "academyinfo_cookies.txt",
    "academyinfo_trend_cookies.txt",
    "cookies.txt",
    ".html",
    ".json",
)

CAUSAL_ASSERTION_PATTERNS: Final[tuple[str, ...]] = (
    "때문에",
    "원인이다",
    "원인으로",
    "초래",
    "입증",
    "증명",
    "결정적",
    "caused",
    "proves",
)

UNSUPPORTED_CERTAINTY_PATTERNS: Final[tuple[str, ...]] = (
    "반드시",
    "확실히",
    "명백히",
    "틀림없이",
    "무조건",
)

PENDING_METRIC_TERMS: Final[tuple[str, ...]] = (
    "학생충원",
    "학생 충원",
    "신입생 충원율",
    "재학생 충원율",
    "법인 재정규모",
    "강의실 면적",
    "실험실습실 면적",
    "실험실습 기자재",
    "student_recruitment",
    "corp_finance_ratio",
    "classroom_area",
    "lab_area",
    "lab_equipment",
)


@dataclass(frozen=True)
class ManagementInsightQuestion:
    question_id: str
    label: str
    supported_modes: tuple[AnalysisMode, ...]
    payload_sections: tuple[str, ...]
    cautions: tuple[str, ...]

    def prompt_context(self, *, mode: AnalysisMode) -> dict[str, Any]:
        return {
            "question_id": self.question_id,
            "label": self.label,
            "analysis_mode": mode,
            "payload_sections": list(self.payload_sections),
            "cautions": list(self.cautions),
        }


MANAGEMENT_QUESTIONS: Final[tuple[ManagementInsightQuestion, ...]] = (
    ManagementInsightQuestion(
        question_id="strengths_weaknesses",
        label="핵심 강점과 취약점은 무엇인가?",
        supported_modes=("single_year", "year_range"),
        payload_sections=("strength_weakness_profile", "latest_strength_weakness_profile", "trend_changes"),
        cautions=("강점과 취약점은 분위수와 변화 방향을 근거로만 판단합니다.",),
    ),
    ManagementInsightQuestion(
        question_id="policy_priorities",
        label="경영진이 우선 검토해야 할 정책 과제는 무엇인가?",
        supported_modes=("single_year", "year_range"),
        payload_sections=(
            "strength_weakness_profile",
            "latest_strength_weakness_profile",
            "comparison_gaps",
            "trend_changes",
            "comparison_gap_changes",
            "pending_metrics",
        ),
        cautions=("정책 과제는 최종 결론이 아니라 검토 우선순위로 표현합니다.",),
    ),
    ManagementInsightQuestion(
        question_id="comparison_gaps",
        label="비교 대학 대비 가장 큰 격차는 무엇인가?",
        supported_modes=("single_year", "year_range"),
        payload_sections=("comparison_gaps", "comparison_gap_changes"),
        cautions=("낮을수록 좋은 지표는 조정된 격차 기준으로 해석합니다.",),
    ),
    ManagementInsightQuestion(
        question_id="quadrant_position",
        label="정책 사분면 위치를 어떻게 해석해야 하는가?",
        supported_modes=("single_year",),
        payload_sections=("quadrant",),
        cautions=("사분면 중앙값 기준 위치는 정책 가설이며 우열의 최종 판단으로 단정하지 않습니다.",),
    ),
    ManagementInsightQuestion(
        question_id="correlation_policy_hypotheses",
        label="상관관계에서 정책 가설로 볼 만한 조합은 무엇인가?",
        supported_modes=("single_year",),
        payload_sections=("correlation_hypotheses",),
        cautions=("상관관계를 인과관계로 표현하지 않습니다.",),
    ),
    ManagementInsightQuestion(
        question_id="action_plan",
        label="실행 가능한 개선 과제는 무엇인가?",
        supported_modes=("single_year", "year_range"),
        payload_sections=(
            "strength_weakness_profile",
            "latest_strength_weakness_profile",
            "comparison_gaps",
            "trend_changes",
            "comparison_gap_changes",
            "pending_metrics",
        ),
        cautions=("권고는 실제 부서가 검토할 수 있는 과제 단위로 제시합니다.",),
    ),
    ManagementInsightQuestion(
        question_id="interpretation_risks",
        label="데이터만으로 단정하면 위험한 부분은 무엇인가?",
        supported_modes=("single_year", "year_range"),
        payload_sections=("correlation_hypotheses", "pending_metrics"),
        cautions=("데이터 한계, 커버리지 차이, 정의 미확정 항목을 분리해서 설명합니다.",),
    ),
    ManagementInsightQuestion(
        question_id="pending_metric_impact",
        label="미구현 지표가 추가되면 해석이 어떻게 달라질 수 있는가?",
        supported_modes=("single_year", "year_range"),
        payload_sections=(
            "strength_weakness_profile",
            "latest_strength_weakness_profile",
            "pending_metrics",
        ),
        cautions=("미구현 지표의 값을 추정하지 말고 보완될 해석 영역만 말합니다.",),
    ),
    ManagementInsightQuestion(
        question_id="range_improvements_declines",
        label="최근 범위에서 개선/악화된 지표는 무엇인가?",
        supported_modes=("year_range",),
        payload_sections=("trend_changes", "comparison_gap_changes"),
        cautions=("범위 내 실제 관측 시작/종료연도가 다를 수 있음을 언급합니다.",),
    ),
    ManagementInsightQuestion(
        question_id="structural_vs_temporary",
        label="일시적 성과와 구조적 강점을 구분하면 무엇인가?",
        supported_modes=("year_range",),
        payload_sections=("latest_strength_weakness_profile", "trend_changes", "comparison_gap_changes"),
        cautions=("지속적인 개선과 단년 강점을 구분하되, 원인 단정은 피합니다.",),
    ),
)


def questions_for_mode(mode: AnalysisMode) -> list[ManagementInsightQuestion]:
    return [question for question in MANAGEMENT_QUESTIONS if mode in question.supported_modes]


def get_question_by_label(label: str, *, mode: AnalysisMode) -> ManagementInsightQuestion:
    for question in questions_for_mode(mode):
        if question.label == label:
            return question
    raise KeyError(f"Unknown management insight question for {mode}: {label}")


def filter_payload_for_question(
    payload: dict[str, Any],
    question: ManagementInsightQuestion,
) -> dict[str, Any]:
    selected_keys = CORE_PAYLOAD_SECTIONS | set(question.payload_sections)
    return {
        key: value
        for key, value in payload.items()
        if key in selected_keys
    }


def _period_label(payload: dict[str, Any]) -> str:
    if payload.get("analysis_mode") == "year_range":
        return f"{payload.get('start_year', '')}-{payload.get('end_year', '')}"
    return str(payload.get("year", ""))


def build_payload_context(
    payload: dict[str, Any],
    *,
    question: ManagementInsightQuestion,
) -> dict[str, Any]:
    """Return display-safe metadata describing the data sent to AI."""

    coverage = payload.get("coverage") if isinstance(payload.get("coverage"), dict) else {}
    warnings = coverage.get("warnings", []) if isinstance(coverage, dict) else []
    payload_sections = [
        key
        for key in payload
        if key not in CORE_PAYLOAD_SECTIONS
    ]
    return {
        "질문": question.label,
        "질문 ID": question.question_id,
        "분석 모드": payload.get("analysis_mode", ""),
        "기준 대학": payload.get("focus_school", ""),
        "비교 대학": payload.get("comparison_schools", []),
        "분석 기간": _period_label(payload),
        "포함 지표 수": payload.get("included_series_count"),
        "미포함 지표 수": payload.get("excluded_pending_metric_count"),
        "커버리지 경고": warnings,
        "사용 payload 섹션": payload_sections,
    }


def payload_context_rows(context: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for key, value in context.items():
        if isinstance(value, list):
            display_value = ", ".join(str(item) for item in value) if value else "없음"
        else:
            display_value = "" if value is None else str(value)
        rows.append({"항목": key, "내용": display_value})
    return rows


def _contains_raw_artifact_marker(value: str) -> bool:
    lowered = value.lower()
    return any(pattern.lower() in lowered for pattern in RAW_ARTIFACT_PATTERNS)


def payload_contains_raw_artifact_reference(payload: Any) -> bool:
    if isinstance(payload, dict):
        return any(
            _contains_raw_artifact_marker(str(key)) or payload_contains_raw_artifact_reference(value)
            for key, value in payload.items()
        )
    if isinstance(payload, (list, tuple, set)):
        return any(payload_contains_raw_artifact_reference(item) for item in payload)
    if isinstance(payload, str):
        return _contains_raw_artifact_marker(payload)
    return False


def _preview_value(value: Any, *, depth: int = 0, list_limit: int = 5) -> Any:
    if depth >= 4:
        return "..."
    if isinstance(value, dict):
        return {
            str(key): _preview_value(item, depth=depth + 1, list_limit=list_limit)
            for key, item in value.items()
            if not _contains_raw_artifact_marker(str(key))
        }
    if isinstance(value, list):
        preview_items = [
            _preview_value(item, depth=depth + 1, list_limit=list_limit)
            for item in value[:list_limit]
        ]
        if len(value) > list_limit:
            preview_items.append(f"... 외 {len(value) - list_limit}개")
        return preview_items
    if isinstance(value, str):
        if _contains_raw_artifact_marker(value):
            return "[원자료/로그 경로 제외]"
        return value if len(value) <= 260 else f"{value[:260]}..."
    return value


def build_payload_preview(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a compact, display-safe preview of the AI payload."""

    return {
        key: _preview_value(value)
        for key, value in payload.items()
        if not _contains_raw_artifact_marker(str(key))
    }


def _extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:].strip()

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("JSON 객체를 찾지 못했습니다.")

    return json.loads(stripped[start:end + 1])


def _normalize_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def normalize_management_analysis_result(text: str) -> dict[str, Any]:
    try:
        parsed = _extract_json_object(text)
    except Exception:
        parsed = {"summary": text.strip()}

    result = DEFAULT_MANAGEMENT_ANALYSIS_RESULT | parsed
    for key in ("evidence", "management_implications", "recommended_actions", "risks", "caveats"):
        result[key] = _normalize_list(result.get(key))
    result["summary"] = str(result.get("summary", "")).strip()

    data_used = result.get("data_used")
    if isinstance(data_used, dict):
        result["data_used"] = {str(key): value for key, value in data_used.items()}
    elif isinstance(data_used, list):
        result["data_used"] = {"items": [str(item) for item in data_used if str(item).strip()]}
    elif isinstance(data_used, str) and data_used.strip():
        result["data_used"] = {"description": data_used.strip()}
    else:
        result["data_used"] = {}
    return result


def _analysis_text(result: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("summary", "evidence", "management_implications", "recommended_actions", "risks", "caveats"):
        value = result.get(key)
        if isinstance(value, list):
            parts.extend(str(item) for item in value)
        elif value:
            parts.append(str(value))
    return "\n".join(parts)


def _mentions_pending_metric_with_number(text: str) -> bool:
    for term in PENDING_METRIC_TERMS:
        for match in re.finditer(re.escape(term), text, flags=re.IGNORECASE):
            start = max(0, match.start() - 40)
            end = min(len(text), match.end() + 40)
            window = text[start:end]
            if re.search(r"\d+(?:\.\d+)?\s*(?:%|개|명|원|천원|점|위)?", window):
                return True
    return False


def validate_management_analysis_result(result: dict[str, Any]) -> list[str]:
    """Return review warnings for risky AI management-analysis wording."""

    warnings: list[str] = []
    if not result.get("evidence"):
        warnings.append("근거(evidence)가 비어 있어 보고서 활용 전 수치 근거를 보강해야 합니다.")

    text = _analysis_text(result)
    if any(pattern.lower() in text.lower() for pattern in CAUSAL_ASSERTION_PATTERNS):
        warnings.append("인과관계로 오해될 수 있는 표현이 포함되어 있습니다. 상관/동반 변화 수준으로 재검토하세요.")
    if _mentions_pending_metric_with_number(text):
        warnings.append("미구현 지표가 수치처럼 표현되었을 가능성이 있습니다. 로드맵 상태와 계산값을 분리해 확인하세요.")
    if any(pattern in text for pattern in UNSUPPORTED_CERTAINTY_PATTERNS):
        warnings.append("데이터 범위를 넘어 단정적으로 읽힐 수 있는 표현이 포함되어 있습니다.")
    return warnings


def analyze_management_insight_with_lmstudio(
    payload: dict[str, Any],
    *,
    question: ManagementInsightQuestion,
    mode: AnalysisMode,
    tone: str,
    client: LMStudioClient | None = None,
) -> dict[str, Any]:
    lm_client = client or LMStudioClient()
    system_prompt, user_prompt = build_management_prompts(
        payload,
        question=question.prompt_context(mode=mode),
        tone=tone,
    )
    response_text = lm_client.chat_completion(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )
    return normalize_management_analysis_result(response_text)
