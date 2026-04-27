from __future__ import annotations

from registry.pending_source_acquisition import FIRST_WAVE_SOURCE_ACQUISITION


FIRST_WAVE_METRICS = {
    "student_recruitment",
    "corp_transfer_ratio",
}


def test_first_wave_source_acquisition_covers_priority_metrics() -> None:
    covered = {spec.metric_id for spec in FIRST_WAVE_SOURCE_ACQUISITION}

    assert covered == FIRST_WAVE_METRICS


def test_first_wave_metrics_have_raw_first_source() -> None:
    raw_first = {
        spec.metric_id for spec in FIRST_WAVE_SOURCE_ACQUISITION if spec.purpose == "raw-first"
    }

    assert raw_first == FIRST_WAVE_METRICS


def test_api_refresh_sources_are_marked_with_service_key_when_needed() -> None:
    api_specs = [spec for spec in FIRST_WAVE_SOURCE_ACQUISITION if spec.kind == "api"]

    assert api_specs
    assert all(spec.auth == "service-key" for spec in api_specs)


def test_source_specs_include_verification_details() -> None:
    for spec in FIRST_WAVE_SOURCE_ACQUISITION:
        assert spec.source_name
        assert spec.url.startswith("https://")
        assert spec.format
        assert spec.verified_fields


def test_kasfo_corp_transfer_download_needs_manual_confirmation() -> None:
    [spec] = [
        item
        for item in FIRST_WAVE_SOURCE_ACQUISITION
        if item.metric_id == "corp_transfer_ratio"
    ]

    assert spec.kind == "web-indicator"
    assert spec.auth == "web-session-unknown"
    assert any("다운로드" in caveat for caveat in spec.caveats)
