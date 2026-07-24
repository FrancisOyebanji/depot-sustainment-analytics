# Depot Sustainment — Decision-Support Briefing

*Synthetic demonstration. Prepared from the analytics pipeline in this repository.*

## Bottom line up front (BLUF)

The **Repair** work center is the depot's throughput constraint at
**124.1% utilization**. Adding **one server at Repair**
raises modeled throughput **+15.3%**
(from 4.77 to 5.5 work orders/day)
and cuts mean flow time **56.1%**. This is the
single highest-leverage capacity investment and should be prioritized in the
modernization plan.

## Data fidelity (analysis is only as good as the feed)

The source feed scored **99.28% fidelity**
(90 issues across 12,500 rows). Top issues:

| Issue | Count | Severity |
|---|---|---|
| missing_arrival_timestamp | 30 | high |
| negative_or_zero_processing_hours | 25 | high |
| orphan_work_center | 20 | medium |
| out_of_sequence_step | 15 | medium |

These rows are dropped or quarantined by the pipeline before analysis; resolving
them at the source (see recommendations in `reports/fidelity_report.json`) would
raise confidence in scheduling and forecasting outputs.

## Constraint analysis (Theory of Constraints)

| Work center | Servers | Utilization |
|---|---|---|
| Repair | 6 | 124.1% |
| Disassembly | 2 | 79.3% |
| Assembly | 4 | 66.5% |
| Test | 2 | 66.1% |
| Inspection | 2 | 54.0% |

## What-if scenarios (discrete-event simulation)

| Scenario | Throughput/day | Gain | Mean flow time | Flow-time reduction | Repair util. |
|---|---|---|---|---|---|
| baseline | 4.77 | +0.0% | 824.08 h | 0.0% | 99.8% |
| add_1_repair_server | 5.5 | +15.3% | 361.56 h | 56.1% | 99.3% |
| add_2_repair_servers | 6.01 | +26.0% | 91.96 h | 88.8% | 93.4% |
| add_1_repair_and_test | 5.51 | +15.5% | 356.58 h | 56.7% | 99.0% |

## Recommendation

1. **Invest first at the constraint.** Add one Repair server before any
   other capacity spend; the simulation shows diminishing returns once the constraint
   moves elsewhere (compare the multi-server scenarios).
2. **Fix the feed.** Prioritize the high-severity fidelity issues so scheduling and
   readiness forecasts rest on complete data.
3. **Stand up the digital twin as a standing capability.** Re-run scenarios as demand
   and staffing change, rather than as a one-time study.

*Modeling caveat: results come from a synthetic arrival/service model; on real depot
data the same pipeline and simulation would be re-parameterized from ERP/MRO history.*
