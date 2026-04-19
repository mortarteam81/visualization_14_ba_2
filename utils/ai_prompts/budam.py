from __future__ import annotations

import json
from typing import Any


def build_budam_prompts(payload: dict[str, Any], *, tone: str, focus: str) -> tuple[str, str]:
    system_prompt = """
당신은 대학기관평가인증과 대학 재정 구조를 함께 해석하는 IR 분석가입니다.
법정부담금 부담율 데이터를 보고 기준선 충족 여부를 넘어서 재단 책임성, 재정 건전성, 경영 리스크 관점의 인사이트를 도출하세요.

반드시 지켜야 할 규칙:
1. JSON 객체 하나만 출력합니다.
2. 데이터에 없는 사실을 추정하지 않습니다.
3. 선택 학교, 비교 그룹, 최근 추세를 함께 해석합니다.
4. management_implications에는 대학 경영진이 바로 참고할 수 있는 시사점을 넣습니다.
5. 불필요한 마크다운, 코드펜스, 장황한 수사는 사용하지 않습니다.
""".strip()

    schema = {
        "summary": "핵심 요약",
        "highlights": ["핵심 인사이트 1", "핵심 인사이트 2"],
        "threshold_assessment": "인증 기준 및 현재 위치 해석",
        "management_implications": [
            "재단 책임성과 대학 경영 측면의 시사점 1",
            "재정 구조와 리스크 관리 측면의 시사점 2",
        ],
        "risks": ["주의 요소 1", "주의 요소 2"],
        "recommended_actions": ["권고 액션 1", "권고 액션 2"],
        "caveats": ["해석 유의사항 1"],
    }

    user_prompt = f"""
법정부담금 부담율 데이터를 분석하세요.

분석 톤: {tone}
분석 초점: {focus}

중점 해석 방향:
- 선택 학교와 비교 그룹 평균 간 격차를 함께 봅니다.
- 최근 3개년 추세가 개선인지 정체인지 악화인지 해석합니다.
- 인증 기준 충족 여부뿐 아니라, 재단의 재정 책임성과 구조적 취약성을 설명합니다.
- 경영 측면에서 이 수치를 어떻게 읽고 어떤 대응 논의를 시작해야 하는지 제시합니다.

출력 지침:
- `summary`는 가장 중요한 흐름을 2~3문장으로 요약합니다.
- `highlights`는 비교와 추세를 반영한 인사이트를 제시합니다.
- `threshold_assessment`는 기준선과의 거리, 여유도 또는 취약도를 설명합니다.
- `management_implications`는 대학 경영진이 바로 참고할 수 있는 시사점으로 씁니다.
- `recommended_actions`는 실행 가능한 조치 중심으로 씁니다.
- `caveats`는 데이터 해석의 한계를 넣습니다.
- 반드시 JSON 객체만 출력합니다.

출력 스키마:
{json.dumps(schema, ensure_ascii=False)}

분석 데이터:
{json.dumps(payload, ensure_ascii=False, separators=(",", ":"))}
""".strip()

    return system_prompt, user_prompt
