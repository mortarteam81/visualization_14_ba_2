"""Data models for reusable Streamlit UI renderers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence


Formatter = Callable[[Any], str]
Predicate = Callable[[Mapping[str, Any]], bool]
SectionRenderer = Callable[[Mapping[str, Any]], None]


@dataclass(frozen=True)
class ThresholdSpec:
    value: float
    label: str
    color: str | None = None
    dash: str = "dash"
    annotation_position: str = "top right"


@dataclass(frozen=True)
class MetricSpec:
    key: str
    label: str
    value_col: str
    y_axis_label: str
    precision: int = 1
    threshold: ThresholdSpec | None = None
    higher_is_better: bool = True
    stats_labels: Mapping[str, str] = field(
        default_factory=lambda: {
            "mean": "Average",
            "max": "Max",
            "min": "Min",
            "count": "Schools",
        }
    )
    chart_title: str | None = None
    chart_color: str | None = None
    formatter: Formatter | None = None


@dataclass(frozen=True)
class KPIItem:
    label: str
    value: str
    delta: str | None = None
    help: str | None = None
    delta_color: str = "normal"


@dataclass(frozen=True)
class SidebarToggle:
    key: str
    label: str
    value: bool = False
    help: str | None = None


@dataclass(frozen=True)
class SidebarRadio:
    key: str
    label: str
    options: Sequence[str]
    index: int = 0
    help: str | None = None
    horizontal: bool = False


@dataclass(frozen=True)
class SidebarMeta:
    text: str


@dataclass(frozen=True)
class SidebarConfig:
    header: str = "Filters"
    school_label: str = "Select schools"
    school_help: str | None = None
    empty_selection_message: str = "Select at least one school from the sidebar."
    toggles: Sequence[SidebarToggle] = field(default_factory=tuple)
    radios: Sequence[SidebarRadio] = field(default_factory=tuple)
    meta_lines: Sequence[SidebarMeta] = field(default_factory=tuple)
    divider_after_controls: bool = True


@dataclass(frozen=True)
class OptionSection:
    label: str
    renderer: SectionRenderer
    when: Predicate | None = None
    mode: str = "expander"
    expanded: bool = False
