"""Streamlit home page rendered from the typed metric registry."""

import streamlit as st

from registry import APP_METADATA, list_metrics
from utils.config import APP_ICON, APP_SUBTITLE, APP_TITLE, DATA_UPDATED
from utils.theme import apply_app_theme

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
)
apply_app_theme()

st.title(f"{APP_ICON} {APP_TITLE}")
st.caption(APP_SUBTITLE)
st.markdown(APP_METADATA["catalog_intro"])
st.divider()

st.markdown(f"#### {APP_METADATA['catalog_heading']}")

metrics = list_metrics()
for index in range(0, len(metrics), 2):
    columns = st.columns(2)
    for column, metric in zip(columns, metrics[index:index + 2]):
        with column:
            st.info(
                f"**{metric.icon} {metric.title}**\n\n"
                f"{metric.summary}\n\n"
                f"{metric.threshold_note}"
            )
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
