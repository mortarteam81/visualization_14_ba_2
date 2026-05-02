"""Build a candidate lecturer-pay asset from local AcademyInfo data.

The preserved raw directory only contains README provenance notes for this
metric.  This converter therefore performs processed-to-candidate
re-standardization and writes an explicit source-preservation gap in its report.
It never overwrites current processed assets.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from utils.data_pipeline import prepare_lecturer_pay_frame

from scripts.converters.academyinfo_common import (
    PROJECT_ROOT,
    AcademyInfoDatasetConfig,
    write_candidate_outputs,
)

DATASET_ID = "lecturer_pay"
CONFIG = AcademyInfoDatasetConfig(
    dataset_id=DATASET_ID,
    dataset_name_ko="강사 강의료",
    source_section="공시데이터 다운로드 > 공시항목 > 14-차. 강사 강의료",
    source_processed_path=PROJECT_ROOT
    / "data"
    / "processed"
    / DATASET_ID
    / "lecturer_pay_2023_2025_v2_1_utf8.csv",
    expected_raw_files=(
        PROJECT_ROOT / "data" / "raw" / DATASET_ID / "lecturer_pay_2023_2025_original.xlsx",
    ),
    source_metadata_path=PROJECT_ROOT / "data" / "metadata" / "lecturer_pay_v2_1.source.json",
    candidate_filename="lecturer_pay_2023_2025_candidate.csv",
    transform=prepare_lecturer_pay_frame,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--print-report", action="store_true", help="Print generated report JSON")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    report = write_candidate_outputs(CONFIG)
    if args.print_report:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(report["output_file"])
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
