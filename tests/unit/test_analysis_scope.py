from __future__ import annotations

import pandas as pd

from utils.analysis_scope import (
    annotate_default_analysis_flags,
    apply_default_analysis_scope,
    load_default_analysis_scope,
)


def test_load_default_analysis_scope_contains_34_schools_and_aliases() -> None:
    scope = load_default_analysis_scope()

    assert scope["school_count"] == 34
    assert len(scope["schools"]) == 34
    assert any(group["aliases"] == ["그리스도대학교", "케이씨대학교"] for group in scope["alias_groups"])
    assert any(group["aliases"] == ["한영신학대학교"] for group in scope["alias_groups"])


def test_annotate_default_analysis_flags_prefers_column_filters() -> None:
    frame = pd.DataFrame(
        {
            "학교명": ["연세대학교", "부산대학교", "서울시립대학교", "서울여자간호대학교", "연세대학교", "폐교대학교", "신설대학교"],
            "지역명": ["서울", "부산", "서울", "서울", "서울", "서울", "서울"],
            "설립유형": ["사립", "사립", "공립", "사립", "사립", "사립", "사립"],
            "학교종류": ["대학교", "대학교", "대학교", "전문대학", "대학교", "대학교", "대학교"],
            "본분교명": ["본교", "본교", "본교", "본교", "분교", "본교", "본교"],
            "학교상태": ["기존", "기존", "기존", "기존", "기존", "폐교", "신설"],
        }
    )

    annotated = annotate_default_analysis_flags(frame)

    assert annotated.loc[0, "default_analysis_excluded"] is False
    assert annotated.loc[1, "exclusion_reasons"] == ["not_seoul"]
    assert annotated.loc[2, "exclusion_reasons"] == ["not_private"]
    assert annotated.loc[3, "exclusion_reasons"] == ["not_four_year_university"]
    assert annotated.loc[4, "exclusion_reasons"] == ["branch_campus"]
    assert annotated.loc[5, "exclusion_reasons"] == ["closed"]
    assert annotated.loc[6, "exclusion_reasons"] == ["new_school"]

    included = apply_default_analysis_scope(frame)
    assert included["학교명"].tolist() == ["연세대학교"]


def test_annotate_default_analysis_flags_falls_back_to_names_and_aliases() -> None:
    frame = pd.DataFrame({"학교명": ["그리스도대학교", "케이씨대학교", "한영신학대학교", "서울대학교"]})

    annotated = annotate_default_analysis_flags(frame)

    assert annotated["default_analysis_excluded"].tolist() == [False, False, False, True]
    assert annotated.loc[3, "exclusion_reasons"] == ["not_in_default_scope"]


def test_annotate_default_analysis_flags_does_not_mutate_source_frame() -> None:
    frame = pd.DataFrame({"학교명": ["연세대학교", "서울대학교"]})
    original = frame.copy(deep=True)

    annotated = annotate_default_analysis_flags(frame)

    pd.testing.assert_frame_equal(frame, original)
    assert "default_analysis_excluded" not in frame.columns
    assert "exclusion_reasons" not in frame.columns
    assert "default_analysis_excluded" in annotated.columns


def test_apply_default_analysis_scope_accepts_metric_like_object() -> None:
    class MetricLike:
        id = "sample"

    frame = pd.DataFrame({"학교명": ["연세대학교", "서울대학교"]})

    included = apply_default_analysis_scope(frame, MetricLike())

    assert included["학교명"].tolist() == ["연세대학교"]
