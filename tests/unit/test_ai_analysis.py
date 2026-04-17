from __future__ import annotations

import pandas as pd

from utils.ai_analysis import build_budam_analysis_payload, normalize_analysis_result


def test_build_budam_analysis_payload_summarizes_selected_school_and_group() -> None:
    frame = pd.DataFrame(
        {
            "기준년도": [2022, 2023, 2024, 2022, 2023, 2024],
            "학교명": ["성신여자대학교", "성신여자대학교", "성신여자대학교", "A대", "A대", "A대"],
            "부담율": [8.0, 9.0, 11.0, 10.0, 10.5, 12.0],
        }
    )

    payload = build_budam_analysis_payload(
        frame,
        year_col="기준년도",
        school_col="학교명",
        value_col="부담율",
        selected_schools=["성신여자대학교"],
        group_definitions={"서울 소재 여대": ["성신여자대학교", "A대"]},
        latest_year=2024,
        threshold=10.0,
    )

    assert payload["metric"] == "법정부담금 부담율"
    assert payload["selected_schools"][0]["school"] == "성신여자대학교"
    assert payload["selected_schools"][0]["latest_value"] == 11.0
    assert payload["groups"][0]["group_name"] == "서울 소재 여대"
    assert payload["groups"][0]["latest_average"] == 11.5


def test_normalize_analysis_result_parses_json_block() -> None:
    result = normalize_analysis_result(
        """
```json
{
  "summary": "요약입니다.",
  "highlights": ["포인트 1"],
  "threshold_assessment": "기준선 충족",
  "risks": ["주의점"],
  "recommended_actions": ["권고안"],
  "caveats": ["유의사항"]
}
```
""".strip()
    )

    assert result["summary"] == "요약입니다."
    assert result["highlights"] == ["포인트 1"]
    assert result["threshold_assessment"] == "기준선 충족"


def test_normalize_analysis_result_falls_back_to_plain_text() -> None:
    result = normalize_analysis_result("단순 텍스트 응답")

    assert result["summary"] == "단순 텍스트 응답"
    assert result["highlights"] == []
