from __future__ import annotations

import pandas as pd

from utils.config import LIBRARY_MATERIAL_PURCHASE_COL
from utils.data_pipeline import prepare_library_material_purchase_frame


def test_prepare_library_material_purchase_frame_filters_seoul_private_universities() -> None:
    raw = pd.DataFrame(
        {
            "reference_year": [2025, 2025, 2025, 2025],
            "row_no": [1, 2, 3, 4],
            "university_name": ["성신여자대학교", "서울대학교", "가천대학교", "서울전문대학"],
            "school_type": ["대학", "대학", "대학", "전문대학"],
            "founding_type": ["사립", "국립", "사립", "사립"],
            "region_name": ["서울", "서울", "경기", "서울"],
            "size_group": ["B그룹", "A그룹", "A그룹", "C그룹"],
            "university_total_settlement": [1_000_000, 1_000_000, 1_000_000, 1_000_000],
            "books_purchase_expense": [100_000, 100_000, 100_000, 100_000],
            "serials_purchase_expense": [0, 0, 0, 0],
            "non_book_purchase_expense": [0, 0, 0, 0],
            "electronic_resources_total": [0, 0, 0, 0],
            "electronic_journals_expense": [0, 0, 0, 0],
            "web_db_expense": [0, 0, 0, 0],
            "subscribed_ebook_expense": [0, 0, 0, 0],
            "other_electronic_resources_expense": [0, 0, 0, 0],
            "total_material_purchase_expense": [60_000_000, 70_000_000, 80_000_000, 90_000_000],
            "enrolled_students_current_year": [1_000, 1_000, 1_000, 1_000],
            "material_purchase_expense_per_student": ["60,000", "70,000", "80,000", "90,000"],
            "source_file_name": ["source.xls"] * 4,
        }
    )

    result = prepare_library_material_purchase_frame(raw)

    assert result["학교명"].tolist() == ["성신여자대학교"]
    assert result["기준년도"].tolist() == [2025]
    assert result[LIBRARY_MATERIAL_PURCHASE_COL].tolist() == [60_000.0]
    assert result["기준충족"].tolist() == [True]
