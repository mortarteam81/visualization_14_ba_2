"""Reusable Streamlit UI helpers for metric pages."""

from .kpi import build_dual_metric_kpis, build_single_metric_kpis, render_kpis
from .models import (
    KPIItem,
    MetricSpec,
    OptionSection,
    SidebarConfig,
    SidebarMeta,
    SidebarRadio,
    SidebarToggle,
    ThresholdSpec,
)
from .renderers import (
    render_dual_metric_page,
    render_optional_page,
    render_single_metric_page,
)
from .sidebar import render_school_sidebar
from .tables import (
    build_pivot_table,
    build_yearly_stats,
    render_definition_table,
    render_pivot_table,
    render_stats_table,
)

__all__ = [
    "KPIItem",
    "MetricSpec",
    "OptionSection",
    "SidebarConfig",
    "SidebarMeta",
    "SidebarRadio",
    "SidebarToggle",
    "ThresholdSpec",
    "build_dual_metric_kpis",
    "build_pivot_table",
    "build_single_metric_kpis",
    "build_yearly_stats",
    "render_dual_metric_page",
    "render_definition_table",
    "render_kpis",
    "render_optional_page",
    "render_pivot_table",
    "render_school_sidebar",
    "render_single_metric_page",
    "render_stats_table",
]
