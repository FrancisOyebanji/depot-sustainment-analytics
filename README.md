# Supply Chain & Operations Analytics — Planning COE + Operations-Research Digital Twin

**A supply-chain planning and operations-analytics system: demand forecasting, inventory optimization, network design, and ABC/XYZ demand mining with a predictive fast-mover model — on top of an MRO operations-research pipeline (PySpark data pipeline, constraint analysis, discrete-event simulation). Python + SQL.**

> **In one breath (Supply Chain Planning focus):** Built a supply-chain planning suite spanning the COE's full scope — an ML demand-forecasting backtest that beats a seasonal-naive baseline by ~15% WAPE on a held-out quarter, inventory optimization (safety stock / reorder point / EOQ) whose (s,Q) policies are *simulation-validated* to hit a 95% service level, a capacitated facility-location network design solved with a drop heuristic that matches the brute-force optimum (saving ~7% vs opening all DCs), and ABC/XYZ demand mining plus a gradient-boosted fast-mover classifier (ROC-AUC 0.71) — every model graded against known ground truth, atop an operations-research digital twin for capacity/bottleneck analysis.

## Supply Chain Planning COE (headline for the Supply Chain data-science role)

The planning work the COE runs — forecasting, inventory, network, and demand mining — each graded against a known data-generating process:

```bash
pip install -r requirements.txt
PYTHONPATH=src python -m supply_chain.run_supply_chain     # forecast -> inventory -> network -> mining
PYTHONPATH=src python -m supply_chain.build_dashboard      # planning dashboard
PYTHONPATH=src python -m pytest tests/test_supply_chain.py -q   # 6 tests, graded vs truth
```

| Capability | Method | Result (synthetic benchmark) |
|---|---|---|
| **Demand forecasting** ([demand_forecasting.py](src/supply_chain/demand_forecasting.py)) | GBM on lag/calendar features vs seasonal-naive, out-of-time backtest | WAPE **0.30 vs 0.35 naive (+15%)**, bias ≈ 0 |
| **Inventory optimization** ([inventory_optimization.py](src/supply_chain/inventory_optimization.py)) | safety stock / reorder point / EOQ + (s,Q) simulation | **95% service target achieved** (sim fill 0.99), 95% of SKUs meet target |
| **Network design** ([network_design.py](src/supply_chain/network_design.py)) | capacitated facility location: LP transport + drop heuristic | **heuristic = brute-force optimum** (0% gap), saves ~7% vs all-open |
| **Demand mining + prediction** ([abc_xyz.py](src/supply_chain/abc_xyz.py)) | ABC (Pareto) / XYZ (CV) + GBM fast-mover classifier | A-class = 48% of SKUs / **79% of revenue**; fast-mover **AUC 0.71** |

The through-line is **optimization validated against ground truth**: forecasts are backtested out-of-time, the inventory policy is *simulated* to confirm it hits its service target (not just computed from a formula), and the network heuristic is checked against the brute-force optimum. That maps directly to the JD's forecasting, ML modeling, **network design**, and **inventory optimization** scope, plus data mining and predictive models of product behavior.

---

## Depot Sustainment Analytics (the operations-research foundation)

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
