"""Decision-support briefing generator.

Turns the fidelity, industrial-engineering, and simulation results into a
leadership-ready Markdown briefing — the "prepare and deliver clear decision-
support briefings and recommendations for senior leaders" deliverable.
"""
from __future__ import annotations

import json
from pathlib import Path


def generate(out_path: str = "reports/DECISION_BRIEFING.md") -> None:
    fid = json.loads(Path("reports/fidelity_report.json").read_text())
    ie = json.loads(Path("reports/ie_analysis.json").read_text())
    sim = json.loads(Path("reports/simulation.json").read_text())

    bn = ie["bottleneck"]
    best = max(sim["comparison"], key=lambda c: c["throughput_gain_pct"])
    one_server = next(c for c in sim["comparison"] if c["scenario"] == "add_1_repair_server")
    base = next(c for c in sim["comparison"] if c["scenario"] == "baseline")

    md = f"""# Depot Sustainment — Decision-Support Briefing

*Synthetic demonstration. Prepared from the analytics pipeline in this repository.*

## Bottom line up front (BLUF)

The **{bn['work_center']}** work center is the depot's throughput constraint at
**{bn['utilization_pct']}% utilization**. Adding **one server at {bn['work_center']}**
raises modeled throughput **+{one_server['throughput_gain_pct']}%**
(from {base['throughput_per_day']} to {one_server['throughput_per_day']} work orders/day)
and cuts mean flow time **{one_server['flow_time_reduction_pct']}%**. This is the
single highest-leverage capacity investment and should be prioritized in the
modernization plan.

## Data fidelity (analysis is only as good as the feed)

The source feed scored **{fid['fidelity_score_pct']}% fidelity**
({fid['total_issues_found']} issues across {fid['rows_scanned']:,} rows). Top issues:

| Issue | Count | Severity |
|---|---|---|
""" + "\n".join(
        f"| {c['issue']} | {c['count']} | {c['severity']} |" for c in fid["catalog"][:4]
    ) + f"""

These rows are dropped or quarantined by the pipeline before analysis; resolving
them at the source (see recommendations in `reports/fidelity_report.json`) would
raise confidence in scheduling and forecasting outputs.

## Constraint analysis (Theory of Constraints)

| Work center | Servers | Utilization |
|---|---|---|
""" + "\n".join(
        f"| {w['work_center']} | {w['servers']} | {w['utilization_pct']}% |"
        for w in ie["work_centers"]
    ) + f"""

## What-if scenarios (discrete-event simulation)

| Scenario | Throughput/day | Gain | Mean flow time | Flow-time reduction | Repair util. |
|---|---|---|---|---|---|
""" + "\n".join(
        f"| {c['scenario']} | {c['throughput_per_day']} | +{c['throughput_gain_pct']}% | "
        f"{c['mean_flow_time_hours']} h | {c['flow_time_reduction_pct']}% | {c['repair_utilization_pct']}% |"
        for c in sim["comparison"]
    ) + f"""

## Recommendation

1. **Invest first at the constraint.** Add one {bn['work_center']} server before any
   other capacity spend; the simulation shows diminishing returns once the constraint
   moves elsewhere (compare the multi-server scenarios).
2. **Fix the feed.** Prioritize the high-severity fidelity issues so scheduling and
   readiness forecasts rest on complete data.
3. **Stand up the digital twin as a standing capability.** Re-run scenarios as demand
   and staffing change, rather than as a one-time study.

*Modeling caveat: results come from a synthetic arrival/service model; on real depot
data the same pipeline and simulation would be re-parameterized from ERP/MRO history.*
"""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(md)
    print(f"Briefing written to {out_path}")


if __name__ == "__main__":
    generate()
