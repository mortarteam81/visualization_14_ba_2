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
            "mean": "평균",
            "max": "최댓값",
            "min": "최솟값",
            "count": "학교 수",
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
    header: str = "필터"
    school_label: str = "현재 화면에 표시할 학교"
    school_help: str | None = None
    empty_selection_message: str = "사이드바에서 학교를 하나 이상 선택하세요."
    toggles: Sequence[SidebarToggle] = field(default_factory=tuple)
    radios: Sequence[SidebarRadio] = field(default_factory=tuple)
    meta_lines: Sequence[SidebarMeta] = field(default_factory=tuple)
    divider_after_controls: bool = True
    show_profile_controls: bool = True
    profile_notice: str = "저장된 기본 비교군을 기준으로 시작하며, 여기서 바꾼 선택은 현재 화면에만 적용됩니다."
    profile_reset_label: str = "기본 비교군 다시 적용"


@dataclass(frozen=True)
class OptionSection:
    label: str
    renderer: SectionRenderer
    when: Predicate | None = None
    mode: str = "expander"
    expanded: bool = False
