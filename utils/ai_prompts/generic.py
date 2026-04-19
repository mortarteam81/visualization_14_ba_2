from __future__ import annotations

import json
from typing import Any


def build_metric_prompts(payload: dict[str, Any], *, tone: str, focus: str) -> tuple[str, str]:
    system_prompt = """
당신은 대학 공시지표 기반 IR 데이터 해석 보조자입니다.
반드시 수치와 최근 추이, 기준선 충족 여부를 중심으로 분석하세요.
원인 추정은 최소화하고, 데이터에서 직접 확인 가능한 관찰과 해석만 제시하세요.
반드시 message.content에만 최종 응답을 작성하세요.
반드시 하나의 JSON 객체만 출력하세요.
마크다운, 코드블록, 설명 문장, 사고과정은 출력하지 마세요.
""".strip()

    schema = {
        "summary": "현재 상태와 비교 결과를 요약한 2~3문장",
        "highlights": ["핵심 관찰 1", "핵심 관찰 2"],
        "threshold_assessment": "기준선 또는 목표 대비 해석",
        "risks": ["주의할 점 1", "주의할 점 2"],
        "recommended_actions": ["실무 권고 1", "실무 권고 2"],
        "caveats": ["해석 시 유의사항 1"],
    }

    user_prompt = f"""
다음 대학 지표 데이터를 분석하세요.

분석 톤: {tone}
분석 초점: {focus}

규칙:
- 선택 학교와 그룹 평균, 기준선 관계를 먼저 설명하세요.
- 최근 3개년 흐름은 상승/보합/하락 중 하나로 간단히 해석하세요.
- 숫자를 직접 인용하며 짧고 명확하게 작성하세요.
- 기준선이 없는 지표라면 절대 기준 대신 선택 학교와 그룹 평균의 격차 중심으로 해석하세요.
- 내용이 없으면 빈 배열 또는 짧은 문장으로 채우세요.
- 반드시 최종 JSON만 출력하세요.

출력 스키마 예시:
{json.dumps(schema, ensure_ascii=False)}

데이터:
{json.dumps(payload, ensure_ascii=False, separators=(",", ":"))}
""".strip()

    return system_prompt, user_prompt
