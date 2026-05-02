import pandas as pd

from scripts.converters.kasfo_common import normalize_code, parse_amount, standardize_frame


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
