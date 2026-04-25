from __future__ import annotations

import json
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
