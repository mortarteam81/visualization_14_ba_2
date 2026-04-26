"""Streamlit home page rendered from the typed metric registry."""

import streamlit as st

from registry import APP_METADATA, list_metrics
from utils.auth import require_authenticated_user
from utils.config import APP_ICON, APP_SUBTITLE, APP_TITLE, DATA_UPDATED
from utils.theme import apply_app_theme

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
)
require_authenticated_user()
apply_app_theme()

st.title(f"{APP_ICON} {APP_TITLE}")
st.caption(APP_SUBTITLE)
st.markdown(APP_METADATA["catalog_intro"])
st.divider()

st.markdown(f"#### {APP_METADATA['catalog_heading']}")

metrics = list_metrics()
implemented_count = sum(1 for m in metrics if m.implemented)
not_implemented_count = len(metrics) - implemented_count

st.markdown(
    f"<p style='margin-bottom:1rem;'>"
    f"<span style='color:#F59E0B;font-weight:700;'>● 구현 완료 ({implemented_count}개)</span>"
    f"&nbsp;&nbsp;&nbsp;"
    f"<span style='color:#F8FBFF;font-weight:700;'>○ 준비 중 ({not_implemented_count}개)</span>"
    f"</p>",
    unsafe_allow_html=True,
)

for index in range(0, len(metrics), 2):
    columns = st.columns(2)
    for column, metric in zip(columns, metrics[index:index + 2]):
        with column:
            if metric.implemented:
                title_color = "#F59E0B"
                summary_color = "#dde6f3"
                border_color = "rgba(245,158,11,0.35)"
                badge = ""
            else:
                title_color = "#F8FBFF"
                summary_color = "#b7c4d8"
                border_color = "rgba(148,163,184,0.18)"
                badge = (
                    "&nbsp;<span style='font-size:0.7em;padding:2px 8px;"
                    "background:rgba(148,163,184,0.18);border-radius:8px;"
                    "color:#b7c4d8;'>준비 중</span>"
                )

            threshold_html = ""
            if metric.threshold_note:
                threshold_html = (
                    f"<p style='margin:0.4rem 0 0;font-size:0.82em;"
                    f"color:#b7c4d8;'>{metric.threshold_note}</p>"
                )

            st.markdown(
                f"<div style='padding:1rem 1.1rem;border-radius:8px;"
                f"border:1px solid {border_color};"
                f"background:rgba(18,24,33,0.94);"
                f"box-shadow:0 12px 28px rgba(0,0,0,0.28);"
                f"margin-bottom:0.5rem;'>"
                f"<p style='margin:0;font-weight:700;color:{title_color};'>"
                f"{metric.icon} {metric.title}{badge}</p>"
                f"<p style='margin:0.4rem 0 0;color:{summary_color};'>"
                f"{metric.summary}</p>"
                f"{threshold_html}"
                f"</div>",
                unsafe_allow_html=True,
            )

            if metric.implemented and metric.page_path:
                st.page_link(
                    metric.page_path,
                    label=f"{metric.title} 열기",
                    icon="📈",
                )

st.divider()
st.markdown(
    f"📅 데이터 기준일: **{DATA_UPDATED}** | "
    f"출처: [{APP_METADATA['source_name']}]({APP_METADATA['source_url']}) | "
    "대상: 서울 소재 사립 4년제 대학교"
)
