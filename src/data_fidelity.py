"""Data-fidelity monitoring — Foundry health-check / governance style.

Scans the raw work-order feed for the issue classes that break downstream
pipelines, catalogs each with a count and severity, and emits a report the
pipeline (and a governance Workshop app) can surface. This is the "identify,
summarize, and catalog data fidelity issues" deliverable from the role.

Pure-Python so it runs with or without Spark (the same predicates are applied
in the PySpark clean step; this module is the auditable catalog of what was
dropped and why).
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

VALID_WORK_CENTERS = {"Disassembly", "Inspection", "Repair", "Assembly", "Test"}
MAX_STEP = 5


@dataclass
class FidelityCheck:
    issue: str
    severity: str
    recommendation: str


CHECKS = [
    FidelityCheck("missing_arrival_timestamp", "high",
                  "Backfill from source MRO system event log; block load until populated."),
    FidelityCheck("negative_or_zero_processing_hours", "high",
                  "Reject at ingest; flag originating work center for clock/entry audit."),
    FidelityCheck("orphan_work_center", "medium",
                  "Map to canonical work-center list or route to a review queue."),
    FidelityCheck("out_of_sequence_step", "medium",
                  "Validate routing against the standard process; correct step_seq."),
]


def scan(raw_csv: str = "data/work_orders.csv", out_path: str = "reports/fidelity_report.json") -> dict:
    rows = list(csv.DictReader(open(raw_csv)))
    total = len(rows)
    counts = {c.issue: 0 for c in CHECKS}

    for r in rows:
        if not r["arrival_ts"].strip():
            counts["missing_arrival_timestamp"] += 1
        try:
            if float(r["processing_hours"]) <= 0:
                counts["negative_or_zero_processing_hours"] += 1
        except ValueError:
            counts["negative_or_zero_processing_hours"] += 1
        if r["work_center"] not in VALID_WORK_CENTERS:
            counts["orphan_work_center"] += 1
        try:
            if not (1 <= int(r["step_seq"]) <= MAX_STEP):
                counts["out_of_sequence_step"] += 1
        except ValueError:
            counts["out_of_sequence_step"] += 1

    catalog = [{"issue": c.issue, "severity": c.severity, "count": counts[c.issue],
                "pct_of_rows": round(100 * counts[c.issue] / total, 2),
                "recommendation": c.recommendation} for c in CHECKS]
    total_affected = sum(counts.values())
    report = {
        "rows_scanned": total,
        "total_issues_found": total_affected,
        "fidelity_score_pct": round(100 * (1 - total_affected / total), 2),
        "catalog": sorted(catalog, key=lambda x: -x["count"]),
    }
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    print(json.dumps(scan(), indent=2))
