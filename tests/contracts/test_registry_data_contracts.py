from __future__ import annotations

from pathlib import Path

import pytest

from registry import MetricSpec, list_metrics
from utils.query import get_dataset


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"


def _implemented_metrics() -> list[MetricSpec]:
    return [metric for metric in list_metrics() if metric.implemented]


@pytest.mark.parametrize("metric", _implemented_metrics(), ids=lambda metric: metric.id)
def test_implemented_metric_registry_points_to_existing_assets(metric: MetricSpec) -> None:
    assert metric.page_path, f"{metric.id} must declare a Streamlit page path"
    assert (PROJECT_ROOT / metric.page_path).exists()
    assert metric.csv_file, f"{metric.id} must declare a CSV asset"
    assert (DATA_DIR / metric.csv_file).exists()
    assert metric.series, f"{metric.id} must declare at least one output series"


@pytest.mark.parametrize("metric", _implemented_metrics(), ids=lambda metric: metric.id)
def test_implemented_metric_dataset_matches_series_contract(metric: MetricSpec) -> None:
    frame = get_dataset(metric.dataset_key)

    assert not frame.empty, f"{metric.id} dataset should not be empty"
    assert {"기준년도", "학교명"}.issubset(frame.columns)
    for series in metric.series:
        assert series.column in frame.columns
