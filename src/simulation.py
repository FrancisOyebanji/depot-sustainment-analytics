"""Discrete-event simulation — a digital twin of the depot flow line.

A from-scratch event-driven simulator (no SimPy dependency): work orders arrive,
flow through the five work centers in sequence, and queue for a free server at
each. It reproduces the bottleneck the IE analysis identifies and lets us run
"what-if" scenarios — the decision-support core of the role.

Metrics per scenario: throughput (completions), mean flow time (cycle time),
mean WIP, and per-work-center utilization + max queue.
"""
from __future__ import annotations

import heapq
import json
import random
import statistics
from dataclasses import dataclass, field
from pathlib import Path

WORK_CENTERS = ["Disassembly", "Inspection", "Repair", "Assembly", "Test"]
MEAN_HOURS = {"Disassembly": 6, "Inspection": 4, "Repair": 28, "Assembly": 10, "Test": 5}
BASE_SERVERS = {"Disassembly": 2, "Inspection": 2, "Repair": 6, "Assembly": 4, "Test": 2}
ARRIVAL_RATE_PER_DAY = 6
SIM_DAYS = 260
WARMUP_DAYS = 60   # exclude the transient before measuring steady-state metrics


@dataclass(order=True)
class Event:
    time: float
    kind: str = field(compare=False)
    wo: int = field(compare=False)
    stage: int = field(compare=False)


class DepotSim:
    def __init__(self, servers: dict[str, int], seed: int = 1):
        self.servers = dict(servers)
        self.rng = random.Random(seed)
        self.free = dict(servers)
        self.queues: dict[str, list] = {wc: [] for wc in WORK_CENTERS}
        self.events: list[Event] = []
        self.enter_time: dict[int, float] = {}
        self.completions: list[tuple[float, float]] = []  # (completion_time, flow_time)
        self.busy_hours = {wc: 0.0 for wc in WORK_CENTERS}
        self.max_queue = {wc: 0 for wc in WORK_CENTERS}
        self.now = 0.0

    def _proc(self, wc: str) -> float:
        return self.rng.lognormvariate(0, 0.4) * MEAN_HOURS[wc]

    def _start_or_queue(self, wo: int, stage: int):
        wc = WORK_CENTERS[stage]
        if self.free[wc] > 0:
            self.free[wc] -= 1
            dur = self._proc(wc)
            self.busy_hours[wc] += dur
            heapq.heappush(self.events, Event(self.now + dur, "depart", wo, stage))
        else:
            self.queues[wc].append((wo, stage))
            self.max_queue[wc] = max(self.max_queue[wc], len(self.queues[wc]))

    def run(self) -> dict:
        horizon = SIM_DAYS * 24
        warmup = WARMUP_DAYS * 24
        # schedule all arrivals up front
        t, i = 0.0, 0
        while t < horizon:
            t += self.rng.expovariate(ARRIVAL_RATE_PER_DAY / 24.0)
            heapq.heappush(self.events, Event(t, "arrive", i, 0))
            i += 1

        # Process events only up to the horizon; we measure the steady-state
        # window [warmup, horizon] and do NOT drain the post-horizon backlog
        # (which would inflate throughput for an unstable system).
        busy_window = {wc: 0.0 for wc in WORK_CENTERS}
        while self.events:
            ev = heapq.heappop(self.events)
            if ev.time > horizon:
                break
            self.now = ev.time
            if ev.kind == "arrive":
                self.enter_time[ev.wo] = ev.time
                self._start_or_queue(ev.wo, 0)
            else:  # depart from a work center
                wc = WORK_CENTERS[ev.stage]
                self.free[wc] += 1
                if self.queues[wc]:                      # pull next from queue
                    nwo, nstage = self.queues[wc].pop(0)
                    self.free[wc] -= 1
                    dur = self._proc(wc)
                    self.busy_hours[wc] += dur
                    heapq.heappush(self.events, Event(self.now + dur, "depart", nwo, nstage))
                if ev.stage + 1 < len(WORK_CENTERS):     # advance to next stage
                    self._start_or_queue(ev.wo, ev.stage + 1)
                else:                                    # work order complete
                    self.completions.append((self.now, self.now - self.enter_time[ev.wo]))

        window_days = SIM_DAYS - WARMUP_DAYS
        in_window = [(ct, ft) for ct, ft in self.completions if ct >= warmup]
        flow = [ft for _, ft in in_window]
        util = {wc: round(100 * self.busy_hours[wc] / (self.servers[wc] * horizon), 1)
                for wc in WORK_CENTERS}
        return {
            "servers": self.servers,
            "completions_in_window": len(in_window),
            "throughput_per_day": round(len(in_window) / window_days, 2),
            "mean_flow_time_hours": round(statistics.mean(flow), 1) if flow else None,
            "p90_flow_time_hours": round(sorted(flow)[int(0.9 * len(flow))], 1) if flow else None,
            "utilization_pct": util,
            "max_queue": dict(self.max_queue),
        }


def _run_replications(servers: dict, n_reps: int = 5) -> dict:
    """Average several independent replications to reduce Monte-Carlo noise."""
    runs = [DepotSim(servers, seed=s).run() for s in range(1, n_reps + 1)]
    def avg(key): return round(sum(r[key] for r in runs) / n_reps, 2)
    base = runs[0]
    base["throughput_per_day"] = avg("throughput_per_day")
    base["mean_flow_time_hours"] = avg("mean_flow_time_hours")
    base["p90_flow_time_hours"] = avg("p90_flow_time_hours")
    base["completions_in_window"] = int(sum(r["completions_in_window"] for r in runs) / n_reps)
    base["utilization_pct"]["Repair"] = round(
        sum(r["utilization_pct"]["Repair"] for r in runs) / n_reps, 1)
    return base


def run_scenarios(out_path: str = "reports/simulation.json") -> dict:
    scenarios = {
        "baseline": BASE_SERVERS,
        "add_1_repair_server": {**BASE_SERVERS, "Repair": BASE_SERVERS["Repair"] + 1},
        "add_2_repair_servers": {**BASE_SERVERS, "Repair": BASE_SERVERS["Repair"] + 2},
        "add_1_repair_and_test": {**BASE_SERVERS, "Repair": BASE_SERVERS["Repair"] + 1,
                                  "Test": BASE_SERVERS["Test"] + 1},
    }
    results = {name: _run_replications(srv) for name, srv in scenarios.items()}

    base = results["baseline"]
    comparison = []
    for name, r in results.items():
        comparison.append({
            "scenario": name,
            "throughput_per_day": r["throughput_per_day"],
            "throughput_gain_pct": round(100 * (r["throughput_per_day"] / base["throughput_per_day"] - 1), 1),
            "mean_flow_time_hours": r["mean_flow_time_hours"],
            "flow_time_reduction_pct": round(100 * (1 - r["mean_flow_time_hours"] / base["mean_flow_time_hours"]), 1),
            "repair_utilization_pct": r["utilization_pct"]["Repair"],
        })

    out = {"scenarios": results, "comparison": comparison}
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    out = run_scenarios()
    print(f"{'scenario':<24}{'thru/day':>10}{'gain%':>8}{'flow hrs':>10}{'flow-red%':>11}")
    for c in out["comparison"]:
        print(f"{c['scenario']:<24}{c['throughput_per_day']:>10}{c['throughput_gain_pct']:>8}"
              f"{c['mean_flow_time_hours']:>10}{c['flow_time_reduction_pct']:>11}")
