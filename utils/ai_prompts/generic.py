from __future__ import annotations

import json
from typing import Any


def _metric_interpretation_axes(metric_name: str) -> list[str]:
    normalized = metric_name.lower().replace(" ", "")

    if "전임교원" in metric_name or "gyowon" in normalized:
        return [
            "교육 품질과 학생 경험을 뒷받침하는 기본 인력 기반이 충분한지 해석",
            "단기 충족 여부보다 중장기 교원 구조 안정성이 확보되고 있는지 판단",
            "확보율 변화가 학사 운영, 강의 배정, 학생 밀착 지원에 주는 영향 점검",
            "경영 측면에서 인건비 부담과 교육 경쟁력의 균형이 어떤 상태인지 설명",
        ]

    if "연구비" in metric_name or "research" in normalized:
        return [
            "연구 경쟁력과 외부 자원 유치 역량이 강화되고 있는지 해석",
            "교내·교외 연구비 구조가 지속 가능한 성장 기반인지 판단",
            "연구비 추세가 교수진 연구 몰입도와 기관 브랜드에 주는 영향 설명",
            "경영 측면에서 수익 다변화와 전략적 투자 우선순위를 제시",
        ]

    if "논문" in metric_name or "paper" in normalized or "scopus" in normalized or "sci" in normalized:
        return [
            "연구 생산성과 대외 학술 경쟁력이 강화되고 있는지 해석",
            "양적 증가인지, 질적 경쟁력 개선인지 구분해서 설명",
            "최근 추세가 연구 인프라와 교수 성과 관리 측면에서 의미하는 바를 정리",
            "경영 관점에서 브랜드, 평판, 연구중심대학 포지셔닝과 연결해 해석",
        ]

    if "졸업생" in metric_name or "진로" in metric_name or "jirosung" in normalized:
        return [
            "학생 성과가 실제 취업 및 진로 경쟁력으로 이어지고 있는지 해석",
            "수요자 관점에서 교육과정의 실효성과 대학 선택 매력도에 미치는 영향 설명",
            "성과 변화가 입학 경쟁력과 대외 신뢰도에 어떤 파급을 주는지 판단",
            "경영 측면에서 취업지원, 산학협력, 커리어 서비스 강화 필요성을 정리",
        ]

    if "등록금" in metric_name or "tuition" in normalized:
        return [
            "재정 구조가 등록금 의존적 구조인지, 다변화되고 있는지 해석",
            "등록금 비율 변화가 재정 안정성과 정책 대응력에 주는 영향 설명",
            "외부 재원 확보가 부진한 신호인지 여부를 판단",
            "경영 측면에서 수입 포트폴리오 재편 필요성을 제시",
        ]

    if "기부금" in metric_name or "donation" in normalized:
        return [
            "대외 신뢰와 발전재원 확보 역량이 강화되고 있는지 해석",
            "기부금 비율 변화가 브랜드 경쟁력과 네트워크 자산을 반영하는지 설명",
            "등록금·운영수입 구조와 비교했을 때 재원 다변화 수준을 판단",
            "경영 측면에서 모금 전략과 대외협력 체계 보완 포인트를 제시",
        ]

    if "법정부담금" in metric_name or "budam" in normalized:
        return [
            "법정부담금 부담 수준이 재단의 재정 책임 이행 관점에서 어떤 상태인지 해석",
            "기준선 충족 여부를 넘어 구조적 취약성 또는 개선 여지를 설명",
            "부담율 변화가 대학 재정 건전성과 대외 신뢰에 주는 영향 정리",
            "경영 측면에서 재단-대학 재정 관계와 리스크 관리 시사점을 제시",
        ]

    return [
        "지표의 절대 수준과 최근 추세가 무엇을 의미하는지 설명",
        "비교 그룹과의 차이가 어떤 구조적 특징을 시사하는지 해석",
        "현재 상태가 유지될 경우 어떤 기회 또는 위험이 있는지 판단",
        "경영 관점에서 우선 검토해야 할 의사결정 포인트를 제시",
    ]


