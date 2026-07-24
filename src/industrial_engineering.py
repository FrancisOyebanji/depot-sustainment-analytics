"""Industrial-engineering analysis of depot flow.

Applies classic operations-research / Lean methods to the cleaned work-order
data to locate the constraint and quantify capacity:

  - Utilization per work center  = demand hours / available capacity hours
  - Bottleneck (Theory of Constraints) = highest-utilization work center
  - Implied throughput at the constraint (servers / mean service time)

Capacity is modeled as continuous operation (24h/day) to match the simulation;
the horizon is derived from the data's own arrival span rather than hardcoded.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Capacity model (must match src/generate_workorders.py and src/simulation.py)
SERVERS = {"Disassembly": 2, "Inspection": 2, "Repair": 6, "Assembly": 4, "Test": 2}
HOURS_PER_DAY = 24          # continuous operation, matches the simulation


def load_clean(clean_csv: str):
    agg = defaultdict(lambda: {"n": 0, "hours": 0.0})
    times = []
    for r in csv.DictReader(open(clean_csv)):
        wc = r["work_center"]
        agg[wc]["n"] += 1
        agg[wc]["hours"] += float(r["processing_hours"])
        if r.get("arrival_ts"):
            try:
                times.append(datetime.fromisoformat(r["arrival_ts"]))
            except ValueError:
                pass
    span_days = max(1.0, (max(times) - min(times)).total_seconds() / 86400) if times else 1.0
    return agg, span_days


def analyze(clean_csv: str = "data/work_orders_clean.csv",
            out_path: str = "reports/ie_analysis.json") -> dict:
    agg, span_days = load_clean(clean_csv)
    rows = []
    for wc, d in agg.items():
        capacity_hours = SERVERS[wc] * HOURS_PER_DAY * span_days
        util = d["hours"] / capacity_hours
        mean_hrs = d["hours"] / d["n"]
        rows.append({
            "work_center": wc, "servers": SERVERS[wc],
            "demand_hours": round(d["hours"], 1),
            "capacity_hours": round(capacity_hours, 1),
            "utilization_pct": round(100 * util, 1),
            "implied_capacity_per_day": round(SERVERS[wc] * HOURS_PER_DAY / mean_hrs, 2),
            "steps": d["n"],
        })
    rows.sort(key=lambda r: -r["utilization_pct"])
    bn = rows[0]

    result = {
        "horizon_days": round(span_days, 1), "hours_per_day": HOURS_PER_DAY,
        "work_centers": rows,
        "bottleneck": {
            "work_center": bn["work_center"],
            "utilization_pct": bn["utilization_pct"],
            "implied_throughput_units_per_day": bn["implied_capacity_per_day"],
        },
        "recommendation": (
            f"{bn['work_center']} is the constraint at {bn['utilization_pct']}% utilization "
            f"(capacity ~{bn['implied_capacity_per_day']} units/day). Per Theory of Constraints, "
            f"system throughput is capped here; adding one server at {bn['work_center']} is the "
            f"highest-leverage capacity investment — quantified in the simulation."),
    }
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    print(json.dumps(analyze(), indent=2))
