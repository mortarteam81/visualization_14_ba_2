from __future__ import annotations

import pandas as pd

from utils.config import LECTURER_PAY_COL
from utils.data_pipeline import prepare_lecturer_pay_frame


def test_prepare_lecturer_pay_frame_filters_and_weights_by_hours() -> None:
    raw = pd.DataFrame(
        {
            "reference_year": [2025, 2025, 2025, 2025],
            "university_name": ["성신여자대학교", "성신여자대학교", "서울대학교", "가천대학교"],
            "school_type": ["대학교", "대학교", "대학교", "대학교"],
            "founding_type": ["사립", "사립", "국립", "사립"],
            "region_name": ["서울", "서울", "서울", "경기"],
            "school_status": ["기존", "기존", "기존", "기존"],
            "lecturer_category": ["강사", "강사", "강사", "강사"],
            "payment_category": ["주간", "야간", "주간", "주간"],
            "paid_lecturer_count": [10, 5, 8, 7],
            "시간당 지급기준 단가(원)": ["50,000", "60,000", "70,000", "80,000"],
            "총 강의시간 수": ["100", "300", "200", "100"],
            "지급인원비율(%)": [50.0, 50.0, 100.0, 100.0],
        }
    )

    result = prepare_lecturer_pay_frame(raw)

    assert result["학교명"].tolist() == ["성신여자대학교"]
    assert result["기준년도"].tolist() == [2025]
    assert result[LECTURER_PAY_COL].tolist() == [57_500.0]
    assert result["연도별기준값"].tolist() == [53_100.0]
    assert result["기준충족"].tolist() == [True]
