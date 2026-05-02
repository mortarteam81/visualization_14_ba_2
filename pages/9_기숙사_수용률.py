from __future__ import annotations

import streamlit as st

from registry import get_metric
from utils.auth import require_authenticated_user
from utils.config import APP_SUBTITLE
from utils.data_validation_modes import build_dormitory_shadow_status
from utils.dormitory_page import render_dormitory_metric_page
from utils.query import get_dataset
from utils.theme import apply_app_theme


PAGE = get_metric("dormitory_rate")


def main() -> None:
    st.set_page_config(
        page_title=f"{PAGE.title} | 대학알리미 시각화 대시보드",
        page_icon=PAGE.icon,
        layout="wide",
    )
    require_authenticated_user()
    apply_app_theme()
    st.title(f"{PAGE.icon} {PAGE.title}")
    st.caption(APP_SUBTITLE)

    df = get_dataset(PAGE.dataset_key)
    st.session_state[f"{PAGE.id}_shadow_validation"] = build_dormitory_shadow_status().as_dict()
    render_dormitory_metric_page(
        df,
        key_prefix=PAGE.id,
        source_label="기숙사 수용 현황 가공 CSV",
        show_ai_panel=True,
    )


main()
