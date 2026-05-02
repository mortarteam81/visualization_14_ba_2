import pandas as pd

from scripts.converters.kasfo_common import normalize_code, parse_amount, standardize_frame
from scripts.converters.kasfo_gyeolsan import build_candidate


def test_parse_amount_kasfo_rules():
    assert parse_amount(" 1,234 ") == 1234.0
    assert parse_amount("-") is None
    assert parse_amount(" -123,456 ") == -123456.0
    assert parse_amount("(1,234)") == -1234.0
    assert parse_amount(0) == 0.0


def test_normalize_school_code_preserves_seven_digits():
    assert normalize_code("50") == "0000050"
    assert normalize_code("0000136") == "0000136"
    assert normalize_code("136.0") == "0000136"


def test_standardize_frame_amount_and_code_columns():
    frame = pd.DataFrame(
        {
            "학교코드": ["50"],
            "학교명": [" 감리교신학대학교 "],
            "1.자금수입총계[1135]": ["1,000"],
            "2.미사용전기이월자금[1127]": ["-500"],
            "memo": ["leave"],
        }
    )
    out = standardize_frame(frame)
    assert out.loc[0, "학교코드"] == "0000050"
    assert out.loc[0, "학교명"] == "감리교신학대학교"
    assert out.loc[0, "1.자금수입총계[1135]"] == 1000.0
    assert out.loc[0, "2.미사용전기이월자금[1127]"] == -500.0
    assert out.loc[0, "memo"] == "leave"


def test_kasfo_gyeolsan_candidate_uses_private_school_account_formula():
    raw = pd.DataFrame(
        [
            {
                "학교명": "성신여자대학교",
                "법인명": "성신학원",
                "설립": "사립",
                "학급": "대학",
                "학종": "일반",
                "지역": "서울",
                "회계": "교비",
                "회계연도": "2024년",
                "2.운영수입[1086]": "1,000",
                "4.등록금수입[1002]": "600",
                "4.기부금수입[1035]": "20",
                "source_file_name": "sample.xlsx",
                "source_sheet_name": "자금계산서",
            },
            {
                "학교명": "성신여자대학교",
                "법인명": "성신학원",
                "설립": "사립",
                "학급": "대학",
                "학종": "일반",
                "지역": "서울",
                "회계": "법인",
                "회계연도": "2024년",
                "2.운영수입[1086]": "10,000",
                "4.등록금수입[1002]": "9,000",
                "4.기부금수입[1035]": "500",
                "source_file_name": "sample.xlsx",
                "source_sheet_name": "자금계산서",
            },
        ]
    )

    candidate = build_candidate(raw)

    assert len(candidate) == 1
    row = candidate.iloc[0]
    assert row["회계"] == "교비"
    assert row["운영수입"] == 1000.0
    assert row["등록금비율"] == 60.0
    assert row["기부금비율"] == 2.0