def build_metric_prompts(payload: dict[str, Any], *, tone: str, focus: str) -> tuple[str, str]:
    metric_name = str(payload.get("metric", ""))
    interpretation_axes = _metric_interpretation_axes(metric_name)
    interpretation_axes_text = "\n".join(f"- {axis}" for axis in interpretation_axes)

    system_prompt = """
당신은 대학기관평가인증과 대학 경영 분석을 함께 수행하는 IR 분석가입니다.
주어진 데이터에서 현재 상태를 요약하는 데 그치지 말고, 비교와 추세를 바탕으로 경영 의사결정에 도움이 되는 인사이트를 도출하세요.

반드시 지켜야 할 규칙:
1. 응답은 JSON 객체 하나만 출력합니다.
2. 데이터에 없는 사실을 단정하지 않습니다.
3. 기준선 충족 여부만 말하지 말고, 그 수치가 대학 경영 측면에서 무엇을 의미하는지 해석합니다.
4. highlights, risks, recommended_actions, management_implications는 실무 보고서에 바로 옮길 수 있게 구체적으로 씁니다.
5. recommended_actions는 실행 가능한 조치 중심으로 씁니다.
6. caveats에는 해석의 한계나 추가 확인이 필요한 점을 넣습니다.
7. 불필요한 수사, 마크다운, 코드펜스는 사용하지 않습니다.
""".strip()

    schema = {
        "summary": "선택 학교와 비교 그룹 흐름을 종합한 2~3문장 요약",
        "highlights": [
            "비교 기반 핵심 인사이트 1",
            "비교 기반 핵심 인사이트 2",
            "추세 또는 격차에 대한 핵심 인사이트 3",
        ],
        "threshold_assessment": "기준선 또는 목표 대비 현재 위치와 경영적 의미를 해석한 문장",
        "management_implications": [
            "대학 경영 관점에서 읽어야 할 의미 1",
            "재정, 수요, 조직, 브랜드, 전략 중 핵심 시사점 2",
        ],
        "risks": [
            "현재 추세가 지속될 경우의 위험 1",
            "중장기적으로 점검해야 할 취약 요소 2",
        ],
        "recommended_actions": [
            "실제로 검토 가능한 액션 1",
            "실제로 검토 가능한 액션 2",
        ],
        "caveats": [
            "데이터 해석의 한계 또는 추가 확인 필요사항 1",
            "데이터 해석의 한계 또는 추가 확인 필요사항 2",
        ],
    }

    user_prompt = f"""
다음 대학 지표 데이터를 분석하세요.

분석 톤: {tone}
분석 초점: {focus}

중점 해석 축:
{interpretation_axes_text}

출력 지침:
- `summary`는 현재 상태를 단순 나열하지 말고, 가장 중요한 흐름과 비교 결과를 묶어서 작성합니다.
- `highlights`에는 선택 학교, 비교 그룹 평균, 최근 추세를 교차 해석한 인사이트를 넣습니다.
- `threshold_assessment`는 기준 충족 여부만 말하지 말고 여유/취약 정도와 그 의미를 설명합니다.
- `management_implications`는 총장단, 기획처, 재정/교무/학생처가 보고 의사결정에 활용할 수 있는 경영 시사점으로 작성합니다.
- `management_implications`에는 “이 수치를 경영진이 어떻게 받아들여야 하는가”, “어떤 구조적 신호로 읽을 수 있는가”를 담습니다.
- `recommended_actions`는 실행 가능한 조치로 씁니다.
- `caveats`에는 데이터만으로 확정할 수 없는 부분을 넣습니다.
- 반드시 JSON 객체만 출력합니다.

출력 스키마:
{json.dumps(schema, ensure_ascii=False)}

분석 데이터:
{json.dumps(payload, ensure_ascii=False, separators=(",", ":"))}
""".strip()

    return system_prompt, user_prompt
