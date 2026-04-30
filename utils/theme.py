"""Global Streamlit theme helpers for the dashboard UI."""

from __future__ import annotations

import streamlit as st


MOBILE_COMPACT_MODE_KEY = "mobile_compact_mode"
MOBILE_COMPACT_INLINE_TOGGLE_KEY = "mobile_compact_mode_inline_toggle"
MOBILE_COMPACT_SIDEBAR_TOGGLE_KEY = "mobile_compact_mode_sidebar_toggle"


DARK_THEME_CSS = """
<style>
:root {
    --app-bg: #0d1117;
    --panel-bg: rgba(18, 24, 33, 0.94);
    --panel-bg-strong: rgba(18, 24, 33, 0.98);
    --panel-border: rgba(181, 190, 204, 0.18);
    --panel-shadow: 0 12px 28px rgba(0, 0, 0, 0.28);
    --radius-panel: 8px;
    --text-primary: #f8fbff;
    --text-secondary: #dde6f3;
    --text-muted: #b7c4d8;
    --accent: #4f8cff;
    --accent-soft: rgba(79, 140, 255, 0.14);
    --gold: #f59e0b;
    --success: #22c55e;
    --danger: #f87171;
}

.stApp {
    background: linear-gradient(180deg, #0d1117 0%, #111827 52%, #16130f 100%);
    color: var(--text-primary);
}

[data-testid="stAppViewContainer"] > .main {
    background: transparent;
}

[data-testid="stHeader"] {
    background: rgba(11, 15, 20, 0.72);
    backdrop-filter: blur(14px);
}

[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, rgba(15, 23, 42, 0.98) 0%, rgba(12, 18, 29, 0.98) 100%);
    border-right: 1px solid var(--panel-border);
}

[data-testid="stSidebar"] * {
    color: var(--text-primary);
}

.block-container {
    max-width: 1360px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

h1, h2, h3, h4, h5, h6 {
    color: var(--text-primary);
    letter-spacing: 0;
}

.stApp p,
.stApp li,
.stApp label,
.stApp span,
.stApp div,
.stMarkdown,
.stText,
[data-testid="stMarkdownContainer"],
[data-testid="stCaptionContainer"] {
    color: var(--text-secondary);
}

.stCaption,
.stCaption p,
[data-testid="stCaptionContainer"] p {
    color: var(--text-secondary) !important;
}

[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4,
[data-testid="stMarkdownContainer"] h5,
[data-testid="stMarkdownContainer"] h6 {
    color: var(--text-primary) !important;
}

[data-testid="stExpander"] details summary,
[data-testid="stExpander"] details summary p,
[data-testid="stExpander"] details summary span,
[data-testid="stExpander"] details summary svg,
[data-testid="stExpanderToggleIcon"] {
    color: var(--text-primary) !important;
    fill: var(--text-primary) !important;
    font-weight: 700 !important;
}

[data-testid="stExpanderDetails"] p,
[data-testid="stExpanderDetails"] span,
[data-testid="stExpanderDetails"] div {
    color: var(--text-secondary) !important;
}

.stApp h2,
.stApp h3 {
    color: var(--text-primary) !important;
}

.stApp h2 + p,
.stApp h3 + p {
    color: var(--text-secondary) !important;
}

[data-testid="stMetric"],
.stAlert,
[data-testid="stExpander"],
[data-testid="stDataFrame"],
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
div[data-baseweb="popover"] > div {
    background: var(--panel-bg);
    border: 1px solid var(--panel-border);
    box-shadow: var(--panel-shadow);
    border-radius: var(--radius-panel);
}

[data-testid="stMetric"] {
    padding: 1rem 1.1rem;
}

[data-testid="stMetricLabel"],
[data-testid="stMetricDelta"] {
    color: var(--text-muted) !important;
}

[data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
}

.stAlert {
    color: var(--text-primary);
}

.stAlert a {
    color: #93c5fd;
}

[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 0.5rem;
    background: transparent;
}

[data-testid="stTabs"] [data-baseweb="tab"] {
    border-radius: var(--radius-panel);
    background: rgba(15, 23, 42, 0.72);
    border: 1px solid var(--panel-border);
    color: var(--text-secondary) !important;
    padding: 0.45rem 0.9rem;
}

[data-testid="stTabs"] [aria-selected="true"] {
    background: linear-gradient(180deg, rgba(79, 140, 255, 0.25), rgba(79, 140, 255, 0.12));
    color: var(--text-primary) !important;
    border-color: rgba(79, 140, 255, 0.45);
}

.stButton > button,
.stDownloadButton > button,
[data-testid="baseButton-secondary"] {
    background: linear-gradient(180deg, #1d4ed8 0%, #1e40af 100%);
    color: white;
    border: 1px solid rgba(147, 197, 253, 0.25);
    border-radius: var(--radius-panel);
    box-shadow: 0 14px 30px rgba(30, 64, 175, 0.28);
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    border-color: rgba(191, 219, 254, 0.55);
    transform: translateY(-1px);
}

.stMultiSelect [data-baseweb="tag"] {
    background: var(--accent-soft);
    border: 1px solid rgba(79, 140, 255, 0.35);
    color: var(--text-primary) !important;
}

div[data-baseweb="select"] svg,
div[data-baseweb="input"] svg,
.stMarkdown hr {
    color: var(--text-secondary);
}

.stMarkdown hr {
    border-color: rgba(148, 163, 184, 0.16);
}

div[data-testid="stDataFrame"] div[role="table"] {
    color: var(--text-primary) !important;
}

div[data-testid="stDataFrame"] th,
div[data-testid="stDataFrame"] td,
div[data-testid="stDataFrame"] label,
div[data-testid="stDataFrame"] p,
div[data-testid="stDataFrame"] span {
    color: #dbe5f3 !important;
}

[data-testid="stDataFrameResizable"] {
    background: transparent;
}

section[data-testid="stSidebar"] .stButton > button {
    width: 100%;
}

a {
    color: #93c5fd;
}

[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] .stCaption p,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span {
    color: var(--text-secondary) !important;
}

.mobile-compact-callout {
    border: 1px solid rgba(45, 212, 191, 0.72);
    border-radius: 8px;
    background:
        linear-gradient(135deg, rgba(20, 184, 166, 0.28), rgba(245, 158, 11, 0.18)),
        rgba(15, 23, 42, 0.92);
    box-shadow: 0 10px 22px rgba(20, 184, 166, 0.12);
    padding: 0.85rem 0.9rem;
    margin: 0.6rem 0 0.75rem;
}

.mobile-compact-callout--inline {
    border-color: rgba(251, 191, 36, 0.9);
    background:
        linear-gradient(135deg, rgba(20, 184, 166, 0.34), rgba(245, 158, 11, 0.24)),
        rgba(15, 23, 42, 0.96);
    box-shadow: 0 16px 32px rgba(245, 158, 11, 0.14);
    margin: 0 0 0.85rem;
}

.mobile-compact-callout__title {
    color: #5EEAD4 !important;
    font-weight: 800;
    font-size: 0.98rem;
    margin: 0 0 0.28rem;
}

.mobile-compact-callout__body {
    color: #F8FBFF !important;
    font-size: 0.84rem;
    line-height: 1.45;
    margin: 0;
}

[data-testid="stSidebar"] [data-testid="stToggle"] label p {
    color: #FDE68A !important;
    font-weight: 800 !important;
}

[data-testid="stAppViewContainer"] [data-testid="stToggle"] label p {
    color: #FDE68A !important;
    font-weight: 800 !important;
}

@media (max-width: 768px) {
    .block-container {
        max-width: 100%;
        padding: 1rem 0.75rem 2rem;
    }

    .mobile-compact-callout--inline {
        margin-top: 0.75rem;
    }

    h1 {
        font-size: 1.55rem !important;
        line-height: 1.25 !important;
    }

    h2 {
        font-size: 1.28rem !important;
        line-height: 1.3 !important;
    }

    h3 {
        font-size: 1.12rem !important;
        line-height: 1.35 !important;
    }

    [data-testid="stHorizontalBlock"] {
        gap: 0.75rem;
    }

    [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }

    [data-testid="stMetric"] {
        padding: 0.85rem 0.95rem;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.35rem !important;
    }

    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        overflow-x: auto;
        flex-wrap: nowrap;
        padding-bottom: 0.25rem;
    }

    [data-testid="stTabs"] [data-baseweb="tab"] {
        flex: 0 0 auto;
        white-space: nowrap;
        padding: 0.4rem 0.7rem;
    }

    [data-testid="stDataFrame"] {
        overflow-x: auto;
    }

    .js-plotly-plot,
    .plotly,
    [data-testid="stPlotlyChart"] {
        max-width: 100%;
        overflow-x: auto;
    }

    .stButton > button,
    .stDownloadButton > button {
        width: 100%;
        min-height: 2.75rem;
    }

    [data-testid="stSidebar"] {
        border-right: 0;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        font-size: 0.92rem;
    }
}
</style>
"""


