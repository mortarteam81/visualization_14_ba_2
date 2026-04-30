from __future__ import annotations

from registry import get_metric
from utils.source_display import format_source_caption


def test_format_source_caption_for_kcue_processed_manifest() -> None:
    caption = format_source_caption(
        {
            "source_label": "한국대학평가원 대학현황지표",
            "source_data_scope": {"label": "평가용 2차 집계자료/가공 CSV"},
            "validation_status": {"label": "가공 검증 완료"},
            "updated_at": "2026-04-27",
        }
    )

    assert caption == (
        "데이터 출처: 한국대학평가원 대학현황지표"
        " | 자료 범위: 평가용 2차 집계자료/가공 CSV"
        " | 검증 상태: 가공 검증 완료"
        " | 업데이트: 2026-04-27"
    )


def test_format_source_caption_for_faculty_processed_metric() -> None:
    caption = format_source_caption(get_metric("adjunct_faculty"))

    assert "데이터 출처: 한국대학평가원 대학통계" in caption
    assert "자료 범위: 평가용 2차 집계자료/가공 CSV" in caption
    assert "검증 상태: 부분 검증" in caption


def test_format_source_caption_for_legacy_metric() -> None:
    caption = format_source_caption(get_metric("budam"))

    assert "데이터 출처: 대학알리미" in caption
    assert "자료 범위: 서울 subset legacy CSV" in caption
    assert "검증 상태: 기존 자료/스키마 보강 필요" in caption
