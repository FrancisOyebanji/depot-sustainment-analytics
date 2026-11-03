# Decision Science & Operations Research — Revenue Management, Optimization, Forecasting & Simulation

**A decision-science toolkit across the techniques a decision scientist uses: revenue management & pricing (nonlinear price optimization, EMSR seat protection, stochastic overbooking), supply-chain optimization (demand forecasting, inventory optimization, facility-location network design), and an operations-research digital twin (discrete-event simulation, Theory of Constraints) — every optimum graded against a known solution or Monte Carlo simulation. Python + SQL.**

> **In one breath (Decision Science / Revenue Management focus):** Built a decision-science toolkit spanning pricing, revenue management, resource allocation, forecasting, optimization and simulation — nonlinear price optimization that recovers the true profit-maximizing price from noisy demand data, EMSR-b seat protection that lifts expected revenue ~124% over naive allocation in a booking simulation, stochastic overbooking whose analytic optimum matches Monte Carlo to within a fraction of a percent, plus supply-chain demand forecasting, (s,Q) inventory optimization validated to a 95% service level, and facility-location network design matched to the brute-force optimum — all atop an operations-research digital twin (discrete-event simulation, Theory of Constraints), every result graded against ground truth.

## Revenue Management & Pricing (headline for the Decision Scientist role)

The revenue-management and pricing decisions a decision scientist models — pricing, capacity allocation, overbooking — each solved with the right optimization technique and validated by simulation against a known optimum:

```bash
pip install -r requirements.txt
PYTHONPATH=src python -m revenue_management.run_revenue       # pricing -> capacity allocation -> overbooking
PYTHONPATH=src python -m revenue_management.build_dashboard   # revenue-management dashboard
PYTHONPATH=src python -m pytest tests/test_revenue_management.py -q   # 3 tests, graded vs optima + simulation
```

| Problem | Technique | Result (graded vs ground truth) |
|---|---|---|
| **Price optimization** ([price_optimization.py](src/revenue_management/price_optimization.py)) | demand estimation + **nonlinear optimization** | recovers true optimal price (73.0 vs 72.5), R² 0.96, elasticity at optimum |
| **Capacity allocation** ([capacity_allocation.py](src/revenue_management/capacity_allocation.py)) | **EMSR-b** nested seat protection | **+124% expected revenue** vs naive FCFS in booking simulation |
| **Overbooking** ([overbooking.py](src/revenue_management/overbooking.py)) | **stochastic optimization** (Binomial no-shows) | optimal sell-limit; analytic profit **matches Monte Carlo** within <2% |
| **Booking simulation** ([booking_simulation.py](src/revenue_management/booking_simulation.py)) | Monte Carlo | validates every policy against its baseline |

The through-line is **the right technique for each decision, validated against a known answer**: a nonlinear program for pricing, a protection heuristic for capacity allocation, and a stochastic optimization for overbooking — each checked against an analytic optimum or a Monte Carlo simulation, not just asserted. That maps directly to the JD's revenue management, pricing, resource allocation, nonlinear/stochastic optimization, and simulation asks.

---

## Supply Chain Planning (forecasting, inventory & network optimization)

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
