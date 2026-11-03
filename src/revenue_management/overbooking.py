"""Overbooking under no-show uncertainty (stochastic optimization).

Each sold seat shows with probability s, so selling only `capacity` seats leaves
planes flying empty. Selling more risks denied boardings. We choose the sell limit
that maximizes expected profit, trading fare revenue against expected denied-
boarding cost, computed exactly from the Binomial no-show distribution — then
validate the optimum with a Monte Carlo booking simulation.
"""
from __future__ import annotations

import numpy as np
from scipy.stats import binom

from revenue_management import booking_simulation as sim


def _expected_denied(n, capacity, show_prob):
    """E[max(0, Shows - capacity)] with Shows ~ Binomial(n, show_prob)."""
    k = np.arange(capacity + 1, n + 1)
    if len(k) == 0:
        return 0.0
    return float(((k - capacity) * binom.pmf(k, n, show_prob)).sum())


def optimize(overbooking: dict, max_overbook_frac: float = 0.4) -> dict:
    cap = overbooking["capacity"]
    s = overbooking["show_prob"]
    fare = overbooking["fare"]
    dcost = overbooking["denied_cost"]

    best_n, best_profit = cap, -np.inf
    curve = []
    for n in range(cap, int(cap * (1 + max_overbook_frac)) + 1):
        exp_profit = n * fare - dcost * _expected_denied(n, cap, s)
        curve.append((n, round(exp_profit, 1)))
        if exp_profit > best_profit:
            best_profit, best_n = exp_profit, n

    no_ob_profit = cap * fare - dcost * _expected_denied(cap, cap, s)   # sell only capacity
    return {
        "optimal_sell_limit": best_n,
        "overbooking_seats": best_n - cap,
        "expected_profit_optimal": round(best_profit, 1),
        "expected_profit_no_overbooking": round(no_ob_profit, 1),
        "profit_gain_vs_no_overbooking": round(best_profit - no_ob_profit, 1),
        "expected_denied_at_optimal": round(_expected_denied(best_n, cap, s), 3),
        "profit_curve": curve,
    }


def evaluate(overbooking: dict, n_trials: int = 8000) -> dict:
    opt = optimize(overbooking)
    cap = overbooking["capacity"]
    # validate with simulation: optimal sell-limit should beat selling only capacity
    sim_opt, denied_opt = sim.simulate_overbooking(
        cap, overbooking["show_prob"], overbooking["fare"], overbooking["denied_cost"],
        opt["optimal_sell_limit"], n_trials)
    sim_cap, _ = sim.simulate_overbooking(
        cap, overbooking["show_prob"], overbooking["fare"], overbooking["denied_cost"],
        cap, n_trials)
    return {
        **opt,
        "sim_profit_optimal": round(sim_opt, 1),
        "sim_profit_no_overbooking": round(sim_cap, 1),
        "sim_mean_denied": round(denied_opt, 3),
        "overbooking_beats_baseline": bool(sim_opt > sim_cap),
    }
