from __future__ import annotations

from utils.data_pipeline import (
    load_faculty_securing_reference_frame,
    load_library_material_purchase_frame,
    load_library_staff_frame,
)
from utils.analysis_scope import apply_default_analysis_scope


DEFAULT_SCOPE_COUNT = 34
RINFO_EXTRA_SCHOOLS = {
    "고려사이버대학교",
    "디지털서울문화예술대학교",
    "명지대학교",
    "서울디지털대학교",
    "서울사이버대학교",
    "숭실사이버대학교",
    "태재대학교",
    "한국열린사이버대학교",
}


def test_rinfo_library_staff_loader_uses_default_scope_school_names() -> None:
    frame = load_library_staff_frame()
    schools = set(frame["학교명"].dropna().unique())

    assert len(schools) <= DEFAULT_SCOPE_COUNT
    assert not (schools & RINFO_EXTRA_SCHOOLS)
    assert "성신여자대학교" in schools


def test_rinfo_material_purchase_loader_uses_default_scope_school_names() -> None:
    frame = load_library_material_purchase_frame()
    schools = set(frame["학교명"].dropna().unique())

    assert len(schools) <= DEFAULT_SCOPE_COUNT
    assert not (schools & RINFO_EXTRA_SCHOOLS)
    assert "성신여자대학교" in schools


def test_faculty_reference_loader_canonicalizes_2015_main_campus_suffixes() -> None:
    frame = load_faculty_securing_reference_frame()
    rows_2015 = frame[frame["기준년도"] == 2015]
    scoped = apply_default_analysis_scope(frame)
    scoped_rows_2015 = scoped[scoped["기준년도"] == 2015]

    assert not rows_2015.empty
    assert not scoped_rows_2015.empty
    assert "성신여자대학교" in set(rows_2015["학교명"])
    assert "성신여자대학교" in set(scoped_rows_2015["학교명"])
    assert "성신여자대학교 본교" not in set(rows_2015["학교명"])
