"""Management insight dataset builders for the prototype dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Final

import pandas as pd

from registry import METRIC_REGISTRY
from utils.config import (
    DORMITORY_COL,
    EDUCATION_RETURN_COL,
    GYOWON_COL_JAEHAK,
    GYOWON_COL_JEONGWON,
    LECTURER_PAY_COL,
    LIBRARY_MATERIAL_PURCHASE_COL,
    LIBRARY_STAFF_COL,
    PAPER_COL_JAEJI,
    PAPER_COL_SCI,
    RESEARCH_COL_IN,
    RESEARCH_COL_OUT,
)
from utils.data_pipeline import (
    load_budam_frame,
    load_dormitory_frame,
    load_education_return_frame,
    load_gyeolsan_frame,
    load_gyowon_csv_frame,
    load_jirosung_frame,
    load_lecturer_pay_frame,
    load_library_material_purchase_frame,
    load_library_staff_frame,
    load_paper_frame,
    load_research_frame,
)


DEFAULT_ANALYSIS_YEAR: Final[int] = 2024
PENDING_METRIC_IDS: Final[tuple[str, ...]] = (
    "corp_transfer_ratio",
    "corp_finance_ratio",
    "student_recruitment",
    "adjunct_faculty",
    "staff_per_student",
    "scholarship_ratio",
    "classroom_area",
    "lab_area",
    "lab_equipment",
)


@dataclass(frozen=True)
class InsightMetricSpec:
    """A single analysis-ready metric series."""

    key: str
    label: str
    source_metric_id: str
    source_column: str
    unit: str
    group: str
    decimals: int = 1
    higher_is_better: bool = True


@dataclass(frozen=True)
class LoaderSpec:
    """Source loader and the metric series extracted from its frame."""

    loader: Callable[[], pd.DataFrame]
    metrics: tuple[InsightMetricSpec, ...]


@dataclass(frozen=True)
class InsightDataset:
    """Normalized data used by the management dashboard."""

    long: pd.DataFrame
    wide: pd.DataFrame
    metrics: tuple[InsightMetricSpec, ...]
    skipped_sources: tuple[str, ...]

    @property
    def implemented_metric_count(self) -> int:
        return len({metric.source_metric_id for metric in self.metrics})

    @property
    def included_series_count(self) -> int:
        return len(self.metrics)

    @property
    def pending_metric_count(self) -> int:
        return len(PENDING_METRIC_IDS)


ANALYSIS_LOADERS: Final[tuple[LoaderSpec, ...]] = (
    LoaderSpec(
        load_gyeolsan_frame,
        (
            InsightMetricSpec(
                key="tuition_ratio",
                label="등록금 비율",
                source_metric_id="tuition",
                source_column="등록금비율",
                unit="%",
                group="재정",
                decimals=2,
                higher_is_better=False,
            ),
            InsightMetricSpec(
                key="donation_ratio",
                label="기부금 비율",
                source_metric_id="donation",
                source_column="기부금비율",
                unit="%",
                group="재정",
                decimals=2,
            ),
        ),
    ),
    LoaderSpec(
        load_budam_frame,
        (
            InsightMetricSpec(
                key="budam_rate",
                label="법정부담금 부담율",
                source_metric_id="budam",
                source_column="부담율",
                unit="%",
                group="재정",
            ),
        ),
    ),
    LoaderSpec(
        load_education_return_frame,
        (
            InsightMetricSpec(
                key="education_return_rate",
                label="교육비 환원율",
                source_metric_id="education_return",
                source_column=EDUCATION_RETURN_COL,
                unit="%",
                group="재정",
            ),
        ),
    ),
    LoaderSpec(
        load_jirosung_frame,
        (
            InsightMetricSpec(
                key="career_outcome_rate",
                label="졸업생 진로 성과",
                source_metric_id="jirosung",
                source_column="졸업생_진로_성과",
                unit="%",
                group="학생성과",
            ),
        ),
    ),
    LoaderSpec(
        load_gyowon_csv_frame,
        (
            InsightMetricSpec(
                key="fulltime_faculty_quota_rate",
                label="전임교원 확보율(정원)",
                source_metric_id="gyowon",
                source_column=GYOWON_COL_JEONGWON,
                unit="%",
                group="교원",
            ),
            InsightMetricSpec(
                key="fulltime_faculty_enrolled_rate",
                label="전임교원 확보율(재학생)",
                source_metric_id="gyowon",
                source_column=GYOWON_COL_JAEHAK,
                unit="%",
                group="교원",
            ),
        ),
    ),
    LoaderSpec(
        load_lecturer_pay_frame,
        (
            InsightMetricSpec(
                key="lecturer_hourly_pay",
                label="강사 강의료",
                source_metric_id="lecturer_pay",
                source_column=LECTURER_PAY_COL,
                unit="원",
                group="교원",
                decimals=0,
            ),
        ),
    ),
    LoaderSpec(
        load_research_frame,
        (
            InsightMetricSpec(
                key="internal_research_fund",
                label="교내 연구비",
                source_metric_id="research",
                source_column=RESEARCH_COL_IN,
                unit="천원",
                group="연구성과",
                decimals=0,
            ),
            InsightMetricSpec(
                key="external_research_fund",
                label="교외 연구비",
                source_metric_id="research",
                source_column=RESEARCH_COL_OUT,
                unit="천원",
                group="연구성과",
                decimals=0,
            ),
        ),
    ),
    LoaderSpec(
        load_paper_frame,
        (
            InsightMetricSpec(
                key="domestic_paper_per_faculty",
                label="국내 논문실적",
                source_metric_id="paper",
                source_column=PAPER_COL_JAEJI,
                unit="편",
                group="연구성과",
                decimals=4,
            ),
            InsightMetricSpec(
                key="international_paper_per_faculty",
                label="국제 논문실적",
                source_metric_id="paper",
                source_column=PAPER_COL_SCI,
                unit="편",
                group="연구성과",
                decimals=4,
            ),
        ),
    ),
    LoaderSpec(
        load_dormitory_frame,
        (
            InsightMetricSpec(
                key="dormitory_accommodation_rate",
                label="기숙사 수용률",
                source_metric_id="dormitory_rate",
                source_column=DORMITORY_COL,
                unit="%",
                group="교육여건",
            ),
        ),
    ),
    LoaderSpec(
        load_library_material_purchase_frame,
        (
            InsightMetricSpec(
                key="library_material_purchase_per_student",
                label="도서자료구입비",
                source_metric_id="library_material_purchase",
                source_column=LIBRARY_MATERIAL_PURCHASE_COL,
                unit="원",
                group="교육여건",
                decimals=0,
            ),
        ),
    ),
    LoaderSpec(
        load_library_staff_frame,
        (
            InsightMetricSpec(
                key="library_staff_per_1000_students",
                label="도서관 직원수",
                source_metric_id="library_staff",
                source_column=LIBRARY_STAFF_COL,
                unit="명",
                group="교육여건",
                decimals=2,
            ),
        ),
    ),
)


QUADRANT_PRESETS: Final[tuple[tuple[str, str, str], ...]] = (
    ("등록금 의존도와 교육 환원", "tuition_ratio", "education_return_rate"),
    ("연구비와 국제 논문 성과", "external_research_fund", "international_paper_per_faculty"),
    ("교원 확보와 진로 성과", "fulltime_faculty_quota_rate", "career_outcome_rate"),
    ("도서관 자료 투자와 인력", "library_material_purchase_per_student", "library_staff_per_1000_students"),
    ("기부금과 법정부담금", "donation_ratio", "budam_rate"),
)


def build_management_insight_dataset(
    loaders: tuple[LoaderSpec, ...] = ANALYSIS_LOADERS,
) -> InsightDataset:
    """Load implemented metrics and normalize them into dashboard-friendly frames."""

    long_parts: list[pd.DataFrame] = []
    metric_specs: list[InsightMetricSpec] = []
    skipped_sources: list[str] = []

    for loader_spec in loaders:
        try:
            source_frame = loader_spec.loader()
        except Exception as exc:  # pragma: no cover - defensive UI reporting path
            skipped_sources.append(f"{loader_spec.loader.__name__}: {exc}")
            continue

        for metric in loader_spec.metrics:
            required_columns = {"기준년도", "학교명", metric.source_column}
            if not required_columns.issubset(source_frame.columns):
                skipped_sources.append(f"{metric.key}: missing {metric.source_column}")
                continue

            frame = source_frame[["기준년도", "학교명", metric.source_column]].copy()
            frame = frame.rename(
                columns={
                    "기준년도": "year",
                    "학교명": "school_name",
                    metric.source_column: "value",
                }
            )
            frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
            frame = frame.dropna(subset=["year", "school_name", "value"])
            frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
            frame = frame.dropna(subset=["year"])
            frame["year"] = frame["year"].astype(int)
            frame["metric_key"] = metric.key
            frame["metric_label"] = metric.label
            frame["source_metric_id"] = metric.source_metric_id
            frame["unit"] = metric.unit
            frame["group"] = metric.group
            frame["higher_is_better"] = metric.higher_is_better
            frame["decimals"] = metric.decimals
            long_parts.append(frame)
            metric_specs.append(metric)

    if long_parts:
        long = pd.concat(long_parts, ignore_index=True)
    else:
        long = pd.DataFrame(
            columns=[
                "year",
                "school_name",
                "value",
                "metric_key",
                "metric_label",
                "source_metric_id",
                "unit",
                "group",
                "higher_is_better",
                "decimals",
            ]
        )

    wide = (
        long.pivot_table(
            index=["year", "school_name"],
            columns="metric_key",
            values="value",
            aggfunc="mean",
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )
    return InsightDataset(
        long=long,
        wide=wide,
        metrics=tuple(metric_specs),
        skipped_sources=tuple(skipped_sources),
    )


def metric_map(metrics: tuple[InsightMetricSpec, ...]) -> dict[str, InsightMetricSpec]:
    return {metric.key: metric for metric in metrics}


def available_years(long: pd.DataFrame) -> list[int]:
    if long.empty:
        return []
    return sorted(int(year) for year in long["year"].dropna().unique())


def default_analysis_year(long: pd.DataFrame) -> int | None:
    years = available_years(long)
    if not years:
        return None
    if DEFAULT_ANALYSIS_YEAR in years:
        return DEFAULT_ANALYSIS_YEAR
    return max(years)


def filter_metric_keys_by_groups(
    metrics: tuple[InsightMetricSpec, ...],
    groups: list[str] | tuple[str, ...],
) -> list[str]:
    selected_groups = set(groups)
    return [metric.key for metric in metrics if metric.group in selected_groups]


def build_percentile_profile(
    long: pd.DataFrame,
    metrics: tuple[InsightMetricSpec, ...],
    *,
    year: int,
    school_name: str,
    groups: list[str] | tuple[str, ...] | None = None,
) -> pd.DataFrame:
    """Return one selected school's percentile profile for the given year."""

    selected_groups = set(groups or [metric.group for metric in metrics])
    year_frame = long[
        (long["year"] == year)
        & (long["group"].isin(selected_groups))
    ].copy()
    rows: list[dict[str, object]] = []

    for metric in metrics:
        if metric.group not in selected_groups:
            continue
        metric_frame = year_frame[year_frame["metric_key"] == metric.key].copy()
        if metric_frame.empty or school_name not in set(metric_frame["school_name"]):
            continue

        ascending = metric.higher_is_better
        metric_frame["percentile"] = metric_frame["value"].rank(
            pct=True,
            ascending=ascending,
            method="average",
        ) * 100
        selected_row = metric_frame[metric_frame["school_name"] == school_name].iloc[0]
        rows.append(
            {
                "metric_key": metric.key,
                "metric_label": metric.label,
                "group": metric.group,
                "value": float(selected_row["value"]),
                "unit": metric.unit,
                "percentile": float(selected_row["percentile"]),
                "school_count": int(metric_frame["school_name"].nunique()),
                "higher_is_better": metric.higher_is_better,
                "decimals": metric.decimals,
            }
        )

    profile = pd.DataFrame(rows)
    if profile.empty:
        return profile
    return profile.sort_values(["percentile", "metric_label"], ascending=[True, True]).reset_index(drop=True)


