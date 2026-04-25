"""Fetch AcademyInfo key-indicator raw data and derive first-wave CSV candidates.

This uses the public AcademyInfo page endpoint behind "대학주요정보 한눈에 보기".
It does not require a data.go.kr ServiceKey because it fetches the web table data
used by the public page, not the OpenAPI update endpoint.

Outputs by default:
- data/raw/academyinfo/university_key_indicators/<year>/academyinfo_key_indicators_<year>.json
- data/raw/academyinfo/university_key_indicators/<year>/academyinfo_key_indicators_<year>.csv
- data/processed/student_recruitment/student_recruitment_<year>_candidate.csv

The student recruitment processed CSV is a candidate dataset.  It includes the
available direct 신입생 충원율 field from the key-indicator page.  재학생 충원율
is not available from this endpoint and must be sourced from the StudentService
OpenAPI or a richer student-status raw file before the metric is marked
implemented.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ACADEMYINFO_PAGE_URL = "https://www.academyinfo.go.kr/main/main2130/doInit.do"
ACADEMYINFO_DATA_URL = "https://www.academyinfo.go.kr/main/main2130/selectSchlList.do"

RAW_COLUMN_MAP: dict[str, str] = {
    "svy_yr": "공시연도",
    "rep_schl_id": "대표학교코드",
    "schl_id": "학교코드",
    "lst_kor_schl_nm": "학교명",
    "psbs_div_nm": "본분교명",
    "schl_div_nm": "대학구분",
    "schl_knd_nm": "학교종류",
    "schl_estb_div_nm": "설립유형",
    "pbnf_area_nm": "지역명",
    "schl_stat_nm": "학교상태",
    "fm_el_gn_ct": "입학정원(학부)",
    "fm_el_gn_ct_year": "입학정원(학부)_기준년도",
    "et_st_ct": "재학생수(학부)",
    "et_st_ct_year": "재학생수(학부)_기준년도",
    "gn_mn_ct": "졸업생수(학부)",
    "gn_mn_ct_year": "졸업생수(학부)_기준년도",
    "fr_fm_tr_sn_ct": "전임교원수(학부+대학원)",
    "fr_fm_tr_sn_ct_year": "전임교원수(학부+대학원)_기준년도",
    "gn_ie_fm_cn_re": "신입생경쟁률(학부)",
    "gn_ie_fm_cn_re_year": "신입생경쟁률(학부)_기준년도",
    "gn_ie_fm_rt_re": "신입생충원율(학부)",
    "gn_ie_fm_rt_re_year": "신입생충원율(학부)_기준년도",
    "st_1_ps_py_sp": "학생1인당연간장학금(학부)",
    "st_1_ps_py_sp_year": "학생1인당연간장학금(학부)_기준년도",
    "ae_tn": "평균등록금(학부)",
    "ae_tn_year": "평균등록금(학부)_기준년도",
    "st_1_ps_py_et": "학생1인당교육비",
    "st_1_ps_py_et_year": "학생1인당교육비_기준년도",
    "be_ae_re": "기숙사수용률",
    "be_ae_re_year": "기숙사수용률_기준년도",
    "st_1_ps_py_bk_ct": "학생1인당도서자료수",
    "st_1_ps_py_bk_ct_year": "학생1인당도서자료수_기준년도",
}

STUDENT_RECRUITMENT_COLUMNS: tuple[str, ...] = (
    "공시연도",
    "대표학교코드",
    "학교코드",
    "학교명",
    "본분교명",
    "대학구분",
    "학교종류",
    "설립유형",
    "지역명",
    "학교상태",
    "입학정원(학부)",
    "재학생수(학부)",
    "신입생경쟁률(학부)",
    "신입생충원율(학부)",
    "신입생충원율(학부)_기준년도",
)


def fetch_key_indicator_records(year: int) -> list[dict[str, Any]]:
    session = requests.Session()
    session.get(ACADEMYINFO_PAGE_URL, timeout=30)
    response = session.post(
        ACADEMYINFO_DATA_URL,
        data={
            "svyYr": str(year),
            "schKndCdArr": "",
            "schEstbDivCdArr": "",
            "schZnCdArr": "",
            "schZnCdArr1": "",
            "numStu": "",
        },
        headers={
            "Referer": ACADEMYINFO_PAGE_URL,
            "X-Requested-With": "XMLHttpRequest",
        },
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    records = payload.get("resultList", [])
    if not isinstance(records, list):
        raise ValueError("AcademyInfo response did not contain a resultList array")
    return records


def normalize_key_indicator_frame(records: list[dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(records)
    return frame.rename(columns=RAW_COLUMN_MAP)


def write_raw_outputs(frame: pd.DataFrame, records: list[dict[str, Any]], year: int) -> tuple[Path, Path]:
    raw_dir = PROJECT_ROOT / "data" / "raw" / "academyinfo" / "university_key_indicators" / str(year)
    raw_dir.mkdir(parents=True, exist_ok=True)
    json_path = raw_dir / f"academyinfo_key_indicators_{year}.json"
    csv_path = raw_dir / f"academyinfo_key_indicators_{year}.csv"

    json_path.write_text(
        json.dumps(
            {
                "source_url": ACADEMYINFO_DATA_URL,
                "page_url": ACADEMYINFO_PAGE_URL,
                "year": year,
                "record_count": len(records),
                "records": records,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    frame.to_csv(csv_path, index=False, encoding="utf-8-sig")
    return json_path, csv_path


def write_student_recruitment_candidate(frame: pd.DataFrame, year: int) -> Path:
    processed_dir = PROJECT_ROOT / "data" / "processed" / "student_recruitment"
    processed_dir.mkdir(parents=True, exist_ok=True)
    output_path = processed_dir / f"student_recruitment_{year}_candidate.csv"

    available_columns = [column for column in STUDENT_RECRUITMENT_COLUMNS if column in frame.columns]
    candidate = frame.loc[:, available_columns].copy()
    candidate["재학생충원율"] = pd.NA
    candidate["재학생충원율_확보상태"] = "대학주요정보 엔드포인트 미제공: StudentService API 또는 학생 현황 원자료 필요"
    candidate["raw_source_url"] = ACADEMYINFO_DATA_URL
    candidate.to_csv(output_path, index=False, encoding="utf-8-sig")
    return output_path


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=2026, help="공시연도")
    parser.add_argument(
        "--skip-fetch",
        action="store_true",
        help="Do not fetch; reserved for future offline fixture support.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.skip_fetch:
        raise SystemExit("--skip-fetch is not implemented yet")

    records = fetch_key_indicator_records(args.year)
    frame = normalize_key_indicator_frame(records)
    json_path, raw_csv_path = write_raw_outputs(frame, records, args.year)
    candidate_path = write_student_recruitment_candidate(frame, args.year)

    print(
        json.dumps(
            {
                "year": args.year,
                "records": len(records),
                "raw_json": str(json_path.relative_to(PROJECT_ROOT)),
                "raw_csv": str(raw_csv_path.relative_to(PROJECT_ROOT)),
                "student_recruitment_candidate": str(candidate_path.relative_to(PROJECT_ROOT)),
                "staff_per_student_status": "직원총계 컬럼이 이 엔드포인트에서 확인되지 않아 추가 직원 현황 원자료 필요",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
