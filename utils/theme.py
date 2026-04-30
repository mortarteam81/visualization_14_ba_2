"""Global Streamlit theme helpers for the dashboard UI."""

from __future__ import annotations

import streamlit as st


MOBILE_COMPACT_MODE_KEY = "mobile_compact_mode"


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

@media (max-width: 768px) {
    .block-container {
        max-width: 100%;
        padding: 1rem 0.75rem 2rem;
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


def render_mobile_compact_toggle() -> None:
    """Render the shared mobile compact layout toggle in the sidebar."""

    with st.sidebar:
        st.toggle(
            "모바일 간편보기",
            value=False,
            key=MOBILE_COMPACT_MODE_KEY,
            help=(
                "스마트폰에서 KPI, 탭, 표, AI 분석 영역을 세로형으로 단순화합니다. "
                "PC 기본 화면은 토글을 끄면 그대로 유지됩니다."
            ),
        )


def get_plotly_chart_config() -> dict[str, bool]:
    """Return the shared Plotly config for responsive Streamlit charts."""

    config = {"responsive": True}
    if is_mobile_compact_mode():
        config["displayModeBar"] = False
    return config


def apply_mobile_plotly_layout(fig, *, height: int = 360, legend_y: float = -0.36) -> None:
    """Make dense Plotly charts easier to scan in mobile compact mode."""

    if not is_mobile_compact_mode():
        return

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
    render_mobile_compact_toggle()
