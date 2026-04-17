"""Typed registry metadata for metric pages and gradual config migration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class SeriesSpec:
    """Describes a single series/column within a metric."""

    id: str
    label: str
    column: str
    unit: str
    threshold: float | None = None
    threshold_label: str | None = None
    threshold_direction: str = "gte"
    decimals: int = 1


@dataclass(frozen=True)
class MetricSpec:
    """Describes a metric page and the dataset it reads from."""

    id: str
    title: str
    icon: str
    summary: str
    description: str
    page_path: str
    dataset_key: str
    csv_file: str
    csv_encoding: str
    default_school: str
    nav_order: int
    threshold_note: str
    supports_branch_toggle: bool = False
    home_visible: bool = True
    series: tuple[SeriesSpec, ...] = ()


APP_METADATA: Final = {
    "title": "서울 소재 사립대학교 교육여건 지표 시각화",
    "subtitle": "대학알리미 공시자료 기반 대학기관평가인증 정량지표 추이 분석",
    "icon": "🎓",
    "data_updated": "2026-03-09",
    "source_name": "대학알리미",
    "source_url": "https://www.academyinfo.go.kr",
    "catalog_heading": "지표 카탈로그",
    "catalog_intro": "관심 있는 지표를 선택해 연도별 추이와 학교별 비교를 확인하세요.",
}


METRIC_REGISTRY: Final[dict[str, MetricSpec]] = {
    "budam": MetricSpec(
        id="budam",
        title="법정부담금 부담율",
        icon="🏛️",
        summary="학교법인이 법정부담금 기준 대비 실제로 부담한 비율",
        description="학교법인의 법정부담금 부담 수준을 연도별로 비교합니다.",
        page_path="pages/1_법정부담금_부담율.py",
        dataset_key="budam",
        csv_file="법정부담금_부담율.csv",
        csv_encoding="utf-8-sig",
        default_school="성신여자대학교",
        nav_order=1,
        threshold_note="4주기 인증 기준: 10% 이상",
        series=(
            SeriesSpec(
                id="budam_rate",
                label="부담율",
                column="부담율",
                unit="%",
                threshold=10.0,
                threshold_label="4주기 인증 기준",
                decimals=1,
            ),
        ),
    ),
    "gyowon": MetricSpec(
        id="gyowon",
        title="전임교원 확보율",
        icon="👩‍🏫",
        summary="법정 기준 교원 대비 실제 전임교원 확보 비율",
        description="학생정원 기준과 재학생 기준 전임교원 확보율을 비교합니다.",
        page_path="pages/2_전임교원_확보율.py",
        dataset_key="gyowon",
        csv_file="전임교원_확보율.csv",
        csv_encoding="utf-8-sig",
        default_school="성신여자대학교",
        nav_order=2,
        threshold_note="4주기 인증 기준: 61% 이상 (학생정원 기준)",
        supports_branch_toggle=True,
        series=(
            SeriesSpec(
                id="gyowon_jeongwon",
                label="학생정원 기준 확보율",
                column="전임교원 확보율(학생정원 기준)",
                unit="%",
                threshold=61.0,
                threshold_label="4주기 인증 기준",
                decimals=1,
            ),
            SeriesSpec(
                id="gyowon_jaehak",
                label="재학생 기준 확보율",
                column="전임교원 확보율(재학생 기준)",
                unit="%",
                decimals=1,
            ),
        ),
    ),
    "research": MetricSpec(
        id="research",
        title="전임교원 1인당 연구비",
        icon="💰",
        summary="전임교원 1인당 교내·교외 연구비 수혜 실적",
        description="교내 및 교외 연구비 수혜 규모를 함께 비교합니다.",
        page_path="pages/3_연구비_수혜실적.py",
        dataset_key="research",
        csv_file="연구비_수혜실적.csv",
        csv_encoding="utf-8-sig",
        default_school="성신여자대학교",
        nav_order=3,
        threshold_note="4주기 인증 기준: 교내 1,000천원 / 교외 10,000천원 이상",
        supports_branch_toggle=True,
        series=(
            SeriesSpec(
                id="research_in",
                label="교내 연구비",
                column="전임교원 1인당 연구비(교내)",
                unit="천원",
                threshold=1_000.0,
                threshold_label="4주기 인증 기준",
                decimals=0,
            ),
            SeriesSpec(
                id="research_out",
                label="교외 연구비",
                column="전임교원 1인당 연구비(교외)",
                unit="천원",
                threshold=10_000.0,
                threshold_label="4주기 인증 기준",
                decimals=0,
            ),
        ),
    ),
    "paper": MetricSpec(
        id="paper",
        title="전임교원 1인당 논문실적",
        icon="📚",
        summary="국내 등재지 논문과 SCI급·SCOPUS 국제 논문 실적",
        description="전임교원 1인당 국내·국제 논문 실적을 비교합니다.",
        page_path="pages/4_논문실적.py",
        dataset_key="paper",
        csv_file="전임교원_논문실적.csv",
        csv_encoding="utf-8-sig",
        default_school="성신여자대학교",
        nav_order=4,
        threshold_note="4주기 인증 기준: 국내 0.35편 / SCI급 0.05편 이상",
        supports_branch_toggle=True,
        series=(
            SeriesSpec(
                id="paper_jaeji",
                label="국내 등재지 논문",
                column="전임교원1인당논문실적(국내, 연구재단등재지(후보포함))",
                unit="편",
                threshold=0.35,
                threshold_label="4주기 인증 기준",
                decimals=4,
            ),
            SeriesSpec(
                id="paper_sci",
                label="SCI급·SCOPUS 논문",
                column="전임교원1인당논문실적(국제, SCI급/SCOPUS학술지)",
                unit="편",
                threshold=0.05,
                threshold_label="4주기 인증 기준",
                decimals=4,
            ),
        ),
    ),
    "jirosung": MetricSpec(
        id="jirosung",
        title="졸업생 진로 성과",
        icon="🧭",
        summary="취업 및 진학을 반영한 졸업생 진로 성과 비율",
        description="취업·진학 성과를 연도별로 비교합니다.",
        page_path="pages/5_졸업생_진로_성과.py",
        dataset_key="jirosung",
        csv_file="졸업생_취업률.csv",
        csv_encoding="utf-8-sig",
        default_school="성신여자대학교",
        nav_order=5,
        threshold_note="4주기 인증 기준: 55% 이상",
        supports_branch_toggle=True,
        series=(
            SeriesSpec(
                id="jirosung_outcome",
                label="진로 성과",
                column="졸업생_진로_성과",
                unit="%",
                threshold=55.0,
                threshold_label="4주기 인증 기준",
                decimals=1,
            ),
        ),
    ),
    "tuition": MetricSpec(
        id="tuition",
        title="세입 중 등록금 비율",
        icon="💳",
        summary="운영수입 대비 등록금수입 비율",
        description="운영수입 대비 등록금수입 비중을 연도별로 확인합니다.",
        page_path="pages/6_세입_중_등록금_비율.py",
        dataset_key="gyeolsan",
        csv_file="결산(22,23,24).csv",
        csv_encoding="utf-8-sig",
        default_school="성신여자대학교",
        nav_order=6,
        threshold_note="4주기 인증 기준: 72% 이하",
        series=(
            SeriesSpec(
                id="tuition_ratio",
                label="등록금 비율",
                column="등록금비율",
                unit="%",
                threshold=72.0,
                threshold_label="4주기 인증 기준",
                threshold_direction="lte",
                decimals=2,
            ),
        ),
    ),
    "donation": MetricSpec(
        id="donation",
        title="세입 중 기부금 비율",
        icon="🎁",
        summary="운영수입 대비 기부금수입 비율",
        description="운영수입 대비 기부금수입 비중을 연도별로 확인합니다.",
        page_path="pages/7_세입_중_기부금_비율.py",
        dataset_key="gyeolsan",
        csv_file="결산(22,23,24).csv",
        csv_encoding="utf-8-sig",
        default_school="성신여자대학교",
        nav_order=7,
        threshold_note="4주기 인증 기준: 0.4% 이상",
        series=(
            SeriesSpec(
                id="donation_ratio",
                label="기부금 비율",
                column="기부금비율",
                unit="%",
                threshold=0.4,
                threshold_label="4주기 인증 기준",
                decimals=2,
            ),
        ),
    ),
}


SERIES_REGISTRY: Final[dict[str, SeriesSpec]] = {
    series.id: series
    for metric in METRIC_REGISTRY.values()
    for series in metric.series
}


def get_metric(metric_id: str) -> MetricSpec:
    return METRIC_REGISTRY[metric_id]


def get_series(series_id: str) -> SeriesSpec:
    return SERIES_REGISTRY[series_id]


def list_metrics() -> list[MetricSpec]:
    return sorted(METRIC_REGISTRY.values(), key=lambda item: item.nav_order)
