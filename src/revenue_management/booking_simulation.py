"""Monte Carlo booking simulation to validate revenue-management policies.

Standard low-fare-books-first arrival assumption: discount classes arrive before
full-fare classes. A protection policy rejects low-fare bookings once their nested
booking limit is hit, saving seats for higher-fare demand that arrives later. The
simulator measures expected revenue of a policy so EMSR can be compared to a naive
first-come-first-served policy, and overbooking to no overbooking.
"""
from __future__ import annotations

import numpy as np


def simulate_capacity_policy(fare_classes, capacity, booking_limits, n_trials=4000, seed=0):
    """Expected revenue under nested booking limits (classes ordered high->low fare).

    booking_limits[i] = max seats sellable to classes i..n (nested). Low-fare
    classes arrive first; each class books up to min(its demand, remaining seats,
    seats still allowed by its nested limit).
    """
    rng = np.random.default_rng(seed)
    fares = np.array([c["fare"] for c in fare_classes])          # high -> low
    mu = np.array([c["mean_demand"] for c in fare_classes])
    sd = np.array([c["std_demand"] for c in fare_classes])
    n = len(fare_classes)
    order = list(range(n))[::-1]                                  # low fare books first

    revs = np.zeros(n_trials)
    for t in range(n_trials):
        demand = np.maximum(0, rng.normal(mu, sd)).round().astype(int)
        sold = np.zeros(n, dtype=int)
        for i in order:
            # seats still allowed for classes i..n-1 (nested limit) and total capacity
            already_lower = sum(sold[j] for j in range(i, n))
            allow = max(0, booking_limits[i] - already_lower)
            remaining = capacity - sold.sum()
            take = min(demand[i], allow, remaining)
            sold[i] = take
        revs[t] = float((sold * fares).sum())
    return float(revs.mean())


def simulate_overbooking(capacity, show_prob, fare, denied_cost, sell_limit,
                         n_trials=8000, seed=0):
    """Expected profit when selling up to `sell_limit` seats; each booking shows
    with prob show_prob. Shows above capacity are denied boarding at denied_cost."""
    rng = np.random.default_rng(seed)
    sold = sell_limit                                            # assume demand fills the limit
    shows = rng.binomial(sold, show_prob, n_trials)
    denied = np.maximum(0, shows - capacity)
    revenue = sold * fare
    profit = revenue - denied * denied_cost
    return float(profit.mean()), float(denied.mean())