def is_mobile_compact_mode() -> bool:
    """Return whether the user enabled the mobile-friendly compact layout."""

    return bool(st.session_state.get(MOBILE_COMPACT_MODE_KEY, False))


def _sync_mobile_compact_mode(widget_key: str) -> None:
    st.session_state[MOBILE_COMPACT_MODE_KEY] = bool(st.session_state.get(widget_key, False))


def _prepare_mobile_compact_widget(widget_key: str) -> None:
    canonical_value = is_mobile_compact_mode()
    if st.session_state.get(widget_key) != canonical_value:
        st.session_state[widget_key] = canonical_value


def render_mobile_compact_toggle(*, placement: str = "sidebar") -> None:
    """Render a shared mobile compact layout toggle."""

    body = "스마트폰에서는 아래 스위치를 켜면 표·차트·AI 분석이 읽기 쉬운 세로형으로 바뀝니다."

    if placement == "inline":
        widget_key = MOBILE_COMPACT_INLINE_TOGGLE_KEY
        callout_modifier = " mobile-compact-callout--inline"
        title = "📱 모바일 화면 설정"
        target = st.container()
    else:
        widget_key = MOBILE_COMPACT_SIDEBAR_TOGGLE_KEY
        callout_modifier = ""
        title = "📱 모바일 화면 설정"
        target = st.sidebar

    _prepare_mobile_compact_widget(widget_key)

    with target:
        st.markdown(
            f"""
            <div class="mobile-compact-callout{callout_modifier}">
                <p class="mobile-compact-callout__title">{title}</p>
                <p class="mobile-compact-callout__body">{body}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.toggle(
            "📱 모바일 간편보기",
            key=widget_key,
            on_change=_sync_mobile_compact_mode,
            args=(widget_key,),
            help=(
                "스마트폰에서 KPI, 탭, 표, AI 분석 영역을 세로형으로 단순화합니다. "
                "PC 기본 화면은 토글을 끄면 그대로 유지됩니다."
            ),
        )
        if is_mobile_compact_mode():
            st.success("모바일 간편보기가 켜져 있습니다.")
        else:
            st.caption("PC 기본 화면은 이 스위치를 끈 상태로 유지됩니다.")


def get_plotly_chart_config() -> dict[str, object]:
    """Return the shared Plotly config for responsive Streamlit charts."""

    config = {"responsive": True}
    if is_mobile_compact_mode():
        config.update(
            {
                "displayModeBar": False,
                "doubleClick": False,
                "scrollZoom": False,
                "staticPlot": True,
            }
        )
    return config


def disable_mobile_plotly_zoom(fig) -> None:
    """Prevent accidental Plotly zoom gestures in mobile compact mode."""

    if not is_mobile_compact_mode():
        return

    fig.update_layout(dragmode=False)
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)


def apply_mobile_plotly_layout(fig, *, height: int = 360, legend_y: float = -0.36) -> None:
    """Make dense Plotly charts easier to scan in mobile compact mode."""

    if not is_mobile_compact_mode():
        return

    disable_mobile_plotly_zoom(fig)

    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=52, b=32),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=legend_y,
            xanchor="left",
            x=0,
            font=dict(size=10),
        ),
        font=dict(size=11),
    )


def apply_app_theme() -> None:
    """Inject the shared dark theme CSS once per page render."""

    st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)
