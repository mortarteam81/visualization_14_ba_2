from __future__ import annotations

import pandas as pd

from utils.school_normalization import (
    canonicalize_school_name,
    canonicalize_school_name_column,
    normalize_school_code,
    resolve_school_name,
)


def test_resolve_school_name_handles_exact_aliases_and_main_campus_suffixes() -> None:
    assert resolve_school_name("성신여자대학교") == "성신여자대학교"
    assert resolve_school_name("성신여자대학교 본교") == "성신여자대학교"
    assert resolve_school_name("케이씨대학교") == "강서대학교"
    assert resolve_school_name("강서대학교(구.케이씨대학교)") == "강서대학교"
    assert resolve_school_name("한영신학대학교") == "서울한영대학교"
    assert resolve_school_name("서울한영대학교(구.한영신학대학교)") == "서울한영대학교"


def test_resolve_school_name_does_not_merge_branch_campuses() -> None:
    assert resolve_school_name("건국대학교(글로컬)") is None
    assert resolve_school_name("고려대학교 세종캠퍼스") is None
    assert resolve_school_name("동국대학교(WISE)") is None
    assert resolve_school_name("연세대학교(미래)") is None
    assert resolve_school_name("한양대학교(ERICA)") is None


def test_canonicalize_school_name_can_preserve_unknown_names() -> None:
    assert canonicalize_school_name("테스트대학교") == "테스트대학교"
    assert canonicalize_school_name("테스트대학교", default_to_original=False) is None


def test_canonicalize_school_name_column_can_restrict_to_default_scope() -> None:
    frame = pd.DataFrame({"학교명": ["성신여자대학교 본교", "케이씨대학교", "서울대학교"]})

    result = canonicalize_school_name_column(frame, restrict_to_default_scope=True)

    assert result["학교명"].tolist() == ["성신여자대학교", "강서대학교"]
    assert frame["학교명"].tolist() == ["성신여자대학교 본교", "케이씨대학교", "서울대학교"]


def test_normalize_school_code_zero_pads_numeric_values() -> None:
    assert normalize_school_code(136) == "0000136"
    assert normalize_school_code("136.0") == "0000136"
    assert normalize_school_code("0000205") == "0000205"
    assert normalize_school_code("") == ""
