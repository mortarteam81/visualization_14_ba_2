"""Download KASFO theme/issue statistics Excel files.

The KASFO theme issue pages expose the same file as the "엑셀파일 저장" button
through ``/statistics/themeIssue/excelDownLoad/{issue_id}``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://uniarlimi.kasfo.or.kr"


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _parse_years(values: list[str]) -> list[int]:
    years: list[int] = []
    for value in values:
        if "-" in value:
            start, end = value.split("-", 1)
            years.extend(range(int(start), int(end) + 1))
        else:
            years.append(int(value))
    return sorted(set(years))


def _content_disposition_filename(header: str | None) -> str | None:
    if not header:
        return None
    for part in header.split(";"):
        part = part.strip()
        if part.lower().startswith("filename="):
            return unquote(part.split("=", 1)[1].strip('"'))
    return None


def download_theme_issue_excel(
    *,
    issue_id: int,
    year: int,
    output_dir: Path,
    filename_prefix: str,
    timeout: int,
    overwrite: bool,
) -> dict[str, Any]:
    url = f"{BASE_URL}/statistics/themeIssue/excelDownLoad/{issue_id}"
    params = {"pageIndex": 1, "totalCount": 0, "putYear": year}
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    payload = response.content
    if not payload.startswith(b"PK"):
        raise ValueError(f"KASFO did not return an XLSX file for issue_id={issue_id}, year={year}")

    output_dir = output_dir if output_dir.is_absolute() else PROJECT_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{filename_prefix}_{year}.xlsx"
    digest = _sha256_bytes(payload)
    preservation_action = "downloaded"
    if output_path.exists():
        existing_digest = _sha256_bytes(output_path.read_bytes())
        if existing_digest != digest and not overwrite:
            raise FileExistsError(
                f"{output_path} already exists with a different SHA-256; rerun with --overwrite after manual review"
            )
        preservation_action = "existing_same_sha256" if existing_digest == digest else "overwritten"
    if preservation_action != "existing_same_sha256":
        output_path.write_bytes(payload)
    return {
        "year": year,
        "path": str(output_path.relative_to(PROJECT_ROOT)),
        "page_url": f"{BASE_URL}/statistics/themeIssue/view/{issue_id}?pageIndex=1&putYear={year}&totalCount=0",
        "download_url": response.url,
        "source_menu": "통계현황 > 테마·이슈통계",
        "issue_id": str(issue_id),
        "original_file_name": _content_disposition_filename(response.headers.get("content-disposition")),
        "content_type": response.headers.get("content-type"),
        "file_size_bytes": len(payload),
        "sha256": digest,
        "preservation_action": preservation_action,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue-id", type=int, required=True)
    parser.add_argument("--years", nargs="+", required=True, help="One or more years, or ranges like 2020-2025")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--filename-prefix", required=True)
    parser.add_argument("--metadata-output", type=Path)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    records = [
        download_theme_issue_excel(
            issue_id=args.issue_id,
            year=year,
            output_dir=args.output_dir,
            filename_prefix=args.filename_prefix,
            timeout=args.timeout,
            overwrite=args.overwrite,
        )
        for year in _parse_years(args.years)
    ]
    payload = {
        "source_org": "한국사학진흥재단",
        "source_name": "대학재정알리미 테마·이슈통계",
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "records": records,
    }

    if args.metadata_output:
        args.metadata_output.parent.mkdir(parents=True, exist_ok=True)
        args.metadata_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
