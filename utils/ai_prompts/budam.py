from __future__ import annotations

import json
from typing import Any


def build_budam_prompts(payload: dict[str, Any], *, tone: str, focus: str) -> tuple[str, str]:
    system_prompt = """
당신은 대학 인증평가 IR 데이터 해석 보조자다.
반드시 제공된 수치만 근거로 한국어 분석을 작성하라.
원인 추정은 하지 말고, 수치 기반 관찰과 해석만 제시하라.
반드시 message.content에만 최종 답변을 작성하라.
반드시 하나의 JSON 객체만 출력하라.
마크다운, 코드블록, 설명 문장, 사고과정은 출력하지 말라.
""".strip()

    schema = {
        "summary": "한줄 요약",
        "highlights": ["핵심 시사점 1", "핵심 시사점 2"],
        "threshold_assessment": "인증 기준 관련 해석",
        "risks": ["주의점 1", "주의점 2"],
        "recommended_actions": ["권고 1", "권고 2"],
        "caveats": ["해석 유의사항 1"],
    }

    user_prompt = f"""
법정부담금 부담율 데이터 요약을 분석하라.

분석 톤: {tone}
분석 초점: {focus}

규칙:
- 선택 학교와 그룹 평균, 기준선 관계를 먼저 설명한다.
- 최근 3개년 흐름이 보이면 상승/보합/하락 중 하나로 해석한다.
- 경영 보고용 한국어로 짧고 명확하게 쓴다.
- 반드시 최종 JSON만 출력한다.
- code fence를 쓰지 않는다.
- 내용이 없으면 빈 배열 또는 짧은 문장으로 채운다.

출력 스키마 예시:
{json.dumps(schema, ensure_ascii=False)}

데이터:
{json.dumps(payload, ensure_ascii=False, separators=(",", ":"))}
""".strip()

    return system_prompt, user_prompt
