from __future__ import annotations

import json
from typing import Any


def build_budam_prompts(payload: dict[str, Any], *, tone: str, focus: str) -> tuple[str, str]:
    system_prompt = """
당신은 대학 인증평가 IR 분석을 돕는 데이터 해석 보조자다.
반드시 제공된 수치만 근거로 한국어 분석을 작성하라.
없는 원인이나 정책 효과를 단정하지 말고, 추정이 필요한 경우에는 가능성으로만 표현하라.
출력은 반드시 JSON 객체 하나만 반환하라.
""".strip()

    user_prompt = f"""
다음은 법정부담금 부담율 화면에서 사용자가 선택한 데이터 요약이다.
분석 톤은 "{tone}", 분석 초점은 "{focus}"이다.

요구사항:
1. 선택 학교와 그룹 평균, 기준선 관계를 우선 해석한다.
2. 최근 3개년 흐름이 있으면 개선/정체/악화 여부를 짧게 판단한다.
3. 과장 표현을 피하고 경영 보고용 문체를 사용한다.
4. 출력은 아래 스키마를 따르는 JSON 하나만 작성한다.

스키마:
{{
  "summary": "한줄 요약",
  "highlights": ["핵심 시사점 1", "핵심 시사점 2"],
  "threshold_assessment": "인증 기준 관련 해석",
  "risks": ["주의점 1", "주의점 2"],
  "recommended_actions": ["권고 1", "권고 2"],
  "caveats": ["해석 유의사항 1"]
}}

데이터:
{json.dumps(payload, ensure_ascii=False, indent=2)}
""".strip()

    return system_prompt, user_prompt
