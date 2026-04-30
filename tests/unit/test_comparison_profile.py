from __future__ import annotations

from utils.comparison_profile import (
    ComparisonGroup,
    ComparisonProfile,
    DEFAULT_OWNER_ID,
    DEFAULT_OWNER_TYPE,
    DEFAULT_PROFILE_ID,
    DEFAULT_PROFILE_NAME,
    FileComparisonProfileStore,
    MAX_COMPARISON_GROUPS,
    MAX_COMPARISON_SCHOOLS,
    comparison_group_definitions,
    comparison_profile_signature,
    default_comparison_profile,
    default_selected_schools,
    normalize_comparison_profile,
    selected_schools_from_profile,
)


SCHOOLS = [
    "성신여자대학교",
    "숙명여자대학교",
    "덕성여자대학교",
    "서울여자대학교",
    "동덕여자대학교",
    "이화여자대학교",
    "국민대학교",
]


def _profile(
    base_school: str,
    comparison_schools: tuple[str, ...],
    comparison_groups: tuple[ComparisonGroup, ...] = (),
) -> ComparisonProfile:
    return ComparisonProfile(
        profile_id=DEFAULT_PROFILE_ID,
        profile_name=DEFAULT_PROFILE_NAME,
        owner_type=DEFAULT_OWNER_TYPE,
        owner_id=DEFAULT_OWNER_ID,
        base_school=base_school,
        comparison_schools=comparison_schools,
        comparison_groups=comparison_groups,
        is_default=True,
        updated_at="",
    )


def test_default_profile_uses_base_and_three_comparison_schools() -> None:
    profile = default_comparison_profile(SCHOOLS)

    assert profile.base_school == "성신여자대학교"
    assert profile.comparison_schools == ("숙명여자대학교", "덕성여자대학교", "서울여자대학교")
    assert profile.comparison_groups == ()


def test_normalize_profile_removes_duplicate_base_and_limits_comparison_schools() -> None:
    profile = _profile(
        "성신여자대학교",
        (
            "숙명여자대학교",
            "성신여자대학교",
            "숙명여자대학교",
            "덕성여자대학교",
            "서울여자대학교",
            "동덕여자대학교",
            "이화여자대학교",
            "국민대학교",
        ),
    )

    normalized = normalize_comparison_profile(profile, SCHOOLS)

    assert normalized.base_school == "성신여자대학교"
    assert normalized.comparison_schools == (
        "숙명여자대학교",
        "덕성여자대학교",
        "서울여자대학교",
        "동덕여자대학교",
        "이화여자대학교",
    )
    assert len(normalized.comparison_schools) == MAX_COMPARISON_SCHOOLS


def test_normalize_profile_falls_back_to_available_base_school() -> None:
    profile = _profile("없는대학교", ("숙명여자대학교",))

    normalized = normalize_comparison_profile(profile, SCHOOLS)

    assert normalized.base_school == "성신여자대학교"
    assert normalized.comparison_schools == ("숙명여자대학교",)


def test_file_store_saves_and_loads_profile(tmp_path) -> None:
    store = FileComparisonProfileStore(tmp_path / "comparison_profile.local.json")
    profile = _profile(
        "성신여자대학교",
        ("숙명여자대학교", "덕성여자대학교"),
        (
            ComparisonGroup("여대 비교군", ("성신여자대학교", "숙명여자대학교")),
        ),
    )

    saved = store.save(profile, SCHOOLS)
    loaded = store.load(SCHOOLS)

    assert saved.updated_at
    assert loaded.base_school == "성신여자대학교"
    assert loaded.comparison_schools == ("숙명여자대학교", "덕성여자대학교")
    assert loaded.comparison_groups == (
        ComparisonGroup("여대 비교군", ("성신여자대학교", "숙명여자대학교")),
    )


def test_default_selected_schools_uses_profile_before_fallback(tmp_path) -> None:
    store = FileComparisonProfileStore(tmp_path / "comparison_profile.local.json")
    store.save(_profile("성신여자대학교", ("숙명여자대학교", "덕성여자대학교")), SCHOOLS)

    selected = default_selected_schools(SCHOOLS, fallback=["국민대학교"], store=store)

    assert selected == ["성신여자대학교", "숙명여자대학교", "덕성여자대학교"]


def test_selected_schools_from_profile_returns_base_then_comparisons() -> None:
    profile = _profile("성신여자대학교", ("숙명여자대학교", "덕성여자대학교"))

    selected = selected_schools_from_profile(profile, SCHOOLS)

    assert selected == ["성신여자대학교", "숙명여자대학교", "덕성여자대학교"]


def test_comparison_profile_signature_changes_when_defaults_change() -> None:
    profile = _profile("성신여자대학교", ("숙명여자대학교",))
    changed_comparisons = _profile("성신여자대학교", ("덕성여자대학교",))
    changed_groups = _profile(
        "성신여자대학교",
        ("숙명여자대학교",),
        (ComparisonGroup("여대 비교군", ("성신여자대학교", "숙명여자대학교")),),
    )

    assert comparison_profile_signature(profile) != comparison_profile_signature(changed_comparisons)
    assert comparison_profile_signature(profile) != comparison_profile_signature(changed_groups)


def test_normalize_profile_limits_comparison_groups_and_filters_schools() -> None:
    profile = _profile(
        "성신여자대학교",
        ("숙명여자대학교",),
        (
            ComparisonGroup("그룹1", ("성신여자대학교", "없는대학교")),
            ComparisonGroup("그룹2", ("덕성여자대학교",)),
            ComparisonGroup("그룹3", ()),
            ComparisonGroup("그룹4", ("서울여자대학교",)),
            ComparisonGroup("그룹5", ("동덕여자대학교",)),
        ),
    )

    normalized = normalize_comparison_profile(profile, SCHOOLS)

    assert normalized.comparison_groups == (
        ComparisonGroup("그룹1", ("성신여자대학교",)),
        ComparisonGroup("그룹2", ("덕성여자대학교",)),
        ComparisonGroup("그룹4", ("서울여자대학교",)),
    )
    assert len(normalized.comparison_groups) == MAX_COMPARISON_GROUPS


def test_comparison_group_definitions_returns_saved_groups(tmp_path) -> None:
    store = FileComparisonProfileStore(tmp_path / "comparison_profile.local.json")
    store.save(
        _profile(
            "성신여자대학교",
            ("숙명여자대학교",),
            (
                ComparisonGroup("여대 비교군", ("성신여자대학교", "숙명여자대학교")),
                ComparisonGroup("규모 비교군", ("국민대학교",)),
            ),
        ),
        SCHOOLS,
    )

    groups = comparison_group_definitions(SCHOOLS, store=store)

    assert groups == {
        "여대 비교군": ["성신여자대학교", "숙명여자대학교"],
        "규모 비교군": ["국민대학교"],
    }
