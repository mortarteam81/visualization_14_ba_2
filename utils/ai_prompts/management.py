from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any


def build_management_prompts(
    payload: dict[str, Any],
    *,
    question: Mapping[str, Any],
    tone: str,
) -> tuple[str, str]:
    """Build prompts for the management insight dashboard AI analysis."""

    system_prompt = """
당신은 대학 경영진에게 공시데이터 기반 정책 가설을 제시하는 IR 분석가입니다.
주어진 요약 데이터만 사용해 경영 의사결정에 도움이 되는 근거 명시형 분석을 작성하세요.

반드시 지켜야 할 규칙:
1. 응답은 JSON 객체 하나만 출력합니다.
2. 데이터에 없는 사실을 단정하지 않습니다.
3. 상관관계는 인과관계로 표현하지 않습니다.
4. 미구현 지표는 계산값처럼 말하지 않고, 로드맵 또는 추가 확인 필요 항목으로만 언급합니다.
5. 요약 데이터에 없는 원자료, 로그, 쿠키, 외부 비공개 정보가 있다고 가정하지 않습니다.
6. evidence에는 반드시 payload 안의 수치, 순위, 분위수, 변화량, 격차, 커버리지 중 하나 이상을 근거로 씁니다.
7. recommended_actions는 대학이 실제로 검토할 수 있는 정책 과제 형태로 씁니다.
8. caveats에는 데이터 커버리지, 정의 미확정, 인과관계 한계 등 해석상 주의점을 넣습니다.
9. 불필요한 수사, 마크다운, 코드펜스는 사용하지 않습니다.
""".strip()

    schema = {
        "summary": "질문에 대한 2~3문장 경영 요약",
        "evidence": [
            "분석 근거 1: 사용한 지표, 수치, 분위수, 변화량 또는 격차를 포함",
            "분석 근거 2: 비교대학 또는 연도 범위 근거를 포함",
        ],
        "management_implications": [
            "총장단/기획처 관점의 정책적 의미 1",
            "재정, 교무, 학생, 연구, 교육여건 중 연결되는 시사점 2",
        ],
        "recommended_actions": [
            "실행 가능한 검토 과제 1",
            "실행 가능한 검토 과제 2",
        ],
        "risks": [
            "현재 흐름이 지속될 경우의 위험 1",
            "보고 시 과도하게 단정하면 안 되는 위험 2",
        ],
        "caveats": [
            "데이터 해석의 한계 또는 추가 확인 필요사항 1",
            "데이터 해석의 한계 또는 추가 확인 필요사항 2",
        ],
        "data_used": {
            "analysis_mode": "single_year 또는 year_range",
            "focus_school": "분석 기준 대학",
            "period": "사용한 연도 또는 연도 범위",
            "included_series_count": "계산에 포함된 구현 완료 지표 수",
            "excluded_pending_metric_count": "계산에서 제외된 미구현 지표 수",
        },
    }

    question_text = str(question.get("label", ""))
    caution_text = "\n".join(f"- {item}" for item in question.get("cautions", []))

    user_prompt = f"""
다음 질문에 답하세요.

질문: {question_text}
분석 톤: {tone}
분석 모드: {question.get("analysis_mode", "")}

질문별 해석 주의사항:
{caution_text}

출력 지침:
- `summary`는 질문에 대한 결론을 먼저 제시합니다.
- `evidence`에는 payload에서 확인 가능한 수치 근거만 씁니다.
- `management_implications`는 경영진이 읽을 정책적 의미로 작성합니다.
- `recommended_actions`는 즉시 검토 가능한 액션 중심으로 작성합니다.
- `risks`와 `caveats`는 데이터 한계와 해석 리스크를 분리해서 씁니다.
- `data_used`에는 실제 payload 기준의 분석 모드, 대학, 기간, 포함/제외 지표 수를 요약합니다.
- 반드시 JSON 객체만 출력합니다.

출력 스키마:
{json.dumps(schema, ensure_ascii=False)}

분석 데이터:
{json.dumps(payload, ensure_ascii=False, separators=(",", ":"))}
""".strip()

    return system_prompt, user_prompt
