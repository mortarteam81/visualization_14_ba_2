"""Build a lightweight SQLite catalog for pending metric raw sources.

This script is intentionally conservative: it does not download external data or
call public APIs.  It creates the raw-first database tables and registers the
planned source metadata for the nine pending metrics.  Actual raw files can be
added later after the source URL, file format, and authentication requirements
are confirmed.

Usage:
    python scripts/build_pending_metric_db.py --db data/raw/pending_metrics.sqlite
    python scripts/build_pending_metric_db.py --db data/raw/pending_metrics.sqlite --print-summary
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from registry.pending_metrics import PENDING_METRIC_PLANS, PendingMetricPlan


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS raw_sources (
  source_id TEXT PRIMARY KEY,
  source_name TEXT NOT NULL,
  source_url TEXT NOT NULL,
  provider TEXT NOT NULL,
  dataset_name TEXT NOT NULL,
  acquired_method TEXT NOT NULL,
  acquired_at TEXT,
  local_path TEXT,
  license_note TEXT,
  auth_required INTEGER NOT NULL DEFAULT 0,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS raw_records (
  source_id TEXT NOT NULL,
  table_name TEXT NOT NULL,
  row_number INTEGER NOT NULL,
  payload_json TEXT NOT NULL,
  PRIMARY KEY (source_id, table_name, row_number),
  FOREIGN KEY (source_id) REFERENCES raw_sources(source_id)
);

CREATE TABLE IF NOT EXISTS metric_values (
  metric_id TEXT NOT NULL,
  school_name TEXT NOT NULL,
  school_id TEXT,
  campus TEXT,
  founding_type TEXT,
  school_type TEXT,
  region TEXT,
  year INTEGER NOT NULL,
  year_type TEXT NOT NULL,
  value REAL,
  numerator REAL,
  denominator REAL,
  unit TEXT NOT NULL,
  source_id TEXT NOT NULL,
  calculated_at TEXT NOT NULL,
  PRIMARY KEY (metric_id, school_name, campus, year, year_type),
  FOREIGN KEY (source_id) REFERENCES raw_sources(source_id)
);

CREATE TABLE IF NOT EXISTS pending_metric_plans (
  metric_id TEXT PRIMARY KEY,
  dataset_key TEXT NOT NULL,
  title TEXT NOT NULL,
  implementation_priority INTEGER NOT NULL,
  needs_definition_review INTEGER NOT NULL,
  numerator TEXT NOT NULL,
  denominator TEXT NOT NULL,
  formula TEXT NOT NULL,
  unit TEXT NOT NULL,
  proposed_series_json TEXT NOT NULL,
  source_priority_json TEXT NOT NULL,
  raw_source_urls_json TEXT NOT NULL,
  api_refresh_urls_json TEXT NOT NULL,
  notes TEXT
);
"""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def infer_provider(url: str) -> str:
    if "data.go.kr" in url:
        return "공공데이터포털"
    if "academyinfo.go.kr" in url:
        return "대학알리미"
    if "uniarlimi.kasfo.or.kr" in url:
        return "한국사학진흥재단 대학재정알리미"
    return "unknown"


def source_id_for(metric_id: str, index: int) -> str:
    return f"pending:{metric_id}:raw:{index}"


def connect_database(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA_SQL)
    return connection


def register_plan(connection: sqlite3.Connection, plan: PendingMetricPlan) -> None:
    connection.execute(
        """
        INSERT OR REPLACE INTO pending_metric_plans (
          metric_id, dataset_key, title, implementation_priority,
          needs_definition_review, numerator, denominator, formula, unit,
          proposed_series_json, source_priority_json, raw_source_urls_json,
          api_refresh_urls_json, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            plan.metric_id,
            plan.dataset_key,
            plan.title,
            plan.implementation_priority,
            int(plan.needs_definition_review),
            plan.numerator,
            plan.denominator,
            plan.formula,
            plan.unit,
            json.dumps([asdict(series) for series in plan.proposed_series], ensure_ascii=False),
            json.dumps(plan.source_priority, ensure_ascii=False),
            json.dumps(plan.raw_source_urls, ensure_ascii=False),
            json.dumps(plan.api_refresh_urls, ensure_ascii=False),
            plan.notes,
        ),
    )


def register_raw_sources(connection: sqlite3.Connection, plan: PendingMetricPlan) -> None:
    for index, url in enumerate(plan.raw_source_urls, start=1):
        provider = infer_provider(url)
        connection.execute(
            """
            INSERT OR REPLACE INTO raw_sources (
              source_id, source_name, source_url, provider, dataset_name,
              acquired_method, acquired_at, local_path, license_note,
              auth_required, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_id_for(plan.metric_id, index),
                plan.source_priority[0],
                url,
                provider,
                plan.dataset_key,
                "planned-download",
                None,
                None,
                "원자료 확보 전 출처 후보. 실제 이용허락/인증 조건은 다운로드 전 재확인 필요.",
                int("data.go.kr" in url or "openapi" in url),
                plan.notes,
            ),
        )


def bootstrap_database(db_path: Path, plans: Iterable[PendingMetricPlan]) -> None:
    with connect_database(db_path) as connection:
        for plan in plans:
            register_plan(connection, plan)
            register_raw_sources(connection, plan)
        connection.commit()


def load_csv_as_raw_records(
    db_path: Path,
    *,
    source_id: str,
    table_name: str,
    csv_path: Path,
    encoding: str = "utf-8-sig",
) -> int:
    """Load a local CSV into raw_records as JSON payload rows.

    This helper is used by tests and later manual ingestion.  It assumes the
    caller already registered the source_id in raw_sources.
    """

    inserted = 0
    with connect_database(db_path) as connection:
        with csv_path.open("r", encoding=encoding, newline="") as handle:
            reader = csv.DictReader(handle)
            for row_number, row in enumerate(reader, start=1):
                connection.execute(
                    """
                    INSERT OR REPLACE INTO raw_records (
                      source_id, table_name, row_number, payload_json
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (
                        source_id,
                        table_name,
                        row_number,
                        json.dumps(row, ensure_ascii=False),
                    ),
                )
                inserted += 1
        connection.commit()
    return inserted


def summarize_database(db_path: Path) -> dict[str, int]:
    with connect_database(db_path) as connection:
        return {
            "pending_metric_plans": connection.execute(
                "SELECT COUNT(*) FROM pending_metric_plans"
            ).fetchone()[0],
            "raw_sources": connection.execute(
                "SELECT COUNT(*) FROM raw_sources"
            ).fetchone()[0],
            "raw_records": connection.execute(
                "SELECT COUNT(*) FROM raw_records"
            ).fetchone()[0],
            "metric_values": connection.execute(
                "SELECT COUNT(*) FROM metric_values"
            ).fetchone()[0],
        }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db",
        type=Path,
        default=PROJECT_ROOT / "data" / "raw" / "pending_metrics.sqlite",
        help="SQLite database path to create/update.",
    )
    parser.add_argument(
        "--print-summary",
        action="store_true",
        help="Print row counts after bootstrapping.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    bootstrap_database(args.db, PENDING_METRIC_PLANS.values())
    if args.print_summary:
        print(json.dumps(summarize_database(args.db), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
