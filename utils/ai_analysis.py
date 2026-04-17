from __future__ import annotations

import json
from typing import Any

import pandas as pd

from utils.ai_prompts import build_budam_prompts
from utils.ai_providers import LMStudioClient
from utils.grouping import AVERAGE_LINE_SUFFIX, build_group_average_frame


DEFAULT_ANALYSIS_RESULT = {
    "summary": "",
    "highlights": [],
    "threshold_assessment": "",
    "risks": [],
    "recommended_actions": [],
    "caveats": [],
}


def _to_json_safe(value: Any) -> Any:
    """Convert pandas/numpy scalars and nested containers into JSON-safe primitives."""

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, dict):
        return {str(key): _to_json_safe(item) for key, item in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [_to_json_safe(item) for item in value]

    if hasattr(value, "item"):
        try:
            return _to_json_safe(value.item())
        except Exception:
            pass

    return str(value)


def _recent_points(frame: pd.DataFrame, *, year_col: str, value_col: str, limit: int = 3) -> list[dict[str, float | int]]:
    ordered = frame.sort_values(year_col).tail(limit)
    return [
        {
            "year": int(row[year_col]),
            "value": round(float(row[value_col]), 2),
        }
        for _, row in ordered.iterrows()
    ]


def _trend_label(points: list[dict[str, float | int]]) -> str:
    if len(points) < 2:
        return "판단 유보"

    start = float(points[0]["value"])
    end = float(points[-1]["value"])
    delta = end - start
    if delta >= 1.0:
        return "상승"
    if delta <= -1.0:
        return "하락"
    return "보합"


def build_budam_analysis_payload(
    df: pd.DataFrame,
    *,
    year_col: str,
    school_col: str,
    value_col: str,
    selected_schools: list[str],
    group_definitions: dict[str, list[str]],
    latest_year: int,
    threshold: float,
) -> dict[str, Any]:
    latest_frame = df[df[year_col] == latest_year].copy()
    group_average_frame = build_group_average_frame(
        df,
        year_col=year_col,
        school_col=school_col,
        value_col=value_col,
        groups=group_definitions,
    )
    latest_group_average = group_average_frame[group_average_frame[year_col] == latest_year].copy()

    selected_school_rows: list[dict[str, Any]] = []
    for school in selected_schools:
        school_frame = df[df[school_col] == school].copy()
        if school_frame.empty:
            continue
        latest_school_frame = school_frame[school_frame[year_col] == latest_year]
        if latest_school_frame.empty:
            continue

        latest_value = float(latest_school_frame.iloc[0][value_col])
        recent_points = _recent_points(school_frame, year_col=year_col, value_col=value_col)
        selected_school_rows.append(
            {
                "school": school,
                "latest_value": round(latest_value, 2),
                "threshold_gap": round(latest_value - threshold, 2),
                "meets_threshold": latest_value >= threshold,
                "recent_points": recent_points,
                "trend": _trend_label(recent_points),
            }
        )

    group_rows: list[dict[str, Any]] = []
    for group_name, schools in group_definitions.items():
        active_schools = [school for school in schools if school]
        if not group_name or not active_schools:
            continue

        group_frame = df[df[school_col].isin(active_schools)].copy()
        if group_frame.empty:
            continue

        average_label = f"{group_name} {AVERAGE_LINE_SUFFIX}"
        average_frame = group_average_frame[group_average_frame[school_col] == average_label].copy()
        latest_average_frame = latest_group_average[latest_group_average[school_col] == average_label]
        latest_average = float(latest_average_frame.iloc[0][value_col]) if not latest_average_frame.empty else None

        member_latest = latest_frame[latest_frame[school_col].isin(active_schools)].copy()
        member_latest_sorted = member_latest.sort_values(value_col, ascending=False)

        comparisons: list[dict[str, Any]] = []
        for school_row in selected_school_rows:
            if latest_average is None:
                continue
            comparisons.append(
                {
                    "school": school_row["school"],
                    "gap_vs_group_average": round(float(school_row["latest_value"]) - latest_average, 2),
                }
            )

        recent_average_points = _recent_points(average_frame, year_col=year_col, value_col=value_col)
        group_rows.append(
            {
                "group_name": group_name,
                "school_count": len(active_schools),
                "schools": active_schools,
                "latest_average": round(latest_average, 2) if latest_average is not None else None,
                "threshold_gap": round(latest_average - threshold, 2) if latest_average is not None else None,
                "recent_average_points": recent_average_points,
                "average_trend": _trend_label(recent_average_points),
                "highest_school_latest": (
                    {
                        "school": str(member_latest_sorted.iloc[0][school_col]),
                        "value": round(float(member_latest_sorted.iloc[0][value_col]), 2),
                    }
                    if not member_latest_sorted.empty
                    else None
                ),
                "lowest_school_latest": (
                    {
                        "school": str(member_latest_sorted.iloc[-1][school_col]),
                        "value": round(float(member_latest_sorted.iloc[-1][value_col]), 2),
                    }
                    if not member_latest_sorted.empty
                    else None
                ),
                "comparisons_to_selected": comparisons,
            }
        )

    payload = {
        "metric": "법정부담금 부담율",
        "latest_year": latest_year,
        "unit": "%",
        "threshold": threshold,
        "selected_school_count": len(selected_school_rows),
        "active_group_count": len(group_rows),
        "selected_schools": selected_school_rows,
        "groups": group_rows,
    }
    return _to_json_safe(payload)


def _extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:].strip()

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("JSON 객체를 찾지 못했습니다.")

    return json.loads(stripped[start:end + 1])


def normalize_analysis_result(text: str) -> dict[str, Any]:
    try:
        parsed = _extract_json_object(text)
    except Exception:
        parsed = {"summary": text.strip()}

    result = DEFAULT_ANALYSIS_RESULT | parsed
    for key in ("highlights", "risks", "recommended_actions", "caveats"):
        value = result.get(key)
        if isinstance(value, list):
            result[key] = [str(item) for item in value if str(item).strip()]
        elif isinstance(value, str) and value.strip():
            result[key] = [value.strip()]
        else:
            result[key] = []

    for key in ("summary", "threshold_assessment"):
        result[key] = str(result.get(key, "")).strip()

    return result


def analyze_budam_with_lmstudio(
    payload: dict[str, Any],
    *,
    tone: str,
    focus: str,
    client: LMStudioClient | None = None,
) -> dict[str, Any]:
    lm_client = client or LMStudioClient()
    system_prompt, user_prompt = build_budam_prompts(payload, tone=tone, focus=focus)
    response_text = lm_client.chat_completion(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )
    return normalize_analysis_result(response_text)
