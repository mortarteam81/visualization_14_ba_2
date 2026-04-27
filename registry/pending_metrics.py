"""Planning metadata for pending raw-first metric implementation.

This module intentionally does not mark pending metrics as implemented.  It keeps
source, calculation, and registry-compatibility proposals in one importable place
so scripts and tests can validate the implementation plan before real downloads
or API calls are introduced.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Mapping


@dataclass(frozen=True)
class ProposedSeriesSpec:
    """Registry-compatible proposed output series for a pending metric."""

    id: str
    label: str
    column: str
    unit: str
    decimals: int = 1


@dataclass(frozen=True)
class PendingMetricPlan:
    """Raw-first/API-refresh implementation plan for a pending metric."""

    metric_id: str
    dataset_key: str
    title: str
    source_priority: tuple[str, ...]
    raw_source_urls: tuple[str, ...]
    api_refresh_urls: tuple[str, ...]
    numerator: str
    denominator: str
    formula: str
    unit: str
    implementation_priority: int
    needs_definition_review: bool
    proposed_series: tuple[ProposedSeriesSpec, ...]
    notes: str = ""


KUEE_4TH_CYCLE_CRITERIA_URL: Final[str] = (
    "https://aims.kcue.or.kr/cop/bbs/selectBoardArticle.do?"
    "bbsId=BBSMSTR_000000000004&nttId=7035"
)
CLASSROOM_AREA_STANDARD_SQM: Final[float] = 1.2
LAB_AREA_STANDARD_SQM: Final[float] = 2.5
LAB_AREA_FIELDS: Final[tuple[str, ...]] = (
    "인문사회계열",
    "자연과학계열",
    "공학계열",
    "의학계열",
    "예체능계열",
)
LAB_AREA_STUDENT_WEIGHTS: Final[Mapping[str, float]] = MappingProxyType(
    {
        "인문사회계열": 1 / 3,
        "자연과학계열": 1.0,
        "공학계열": 1.0,
        "의학계열": 1.0,
        "예체능계열": 1.0,
    }
)
LAB_EQUIPMENT_FIELDS: Final[tuple[str, ...]] = (
    "자연과학계열",
    "공학계열",
    "의학계열",
    "예체능계열",
)
LAB_EQUIPMENT_DEFINITION_YEARS: Final[tuple[int, int]] = (2024, 2025)


PENDING_METRIC_PLANS: Final[dict[str, PendingMetricPlan]] = {
    "corp_finance_ratio": PendingMetricPlan(
        metric_id="corp_finance_ratio",
        dataset_key="corp_finance_ratio",
        title="법인(일반회계) 재정규모 대비 법인전입금 비율",
        source_priority=(
            "한국사학진흥재단 대학재정알리미 법인회계 원자료",
            "학교법인 일반회계 자금계산서",
        ),
        raw_source_urls=(
            "https://uniarlimi.kasfo.or.kr/statistics/indicator",
        ),
        api_refresh_urls=(),
        numerator="학교로 전출된 법인전입금",
        denominator="법인 일반회계 재정규모 또는 법인 일반회계 자금수입 총액",
        formula="법인전입금 / 법인 일반회계 자금수입 총액 × 100",
        unit="%",
        implementation_priority=2,
        needs_definition_review=True,
        proposed_series=(
            ProposedSeriesSpec(
                id="corp_finance_transfer_ratio",
                label="법인 재정규모 대비 법인전입금 비율",
                column="법인재정규모대비법인전입금비율",
                unit="%",
                decimals=2,
            ),
        ),
        notes="분모 정의 확정 필요. 직접 지표가 아니라 계산형으로 접근.",
    ),
    "student_recruitment": PendingMetricPlan(
        metric_id="student_recruitment",
        dataset_key="student_recruitment",
        title="학생 충원 성과",
        source_priority=(
            "공공데이터포털 한국대학교육협의회 대학정보공시 학생 현황",
            "대학알리미 학생 현황 원자료",
        ),
        raw_source_urls=(
            "https://www.data.go.kr/data/15037346/openapi.do",
        ),
        api_refresh_urls=(
            "http://openapi.academyinfo.go.kr/openapi/service/rest/StudentService",
        ),
        numerator="입학자 수 또는 재학생 수",
        denominator="모집인원 또는 편제정원",
        formula="신입생 충원율 및 재학생 충원율을 원자료 직접값으로 우선 사용하고, 필요 시 분자/분모로 재계산",
        unit="%",
        implementation_priority=1,
        needs_definition_review=False,
        proposed_series=(
            ProposedSeriesSpec(
                id="freshman_fill_rate",
                label="신입생 충원율",
                column="신입생충원율",
                unit="%",
                decimals=1,
            ),
            ProposedSeriesSpec(
                id="student_fill_rate",
                label="재학생 충원율",
                column="재학생충원율",
                unit="%",
                decimals=1,
            ),
        ),
        notes="API 업데이트 단계에 가장 적합한 1차 구현 후보.",
    ),
    "adjunct_faculty": PendingMetricPlan(
        metric_id="adjunct_faculty",
        dataset_key="adjunct_faculty",
        title="겸임교원 확보율",
        source_priority=(
            "공공데이터포털 한국대학교육협의회 대학알리미 교원·연구 현황",
            "대학알리미 교원 세부 원자료",
        ),
        raw_source_urls=(
            "https://www.data.go.kr/data/15037505/openapi.do",
        ),
        api_refresh_urls=(
            "http://openapi.academyinfo.go.kr/openapi/service/rest/EducationResearchService",
        ),
        numerator="겸임교원 수",
        denominator="기준 필요 겸임교원 수 또는 전체 교원 수",
        formula="겸임교원 수 / 기준 필요 겸임교원 수 × 100 (정의 확정 전 임시)",
        unit="%",
        implementation_priority=2,
        needs_definition_review=True,
        proposed_series=(
            ProposedSeriesSpec(
                id="adjunct_faculty_rate",
                label="겸임교원 확보율",
                column="겸임교원확보율",
                unit="%",
                decimals=1,
            ),
        ),
        notes="대학알리미 활용가이드에서 직접 항목 존재 여부와 공식 산식 확인 필요.",
    ),
    "classroom_area": PendingMetricPlan(
        metric_id="classroom_area",
        dataset_key="classroom_area",
        title="재학생 1인당 강의실 면적",
        source_priority=(
            "공공데이터포털 한국대학교육협의회 대학알리미 교육여건 현황",
            "대학알리미 교육시설 원자료",
        ),
        raw_source_urls=(
            "https://www.data.go.kr/data/15037506/openapi.do",
        ),
        api_refresh_urls=(
            "http://openapi.academyinfo.go.kr/openapi/service/rest/EducationConditionService",
        ),
        numerator="일반 강의실 면적 + 멀티미디어 강의실 면적(공용 면적 제외, ㎡)",
        denominator="재학생 수(학부+대학원, 정원내+정원외, 평가 기준 제외 대상 반영)",
        formula="전체 강의실 면적 / 재학생 수",
        unit="㎡",
        implementation_priority=2,
        needs_definition_review=True,
        proposed_series=(
            ProposedSeriesSpec(
                id="classroom_area_per_student",
                label="재학생 1인당 강의실 면적",
                column="재학생1인당강의실면적",
                unit="㎡",
                decimals=2,
            ),
        ),
        notes=(
            "한국대학평가원 4주기 대학기관평가인증 평가 기준 양식 4.4-1 기준. "
            "계열별 산출 지표가 아니라 일반/멀티미디어 강의실 합계 면적을 재학생 수로 나누며, "
            "기준값은 1.2㎡이다. 캠퍼스 분리 운영 대학은 캠퍼스별 작성이 필요하고, 복도 등 공용 면적은 제외한다. "
            f"정의 출처: {KUEE_4TH_CYCLE_CRITERIA_URL}"
        ),
    ),
    "lab_area": PendingMetricPlan(
        metric_id="lab_area",
        dataset_key="lab_area",
        title="재학생 1인당 실험실습실 면적",
        source_priority=(
            "공공데이터포털 한국대학교육협의회 대학알리미 교육여건 현황",
            "대학알리미 교육시설 원자료",
        ),
        raw_source_urls=(
            "https://www.data.go.kr/data/15037506/openapi.do",
        ),
        api_refresh_urls=(
            "http://openapi.academyinfo.go.kr/openapi/service/rest/EducationConditionService",
        ),
        numerator="계열별 실험·실습실 면적(공용 면적 제외, ㎡)",
        denominator="계열별 재학생 수",
        formula=(
            "계열별 실험·실습실 면적 / 계열별 재학생 수; 평균은 인문사회계열 "
            "재학생 수를 1/3로 가중한 환산 재학생 수 기준"
        ),
        unit="㎡",
        implementation_priority=2,
        needs_definition_review=True,
        proposed_series=(
            ProposedSeriesSpec(
                id="lab_area_per_student",
                label="재학생 1인당 실험실습실 면적",
                column="재학생1인당실험실습실면적",
                unit="㎡",
                decimals=2,
            ),
        ),
        notes=(
            "한국대학평가원 4주기 대학기관평가인증 평가 기준 양식 4.4-2 기준. "
            "계열은 인문사회·자연과학·공학·의학·예체능으로 구분하고, 기준값은 2.5㎡이다. "
            "공동 사용 실험·실습실은 계열별 재학생 수 기준으로 배분하며, 캠퍼스 분리 운영 대학은 캠퍼스별 작성이 필요하다. "
            f"정의 출처: {KUEE_4TH_CYCLE_CRITERIA_URL}"
        ),
    ),
    "lab_equipment": PendingMetricPlan(
        metric_id="lab_equipment",
        dataset_key="lab_equipment",
        title="재학생 1인당 실험실습 기자재 구입비",
        source_priority=(
            "공공데이터포털 한국대학교육협의회 대학알리미 재정 현황",
            "대학알리미 교육여건/재정 원자료",
        ),
        raw_source_urls=(
            "https://www.data.go.kr/data/15038392/openapi.do",
        ),
        api_refresh_urls=(
            "http://openapi.academyinfo.go.kr/openapi/service/rest/FinanceService",
        ),
        numerator="최근 2년 계열별 실험·실습 기자재 구입비 합계",
        denominator="최근 2개 학년도 계열별 재학생 수 합계",
        formula=(
            "최근 2년 실험·실습 기자재 구입비 합계 / 최근 2개 학년도 재학생 수 합계; "
            "기준값은 대학 자체 자연과학-인문사회 평균 등록금 차액의 15%와 전국 기준값 중 작은 값"
        ),
        unit="천원",
        implementation_priority=2,
        needs_definition_review=True,
        proposed_series=(
            ProposedSeriesSpec(
                id="lab_equipment_expense_per_student",
                label="재학생 1인당 실험실습 기자재 구입비",
                column="재학생1인당실험실습기자재구입비",
                unit="천원",
                decimals=0,
            ),
        ),
        notes=(
            "한국대학평가원 4주기 대학기관평가인증 평가 기준 양식 4.4-3 기준. "
            "계열별 작성 대상은 자연과학·공학·의학·예체능이며, 인문사회계열은 기준값 산출 참고용이다. "
            "기계·기구 매입비, 실험·실습 기자재/집기 구입비와 리스 임차료를 포함하고 시약·샘플 구입비는 제외한다. "
            "2024~2025회계연도 결산 자료와 2024~2025학년도 재학생 수를 사용한다. "
            f"정의 출처: {KUEE_4TH_CYCLE_CRITERIA_URL}"
        ),
    ),
}


PENDING_METRIC_IDS: Final[tuple[str, ...]] = tuple(PENDING_METRIC_PLANS)


__all__ = [
    "CLASSROOM_AREA_STANDARD_SQM",
    "KUEE_4TH_CYCLE_CRITERIA_URL",
    "LAB_AREA_FIELDS",
    "LAB_AREA_STANDARD_SQM",
    "LAB_AREA_STUDENT_WEIGHTS",
    "LAB_EQUIPMENT_DEFINITION_YEARS",
    "LAB_EQUIPMENT_FIELDS",
    "PENDING_METRIC_IDS",
    "PENDING_METRIC_PLANS",
    "PendingMetricPlan",
    "ProposedSeriesSpec",
]
