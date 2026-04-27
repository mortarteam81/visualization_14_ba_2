"""Management insight dataset builders for the prototype dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Final

import pandas as pd

from registry import METRIC_REGISTRY
from utils.config import (
    CORP_TRANSFER_RATIO_COL,
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
    SCHOLARSHIP_RATIO_COL,
    STAFF_PER_STUDENT_COL,
)
from utils.data_pipeline import (
    load_budam_frame,
    load_corp_transfer_ratio_frame,
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
    load_scholarship_ratio_frame,
    load_staff_per_student_frame,
)


DEFAULT_ANALYSIS_YEAR: Final[int] = 2024
PENDING_METRIC_IDS: Final[tuple[str, ...]] = (
    "corp_finance_ratio",
    "student_recruitment",
    "adjunct_faculty",
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
        load_corp_transfer_ratio_frame,
        (
            InsightMetricSpec(
                key="corp_transfer_ratio",
                label="법인전입금 비율",
                source_metric_id="corp_transfer_ratio",
                source_column=CORP_TRANSFER_RATIO_COL,
                unit="%",
                group="재정",
                decimals=2,
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
    LoaderSpec(
        load_staff_per_student_frame,
        (
            InsightMetricSpec(
                key="students_per_staff",
                label="직원 1인당 학생수",
                source_metric_id="staff_per_student",
                source_column=STAFF_PER_STUDENT_COL,
                unit="명",
                group="교육여건",
                higher_is_better=False,
            ),
        ),
    ),
    LoaderSpec(
        load_scholarship_ratio_frame,
        (
            InsightMetricSpec(
                key="scholarship_ratio",
                label="장학금 비율",
                source_metric_id="scholarship_ratio",
                source_column=SCHOLARSHIP_RATIO_COL,
                unit="%",
                group="재정",
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


def build_quadrant_path_frame(
    wide: pd.DataFrame,
    *,
    start_year: int,
    end_year: int,
    x_metric_key: str,
    y_metric_key: str,
    schools: list[str] | tuple[str, ...],
) -> pd.DataFrame:
    """Return start/end quadrant positions for selected schools."""

    if start_year > end_year:
        start_year, end_year = end_year, start_year

    required = {"year", "school_name", x_metric_key, y_metric_key}
    if not required.issubset(wide.columns) or not schools:
        return pd.DataFrame(
            columns=[
                "school_name",
                "phase",
                "year",
                x_metric_key,
                y_metric_key,
            ]
        )

    rows: list[pd.Series] = []
    for school in schools:
        school_frame = wide[
            (wide["school_name"] == school)
            & (wide["year"] >= start_year)
            & (wide["year"] <= end_year)
        ][["year", "school_name", x_metric_key, y_metric_key]].dropna().sort_values("year")
        if len(school_frame) < 2:
            continue
        first = school_frame.iloc[0].copy()
        first["phase"] = "시작"
        last = school_frame.iloc[-1].copy()
        last["phase"] = "종료"
        rows.extend([first, last])

    if not rows:
        return pd.DataFrame(
            columns=[
                "school_name",
                "phase",
                "year",
                x_metric_key,
                y_metric_key,
            ]
        )
    return pd.DataFrame(rows).reset_index(drop=True)


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


def _to_json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _to_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_json_safe(item) for item in value]
    if hasattr(value, "item"):
        try:
            return _to_json_safe(value.item())
        except Exception:
            pass
    return str(value)


def _metric_keys_for_groups(
    metrics: tuple[InsightMetricSpec, ...],
    groups: list[str] | tuple[str, ...] | None,
) -> list[str]:
    selected_groups = set(groups or [metric.group for metric in metrics])
    return [metric.key for metric in metrics if metric.group in selected_groups]


def _metric_record_from_profile(row: pd.Series) -> dict[str, Any]:
    return {
        "metric_key": str(row["metric_key"]),
        "metric_label": str(row["metric_label"]),
        "group": str(row["group"]),
        "value": round(float(row["value"]), int(row["decimals"])),
        "formatted_value": format_metric_value(float(row["value"]), row),
        "unit": str(row["unit"]),
        "percentile": round(float(row["percentile"]), 1),
        "school_count": int(row["school_count"]),
        "higher_is_better": bool(row["higher_is_better"]),
    }


def _profile_summary(profile: pd.DataFrame, *, limit: int = 5) -> dict[str, list[dict[str, Any]]]:
    if profile.empty:
        return {"strengths": [], "weaknesses": []}

    return {
        "strengths": [
            _metric_record_from_profile(row)
            for _, row in profile.sort_values("percentile", ascending=False).head(limit).iterrows()
        ],
        "weaknesses": [
            _metric_record_from_profile(row)
            for _, row in profile.sort_values("percentile", ascending=True).head(limit).iterrows()
        ],
    }


def _comparison_gap_item(
    *,
    metric: InsightMetricSpec,
    focus_value: float,
    comparison_average: float,
    comparison_school_count: int,
) -> dict[str, Any]:
    raw_gap = focus_value - comparison_average
    adjusted_gap = raw_gap if metric.higher_is_better else -raw_gap
    return {
        "metric_key": metric.key,
        "metric_label": metric.label,
        "group": metric.group,
        "focus_value": round(focus_value, metric.decimals),
        "comparison_average": round(comparison_average, metric.decimals),
        "raw_gap": round(raw_gap, metric.decimals),
        "adjusted_gap": round(adjusted_gap, metric.decimals),
        "gap_interpretation": "기준 대학 우위" if adjusted_gap > 0 else "기준 대학 열위" if adjusted_gap < 0 else "비슷함",
        "comparison_school_count": comparison_school_count,
        "unit": metric.unit,
        "higher_is_better": metric.higher_is_better,
    }


def _comparison_gap_summary(
    long: pd.DataFrame,
    metrics: tuple[InsightMetricSpec, ...],
    *,
    year: int,
    focus_school: str,
    comparison_schools: list[str],
    groups: list[str] | tuple[str, ...] | None,
    limit: int = 5,
) -> dict[str, list[dict[str, Any]]]:
    if not comparison_schools:
        return {"favorable": [], "unfavorable": []}

    selected_metric_keys = set(_metric_keys_for_groups(metrics, groups))
    rows: list[dict[str, Any]] = []
    for metric in metrics:
        if metric.key not in selected_metric_keys:
            continue
        metric_frame = long[(long["year"] == year) & (long["metric_key"] == metric.key)].copy()
        focus_frame = metric_frame[metric_frame["school_name"] == focus_school]
        comparison_frame = metric_frame[metric_frame["school_name"].isin(comparison_schools)]
        if focus_frame.empty or comparison_frame.empty:
            continue

        focus_value = float(focus_frame.iloc[0]["value"])
        comparison_average = float(comparison_frame["value"].mean())
        rows.append(
            _comparison_gap_item(
                metric=metric,
                focus_value=focus_value,
                comparison_average=comparison_average,
                comparison_school_count=comparison_frame["school_name"].nunique(),
            )
        )

    sorted_rows = sorted(rows, key=lambda item: float(item["adjusted_gap"]))
    return {
        "favorable": list(reversed(sorted_rows[-limit:])),
        "unfavorable": sorted_rows[:limit],
    }


def summarize_rank_correlation_pairs(
    wide: pd.DataFrame,
    metrics: tuple[InsightMetricSpec, ...],
    metric_keys: list[str] | tuple[str, ...],
    *,
    year: int,
    min_pair_count: int = 10,
    top_n: int = 5,
) -> dict[str, list[dict[str, Any]]]:
    """Return compact positive/negative rank-correlation pairs for AI context."""

    correlation = build_rank_correlation(
        wide,
        metric_keys,
        year=year,
        min_pair_count=min_pair_count,
    )
    if correlation.empty:
        return {"positive": [], "negative": []}

    metrics_by_key = metric_map(metrics)
    pairs: list[dict[str, Any]] = []
    columns = list(correlation.columns)
    for left_index, left_key in enumerate(columns):
        for right_key in columns[left_index + 1:]:
            value = correlation.loc[left_key, right_key]
            if pd.isna(value):
                continue
            pairs.append(
                {
                    "left_metric_key": left_key,
                    "left_metric_label": metrics_by_key[left_key].label,
                    "right_metric_key": right_key,
                    "right_metric_label": metrics_by_key[right_key].label,
                    "rank_correlation": round(float(value), 3),
                }
            )

    positive = sorted(
        [item for item in pairs if float(item["rank_correlation"]) > 0],
        key=lambda item: float(item["rank_correlation"]),
        reverse=True,
    )[:top_n]
    negative = sorted(
        [item for item in pairs if float(item["rank_correlation"]) < 0],
        key=lambda item: float(item["rank_correlation"]),
    )[:top_n]
    return {"positive": positive, "negative": negative}


def _quadrant_summary(
    wide: pd.DataFrame,
    metrics: tuple[InsightMetricSpec, ...],
    *,
    year: int,
    focus_school: str,
    quadrant_preset: tuple[str, str, str],
) -> dict[str, Any]:
    preset_label, x_key, y_key = quadrant_preset
    metrics_by_key = metric_map(metrics)
    if x_key not in metrics_by_key or y_key not in metrics_by_key:
        return {}

    frame = build_quadrant_frame(
        wide,
        year=year,
        x_metric_key=x_key,
        y_metric_key=y_key,
    )
    focus_frame = frame[frame["school_name"] == focus_school]
    if frame.empty or focus_frame.empty:
        return {}

    focus_row = focus_frame.iloc[0]
    x_median = float(frame[x_key].median())
    y_median = float(frame[y_key].median())
    x_value = float(focus_row[x_key])
    y_value = float(focus_row[y_key])
    return {
        "preset": preset_label,
        "year": year,
        "school_count": int(frame["school_name"].nunique()),
        "x_metric": {
            "metric_key": x_key,
            "metric_label": metrics_by_key[x_key].label,
            "value": round(x_value, metrics_by_key[x_key].decimals),
            "median": round(x_median, metrics_by_key[x_key].decimals),
            "position_vs_median": "높음" if x_value >= x_median else "낮음",
            "higher_is_better": metrics_by_key[x_key].higher_is_better,
            "unit": metrics_by_key[x_key].unit,
        },
        "y_metric": {
            "metric_key": y_key,
            "metric_label": metrics_by_key[y_key].label,
            "value": round(y_value, metrics_by_key[y_key].decimals),
            "median": round(y_median, metrics_by_key[y_key].decimals),
            "position_vs_median": "높음" if y_value >= y_median else "낮음",
            "higher_is_better": metrics_by_key[y_key].higher_is_better,
            "unit": metrics_by_key[y_key].unit,
        },
    }


def _pending_metric_status_summary() -> list[dict[str, Any]]:
    roadmap = pending_metric_roadmap_frame()
    return [
        {
            "metric_id": str(row["metric_id"]),
            "metric_label": str(row["지표"]),
            "data_status": str(row["데이터 상태"]),
            "definition_status": str(row["정의 상태"]),
            "implementation_status": str(row["구현 상태"]),
            "calculation_included": False,
        }
        for _, row in roadmap.iterrows()
    ]


def _coverage_summary(
    long: pd.DataFrame,
    metric_keys: list[str] | tuple[str, ...],
    *,
    years: list[int],
) -> dict[str, Any]:
    if not years:
        return {"years": [], "warnings": []}

    total_metric_count = len(metric_keys)
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for year in years:
        year_frame = long[(long["year"] == year) & (long["metric_key"].isin(metric_keys))]
        metric_count = int(year_frame["metric_key"].nunique())
        school_count = int(year_frame["school_name"].nunique())
        coverage_ratio = metric_count / total_metric_count if total_metric_count else 0
        row = {
            "year": year,
            "metric_count": metric_count,
            "school_count": school_count,
            "coverage_ratio": round(coverage_ratio, 3),
        }
        rows.append(row)
        if coverage_ratio < 0.8:
            warnings.append(
                f"{year}년은 선택 지표 {total_metric_count}개 중 {metric_count}개만 있어 범위 해석에 주의가 필요합니다."
            )

    return {"years": rows, "warnings": warnings}


def build_single_year_management_ai_payload(
    dataset: InsightDataset,
    *,
    year: int,
    focus_school: str,
    comparison_schools: list[str],
    groups: list[str] | tuple[str, ...] | None,
    quadrant_preset: tuple[str, str, str] = QUADRANT_PRESETS[0],
    min_pair_count: int = 10,
) -> dict[str, Any]:
    """Build a compact, sanitized single-year AI context for management insights."""

    metric_keys = _metric_keys_for_groups(dataset.metrics, groups)
    profile = build_percentile_profile(
        dataset.long,
        dataset.metrics,
        year=year,
        school_name=focus_school,
        groups=groups,
    )
    payload = {
        "analysis_mode": "single_year",
        "year": year,
        "focus_school": focus_school,
        "comparison_schools": comparison_schools,
        "included_series_count": len(metric_keys),
        "excluded_pending_metric_count": dataset.pending_metric_count,
        "coverage": _coverage_summary(dataset.long, metric_keys, years=[year]),
        "strength_weakness_profile": _profile_summary(profile),
        "comparison_gaps": _comparison_gap_summary(
            dataset.long,
            dataset.metrics,
            year=year,
            focus_school=focus_school,
            comparison_schools=comparison_schools,
            groups=groups,
        ),
        "quadrant": _quadrant_summary(
            dataset.wide,
            dataset.metrics,
            year=year,
            focus_school=focus_school,
            quadrant_preset=quadrant_preset,
        ),
        "correlation_hypotheses": summarize_rank_correlation_pairs(
            dataset.wide,
            dataset.metrics,
            metric_keys,
            year=year,
            min_pair_count=min_pair_count,
        ),
        "pending_metrics": _pending_metric_status_summary(),
        "guardrails": [
            "이 payload는 구현 완료 지표의 요약값만 포함하며 원시 로그, 쿠키, 원시 HTML/JSON은 포함하지 않습니다.",
            "미구현 지표는 계산값이 아니라 로드맵 상태로만 해석해야 합니다.",
            "상관관계는 정책 가설 탐색용이며 인과관계를 의미하지 않습니다.",
        ],
    }
    return _to_json_safe(payload)


def build_range_metric_change_frame(
    long: pd.DataFrame,
    metrics: tuple[InsightMetricSpec, ...],
    *,
    start_year: int,
    end_year: int,
    focus_school: str,
    groups: list[str] | tuple[str, ...] | None,
) -> pd.DataFrame:
    """Return all focus-school metric changes in a year range."""

    if start_year > end_year:
        start_year, end_year = end_year, start_year

    selected_metric_keys = set(_metric_keys_for_groups(metrics, groups))
    selected_years = sorted(
        int(year)
        for year in long.loc[
            (long["year"] >= start_year) & (long["year"] <= end_year),
            "year",
        ].dropna().unique()
    )
    profiles_by_year = {
        year: build_percentile_profile(
            long,
            metrics,
            year=year,
            school_name=focus_school,
            groups=groups,
        ).set_index("metric_key")
        for year in selected_years
    }

    rows: list[dict[str, Any]] = []
    for metric in metrics:
        if metric.key not in selected_metric_keys:
            continue
        metric_frame = long[
            (long["metric_key"] == metric.key)
            & (long["school_name"] == focus_school)
            & (long["year"] >= start_year)
            & (long["year"] <= end_year)
        ].sort_values("year")
        if len(metric_frame) < 2:
            continue

        first = metric_frame.iloc[0]
        last = metric_frame.iloc[-1]
        raw_delta = float(last["value"]) - float(first["value"])
        adjusted_delta = raw_delta if metric.higher_is_better else -raw_delta
        first_profile = profiles_by_year.get(int(first["year"]), pd.DataFrame())
        last_profile = profiles_by_year.get(int(last["year"]), pd.DataFrame())
        first_percentile = (
            float(first_profile.loc[metric.key, "percentile"])
            if not first_profile.empty and metric.key in first_profile.index
            else None
        )
        last_percentile = (
            float(last_profile.loc[metric.key, "percentile"])
            if not last_profile.empty and metric.key in last_profile.index
            else None
        )
        percentile_delta = (
            round(last_percentile - first_percentile, 1)
            if first_percentile is not None and last_percentile is not None
            else None
        )
        rows.append(
            {
                "metric_key": metric.key,
                "metric_label": metric.label,
                "group": metric.group,
                "first_year": int(first["year"]),
                "last_year": int(last["year"]),
                "first_value": round(float(first["value"]), metric.decimals),
                "last_value": round(float(last["value"]), metric.decimals),
                "raw_delta": round(raw_delta, metric.decimals),
                "adjusted_delta": round(adjusted_delta, metric.decimals),
                "first_percentile": round(first_percentile, 1) if first_percentile is not None else None,
                "last_percentile": round(last_percentile, 1) if last_percentile is not None else None,
                "percentile_delta": percentile_delta,
                "trend_interpretation": "개선" if adjusted_delta > 0 else "악화" if adjusted_delta < 0 else "보합",
                "unit": metric.unit,
                "decimals": metric.decimals,
                "higher_is_better": metric.higher_is_better,
            }
        )

    return pd.DataFrame(rows)


def build_range_profile_classification(
    long: pd.DataFrame,
    metrics: tuple[InsightMetricSpec, ...],
    *,
    start_year: int,
    end_year: int,
    focus_school: str,
    groups: list[str] | tuple[str, ...] | None,
    strength_threshold: float = 65.0,
    weakness_threshold: float = 35.0,
    trend_threshold: float = 5.0,
) -> pd.DataFrame:
    """Classify range changes into management-friendly profile buckets."""

    frame = build_range_metric_change_frame(
        long,
        metrics,
        start_year=start_year,
        end_year=end_year,
        focus_school=focus_school,
        groups=groups,
    )
    if frame.empty:
        return frame.assign(classification=pd.Series(dtype="object"))

    def classify(row: pd.Series) -> str:
        current = row["last_percentile"]
        delta = row["percentile_delta"]
        if pd.isna(current):
            return "관찰 유지"
        if current < weakness_threshold and (pd.isna(delta) or delta <= trend_threshold):
            return "구조적 취약"
        if current >= strength_threshold and (pd.isna(delta) or delta >= -trend_threshold):
            return "현재 강점"
        if not pd.isna(delta) and delta >= trend_threshold:
            return "개선 중"
        if not pd.isna(delta) and delta <= -trend_threshold:
            return "악화 중"
        return "관찰 유지"

    classified = frame.copy()
    classified["classification"] = classified.apply(classify, axis=1)
    return classified.sort_values(
        ["classification", "last_percentile", "percentile_delta", "metric_label"],
        ascending=[True, False, False, True],
    ).reset_index(drop=True)


def _range_metric_changes(
    long: pd.DataFrame,
    metrics: tuple[InsightMetricSpec, ...],
    *,
    start_year: int,
    end_year: int,
    focus_school: str,
    groups: list[str] | tuple[str, ...] | None,
    limit: int = 6,
) -> dict[str, list[dict[str, Any]]]:
    frame = build_range_metric_change_frame(
        long,
        metrics,
        start_year=start_year,
        end_year=end_year,
        focus_school=focus_school,
        groups=groups,
    )
    if frame.empty:
        return {"improved": [], "declined": []}

    rows = frame.to_dict("records")
    improved = sorted(
        [item for item in rows if float(item["adjusted_delta"]) > 0],
        key=lambda item: (item["percentile_delta"] is not None, item["percentile_delta"] or 0, float(item["adjusted_delta"])),
        reverse=True,
    )[:limit]
    declined = sorted(
        [item for item in rows if float(item["adjusted_delta"]) < 0],
        key=lambda item: (item["percentile_delta"] is None, item["percentile_delta"] or 0, float(item["adjusted_delta"])),
    )[:limit]
    return {"improved": improved, "declined": declined}


def _range_comparison_gap_changes(
    long: pd.DataFrame,
    metrics: tuple[InsightMetricSpec, ...],
    *,
    start_year: int,
    end_year: int,
    focus_school: str,
    comparison_schools: list[str],
    groups: list[str] | tuple[str, ...] | None,
    limit: int = 5,
) -> dict[str, list[dict[str, Any]]]:
    if not comparison_schools:
        return {"improved_vs_comparison": [], "worsened_vs_comparison": []}

    selected_metric_keys = set(_metric_keys_for_groups(metrics, groups))
    rows: list[dict[str, Any]] = []
    for metric in metrics:
        if metric.key not in selected_metric_keys:
            continue
        metric_frame = long[
            (long["metric_key"] == metric.key)
            & (long["year"] >= start_year)
            & (long["year"] <= end_year)
        ].copy()
        focus_frame = metric_frame[metric_frame["school_name"] == focus_school].sort_values("year")
        if len(focus_frame) < 2:
            continue

        first = focus_frame.iloc[0]
        last = focus_frame.iloc[-1]
        comparison_first = metric_frame[
            (metric_frame["year"] == first["year"])
            & (metric_frame["school_name"].isin(comparison_schools))
        ]
        comparison_last = metric_frame[
            (metric_frame["year"] == last["year"])
            & (metric_frame["school_name"].isin(comparison_schools))
        ]
        if comparison_first.empty or comparison_last.empty:
            continue

        first_raw_gap = float(first["value"]) - float(comparison_first["value"].mean())
        last_raw_gap = float(last["value"]) - float(comparison_last["value"].mean())
        first_adjusted_gap = first_raw_gap if metric.higher_is_better else -first_raw_gap
        last_adjusted_gap = last_raw_gap if metric.higher_is_better else -last_raw_gap
        adjusted_gap_delta = last_adjusted_gap - first_adjusted_gap
        rows.append(
            {
                "metric_key": metric.key,
                "metric_label": metric.label,
                "group": metric.group,
                "first_year": int(first["year"]),
                "last_year": int(last["year"]),
                "first_adjusted_gap": round(first_adjusted_gap, metric.decimals),
                "last_adjusted_gap": round(last_adjusted_gap, metric.decimals),
                "adjusted_gap_delta": round(adjusted_gap_delta, metric.decimals),
                "gap_change_interpretation": (
                    "비교대학 대비 개선"
                    if adjusted_gap_delta > 0
                    else "비교대학 대비 악화"
                    if adjusted_gap_delta < 0
                    else "비슷함"
                ),
                "comparison_school_count": int(comparison_last["school_name"].nunique()),
                "unit": metric.unit,
                "higher_is_better": metric.higher_is_better,
            }
        )

    sorted_rows = sorted(rows, key=lambda item: float(item["adjusted_gap_delta"]))
    return {
        "improved_vs_comparison": list(reversed(sorted_rows[-limit:])),
        "worsened_vs_comparison": sorted_rows[:limit],
    }


def build_comparison_gap_trend_frame(
    long: pd.DataFrame,
    metrics: tuple[InsightMetricSpec, ...],
    *,
    start_year: int,
    end_year: int,
    focus_school: str,
    comparison_schools: list[str],
    groups: list[str] | tuple[str, ...] | None,
) -> pd.DataFrame:
    """Return yearly focus-vs-comparison gaps by metric."""

    if start_year > end_year:
        start_year, end_year = end_year, start_year
    if not comparison_schools:
        return pd.DataFrame()

    selected_metric_keys = set(_metric_keys_for_groups(metrics, groups))
    rows: list[dict[str, Any]] = []
    for metric in metrics:
        if metric.key not in selected_metric_keys:
            continue
        metric_frame = long[
            (long["metric_key"] == metric.key)
            & (long["year"] >= start_year)
            & (long["year"] <= end_year)
        ].copy()
        for year in sorted(metric_frame["year"].dropna().astype(int).unique()):
            year_frame = metric_frame[metric_frame["year"] == year]
            focus_frame = year_frame[year_frame["school_name"] == focus_school]
            comparison_frame = year_frame[year_frame["school_name"].isin(comparison_schools)]
            if focus_frame.empty or comparison_frame.empty:
                continue

            focus_value = float(focus_frame.iloc[0]["value"])
            comparison_average = float(comparison_frame["value"].mean())
            raw_gap = focus_value - comparison_average
            adjusted_gap = raw_gap if metric.higher_is_better else -raw_gap
            rows.append(
                {
                    "year": int(year),
                    "metric_key": metric.key,
                    "metric_label": metric.label,
                    "group": metric.group,
                    "focus_school": focus_school,
                    "focus_value": round(focus_value, metric.decimals),
                    "comparison_average": round(comparison_average, metric.decimals),
                    "raw_gap": round(raw_gap, metric.decimals),
                    "adjusted_gap": round(adjusted_gap, metric.decimals),
                    "comparison_school_count": int(comparison_frame["school_name"].nunique()),
                    "unit": metric.unit,
                    "higher_is_better": metric.higher_is_better,
                }
            )

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(["metric_label", "year"]).reset_index(drop=True)


def build_range_management_ai_payload(
    dataset: InsightDataset,
    *,
    start_year: int,
    end_year: int,
    focus_school: str,
    comparison_schools: list[str],
    groups: list[str] | tuple[str, ...] | None,
) -> dict[str, Any]:
    """Build a compact, sanitized multi-year AI context for management insights."""

    if start_year > end_year:
        start_year, end_year = end_year, start_year

    metric_keys = _metric_keys_for_groups(dataset.metrics, groups)
    selected_years = [
        year
        for year in available_years(dataset.long)
        if start_year <= year <= end_year
    ]
    actual_end_year = max(selected_years) if selected_years else end_year
    latest_profile = build_percentile_profile(
        dataset.long,
        dataset.metrics,
        year=actual_end_year,
        school_name=focus_school,
        groups=groups,
    )
    payload = {
        "analysis_mode": "year_range",
        "start_year": start_year,
        "end_year": end_year,
        "available_years_in_range": selected_years,
        "focus_school": focus_school,
        "comparison_schools": comparison_schools,
        "included_series_count": len(metric_keys),
        "excluded_pending_metric_count": dataset.pending_metric_count,
        "coverage": _coverage_summary(dataset.long, metric_keys, years=selected_years),
        "latest_strength_weakness_profile": _profile_summary(latest_profile),
        "trend_changes": _range_metric_changes(
            dataset.long,
            dataset.metrics,
            start_year=start_year,
            end_year=end_year,
            focus_school=focus_school,
            groups=groups,
        ),
        "comparison_gap_changes": _range_comparison_gap_changes(
            dataset.long,
            dataset.metrics,
            start_year=start_year,
            end_year=end_year,
            focus_school=focus_school,
            comparison_schools=comparison_schools,
            groups=groups,
        ),
        "pending_metrics": _pending_metric_status_summary(),
        "guardrails": [
            "이 payload는 구현 완료 지표의 요약값만 포함하며 원시 로그, 쿠키, 원시 HTML/JSON은 포함하지 않습니다.",
            "미구현 지표는 계산값이 아니라 로드맵 상태로만 해석해야 합니다.",
            "연도별 지표 커버리지가 다른 경우 장기 추세 해석에 주의해야 합니다.",
        ],
    }
    return _to_json_safe(payload)
