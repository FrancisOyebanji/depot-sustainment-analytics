"""Synthetic depot maintenance (MRO) work-order data.

Models a depot that overhauls assets through a sequence of work centers
(Disassembly -> Inspection -> Repair -> Assembly -> Test). Each work order
carries arrival time, per-work-center processing hours, and routing. A bottleneck
is deliberately engineered (Repair is under-capacitied) so the industrial-
engineering analysis and simulation have a real constraint to find.

Deliberate DATA-FIDELITY issues are injected (missing timestamps, negative
durations, out-of-sequence steps, orphan work centers) for the monitoring layer.

All data is synthetic; represents no real depot, ERP/MRO system, or program.
"""
from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

SEED = 5
random.seed(SEED)

WORK_CENTERS = ["Disassembly", "Inspection", "Repair", "Assembly", "Test"]
# Mean processing hours per work center; Repair is the heavy step.
MEAN_HOURS = {"Disassembly": 6, "Inspection": 4, "Repair": 28, "Assembly": 10, "Test": 5}
# Servers (parallel capacity) per work center. Baseline Repair is under-resourced
# (6 servers -> capacity 5.1 units/day < 6/day demand): a deliberate bottleneck.
SERVERS = {"Disassembly": 2, "Inspection": 2, "Repair": 6, "Assembly": 4, "Test": 2}

ASSET_TYPES = ["Engine", "Transmission", "Avionics", "Hydraulics"]
N_WORKORDERS = 2500
ARRIVAL_RATE_PER_DAY = 6  # work orders arriving per day (exceeds Repair capacity)


def generate(out_dir: str = "data") -> None:
    rng = random.Random(SEED)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    start = datetime(2025, 1, 1, 6, 0)

    rows = []
    t = start
    for i in range(N_WORKORDERS):
        # Poisson-ish arrivals: exponential inter-arrival gaps
        t += timedelta(hours=rng.expovariate(ARRIVAL_RATE_PER_DAY / 24.0))
        wo = f"WO{i:06d}"
        asset = rng.choice(ASSET_TYPES)
        priority = rng.choices(["Routine", "Urgent", "AOG"], weights=[70, 25, 5])[0]
        for step, wc in enumerate(WORK_CENTERS):
            hours = round(rng.lognormvariate(0, 0.4) * MEAN_HOURS[wc], 1)
            rows.append({
                "work_order": wo, "asset_type": asset, "priority": priority,
                "step_seq": step + 1, "work_center": wc,
                "arrival_ts": t.isoformat(timespec="minutes"),
                "processing_hours": hours,
            })

    # --- Inject data-fidelity issues (~2%) ---
    for _ in range(30):
        rows[rng.randrange(len(rows))]["arrival_ts"] = ""            # missing timestamp
    for _ in range(25):
        rows[rng.randrange(len(rows))]["processing_hours"] = -abs(   # negative duration
            float(rows[rng.randrange(len(rows))]["processing_hours"]))
    for _ in range(20):
        rows[rng.randrange(len(rows))]["work_center"] = "UNKNOWN"    # orphan work center
    for _ in range(15):
        r = rows[rng.randrange(len(rows))]
        r["step_seq"] = 99                                           # out-of-sequence step

    with open(out / "work_orders.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"Wrote {len(rows):,} work-order steps ({N_WORKORDERS:,} work orders) to {out}/work_orders.csv")


if __name__ == "__main__":
    generate()
