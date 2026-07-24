# Depot Sustainment Analytics — PySpark Pipeline + Operations-Research Digital Twin

**A depot maintenance (MRO) analytics system: a PySpark data pipeline with a data-fidelity monitoring layer, industrial-engineering constraint analysis, and a discrete-event simulation (digital twin) that runs what-if capacity scenarios and produces a leadership decision briefing.**

> **In one breath:** Built a depot-sustainment analytics system combining a PySpark (Foundry-style) data pipeline and data-fidelity monitoring layer with an operations-research digital twin: industrial-engineering constraint analysis identifies the bottleneck work center (124% utilization), and a from-scratch discrete-event simulation quantifies what-if capacity investments (adding one server at the constraint lifts throughput +15%), delivered as an executive decision-support briefing.

## What it does

Models a depot that overhauls assets through five work centers (Disassembly → Inspection → Repair → Assembly → Test), then answers the questions a modernization decision needs:

1. **Is the data trustworthy?** — a fidelity monitor catalogs missing timestamps, negative durations, orphan work centers, and out-of-sequence steps with counts, severity, and remediation recommendations.
2. **Where is the constraint?** — industrial-engineering analysis computes per-work-center utilization and applies Theory of Constraints to locate the bottleneck.
3. **What should we invest in?** — a discrete-event simulation runs capacity what-if scenarios and quantifies the throughput and flow-time impact of each.

## Results (reproduce with `python src/run_pipeline.py`)

| | |
|---|---|
| Bottleneck | **Repair** @ 124% utilization (demand exceeds capacity) |
| Baseline throughput | 4.8 work orders/day (capped by the constraint) |
| + 1 Repair server | **+15%** throughput, lower flow time |
| + 2 Repair servers | +26% throughput (constraint relieved) |
| + 1 Repair **and** 1 Test | ≈ same as +1 Repair alone — **investing off the constraint is wasted** |
| Data fidelity score | 99.3% (90 issues cataloged with remediations) |

That last row is the Theory-of-Constraints lesson made quantitative: capacity added anywhere but the bottleneck does not move throughput.

## Run it

```bash
pip install -r requirements.txt
python src/run_pipeline.py       # generate -> fidelity -> clean -> IE analysis -> simulation -> briefing
python src/build_dashboard.py    # decision-support dashboard -> reports/dashboard.html
python -m pytest tests/ -q       # 4 analytics tests (+1 PySpark test when Spark is present)
```

Outputs: [`reports/DECISION_BRIEFING.md`](reports/DECISION_BRIEFING.md), `reports/dashboard.html`, and JSON results for fidelity, IE analysis, and simulation.

## Architecture

```
 src/generate_workorders.py   synthetic MRO work orders (with seeded data-fidelity issues)
 src/data_fidelity.py         catalog issues: count · severity · remediation  (governance/monitoring)
 transforms/pipeline.py       PySpark clean/aggregate — Foundry Code Repositories style
 src/industrial_engineering.py  utilization, Theory-of-Constraints bottleneck, implied capacity
 src/simulation.py            discrete-event digital twin + averaged what-if scenarios
 src/briefing.py              leadership decision briefing (BLUF + recommendation)
```

### On PySpark and Foundry

`transforms/pipeline.py` is written in **PySpark**, structured as Palantir Foundry Code Repositories transforms would be — each function maps to a `@transform_df` with typed dataset I/O. The orchestrator runs the Spark pipeline when a Spark runtime is available and falls back to an identical-logic **pandas** implementation otherwise, so the analysis always executes and the repo is verifiable without a cluster. The `test_pyspark_clean_matches_rules` test exercises the Spark path when PySpark is installed.

## Design choices worth noting

- **The bottleneck is engineered, then rediscovered.** Repair is deliberately under-capacitied in the data generator; the IE analysis and simulation both independently find it — and a test asserts they do.
- **Steady-state measurement, not backlog draining.** The simulation measures throughput over a `[warmup, horizon]` window and averages replications, so an unstable baseline reports its true (capped) throughput rather than an artifact of draining the queue.
- **Fidelity is a first-class deliverable.** Bad rows are cataloged with counts and remediations (the "identify, summarize, and catalog data fidelity issues" task), not silently dropped.
- **The output is a decision, not a dataset.** The pipeline ends in a BLUF briefing a senior leader can act on.

## Data & compliance

All work-order, timing, and routing data is synthetic and seeded. No real depot, ERP/MRO system, program, or classified information is used or represented.

---

*Francis Oluwatobi · oluwatobi.ou@gmail.com*
