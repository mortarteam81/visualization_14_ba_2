from __future__ import annotations

import pandas as pd

from utils.config import GYOWON_COL_JAEHAK, GYOWON_COL_JEONGWON
from utils.services.data_service import GyowonDataService


def _make_input_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "기준연도": ["2024", "2024", "2023", "2024"],
            "학교명": ["Alpha University", "Alpha University", "Beta University", "Gamma National"],
            "본분교명": ["본교", "분교", "본교", "본교"],
            "설립유형": ["사립", "사립", "사립", "국립"],
            GYOWON_COL_JEONGWON: ["81.0", "79.5", "82.0", "99.0"],
            GYOWON_COL_JAEHAK: ["84.0", "83.0", "85.0", "99.0"],
        }
    )


class TestServiceContracts:
    def test_prepare_returns_normalized_shape(self) -> None:
        result = GyowonDataService.prepare(_make_input_frame(), bonkyo_only=True)

        assert list(result.columns) == [
            "기준년도",
            "학교명",
            "본분교명",
            GYOWON_COL_JEONGWON,
            GYOWON_COL_JAEHAK,
        ]
        assert result["기준년도"].dtype.kind in {"i", "u"}
        assert result[GYOWON_COL_JEONGWON].dtype.kind == "f"
        assert result[GYOWON_COL_JAEHAK].dtype.kind == "f"

    def test_prepare_filters_to_private_main_campus_by_default(self) -> None:
        result = GyowonDataService.prepare(_make_input_frame())

        assert len(result) == 2
        assert set(result["학교명"]) == {"Alpha University", "Beta University"}
        assert set(result["본분교명"]) == {"본교"}

    def test_prepare_can_expand_branch_names_when_requested(self) -> None:
        result = GyowonDataService.prepare(_make_input_frame(), bonkyo_only=False)

        assert len(result) == 3
        assert "Alpha University (분교)" in set(result["학교명"])
