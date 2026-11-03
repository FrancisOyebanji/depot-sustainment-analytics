"""Multi-fare-class capacity allocation (seat protection).

Implements EMSR-b, the standard revenue-management heuristic for nested seat
protection: for each fare class it computes how many seats to protect for the
higher-value classes, giving nested booking limits for the lower ones. The policy
is validated by Monte Carlo booking simulation against a naive first-come-first-
served policy (no protection) to quantify the revenue it captures.
"""
from __future__ import annotations

import numpy as np
from scipy import stats

from revenue_management import booking_simulation as sim


def emsr_b(fare_classes, capacity) -> dict:
    """Return protection levels and nested booking limits (classes ordered high->low fare)."""
    fares = np.array([c["fare"] for c in fare_classes], dtype=float)
    mu = np.array([c["mean_demand"] for c in fare_classes], dtype=float)
    sd = np.array([c["std_demand"] for c in fare_classes], dtype=float)
    n = len(fare_classes)

    protection = [0]           # protection for classes above class 0 is 0
    booking_limits = [capacity]
    for k in range(1, n):
        mu_agg = mu[:k].sum()
        sd_agg = np.sqrt((sd[:k] ** 2).sum())
        fbar = float((fares[:k] * mu[:k]).sum() / mu[:k].sum())
        ratio = fares[k] / fbar
        z = stats.norm.ppf(1 - ratio) if 0 < ratio < 1 else 0.0
        y = mu_agg + z * sd_agg                       # protect this many for classes 0..k-1
        y = float(np.clip(y, 0, capacity))
        protection.append(round(y, 1))
        booking_limits.append(int(max(0, round(capacity - y))))
    return {"protection_levels": protection, "booking_limits": booking_limits}


def evaluate(data: dict, n_trials: int = 4000) -> dict:
    fc, cap = data["fare_classes"], data["capacity"]
    emsr = emsr_b(fc, cap)

    rev_emsr = sim.simulate_capacity_policy(fc, cap, emsr["booking_limits"], n_trials)
    # FCFS baseline: every class can book up to full capacity (no protection)
    rev_fcfs = sim.simulate_capacity_policy(fc, cap, [cap] * len(fc), n_trials)
    # theoretical ceiling: sell every seat at the highest fare (unattainable upper bound)
    ceiling = cap * max(c["fare"] for c in fc)

    uplift = (rev_emsr - rev_fcfs) / rev_fcfs if rev_fcfs else 0.0
    return {
        "booking_limits": emsr["booking_limits"],
        "protection_levels": emsr["protection_levels"],
        "revenue_emsr": round(rev_emsr, 0),
        "revenue_fcfs": round(rev_fcfs, 0),
        "revenue_uplift_pct": round(uplift * 100, 2),
        "emsr_beats_fcfs": bool(rev_emsr > rev_fcfs),
        "pct_of_ceiling": round(rev_emsr / ceiling * 100, 1),
    }