def build_rank_correlation(
    wide: pd.DataFrame,
    metric_keys: list[str] | tuple[str, ...],
    *,
    year: int,
    min_pair_count: int = 10,
) -> pd.DataFrame:
    """Compute rank correlation without relying on scipy."""

    available_keys = [key for key in metric_keys if key in wide.columns]
    if not available_keys:
        return pd.DataFrame()

    year_frame = wide[wide["year"] == year][available_keys].copy()
    enough_keys = [
        key
        for key in available_keys
        if year_frame[key].notna().sum() >= min_pair_count
    ]
    if len(enough_keys) < 2:
        return pd.DataFrame()

    ranked = year_frame[enough_keys].rank(method="average")
    correlation = ranked.corr()
    pair_counts = year_frame[enough_keys].notna().astype(int).T.dot(
        year_frame[enough_keys].notna().astype(int)
    )
    return correlation.where(pair_counts >= min_pair_count)


def build_quadrant_frame(
    wide: pd.DataFrame,
    *,
    year: int,
    x_metric_key: str,
    y_metric_key: str,
) -> pd.DataFrame:
    """Return complete rows for a two-metric strategic quadrant."""

    required = ["year", "school_name", x_metric_key, y_metric_key]
    if not set(required).issubset(wide.columns):
        return pd.DataFrame(columns=required)
    return wide[wide["year"] == year][required].dropna().reset_index(drop=True)


def format_metric_value(value: float, metric: InsightMetricSpec | pd.Series) -> str:
    if isinstance(metric, pd.Series):
        decimals = int(metric["decimals"])
        unit = metric["unit"]
    else:
        decimals = metric.decimals
        unit = metric.unit
    formatted = f"{value:,.{decimals}f}"
    return f"{formatted}{unit}"


def pending_metric_roadmap_frame() -> pd.DataFrame:
    """Return non-computational roadmap status for unimplemented metrics."""

    rows = [
        ("student_recruitment", "데이터 확보", "정의 확인 완료", "구현 예정"),
        ("staff_per_student", "데이터 확보", "직원 총계 합산 규칙 확정 필요", "구현 예정"),
        ("scholarship_ratio", "데이터 확보", "등록금수입 분모 매핑 필요", "구현 예정"),
        ("corp_transfer_ratio", "일부 확보", "직접 지표/계정 매핑 확인 필요", "산식 검토"),
        ("corp_finance_ratio", "일부 확보", "법인 재정규모 분모 정의 필요", "산식 검토"),
        ("adjunct_faculty", "일부 확보", "겸임교원 확보율 공식 분모 정의 필요", "산식 검토"),
        ("classroom_area", "일부 확보", "강의실 세부 면적 정의 확인 필요", "산식 검토"),
        ("lab_area", "공개자료 한계", "계열별 실험실습실 면적 필요", "내부자료 필요"),
        ("lab_equipment", "공개자료 한계", "계열별 기자재 구입비와 2025 결산 필요", "내부자료 필요"),
    ]
    return pd.DataFrame(
        [
            {
                "metric_id": metric_id,
                "지표": METRIC_REGISTRY[metric_id].title,
                "데이터 상태": data_status,
                "정의 상태": definition_status,
                "구현 상태": implementation_status,
                "계산 포함": "아니오",
            }
            for metric_id, data_status, definition_status, implementation_status in rows
        ]
    )
