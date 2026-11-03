"""Synthetic revenue-management data with KNOWN ground truth.

  price_demand  - noisy (price, quantity) observations from a KNOWN linear demand
                  curve Q(p) = a - b*p, with a known unit cost, so the recovered
                  optimal price can be graded against the analytic optimum.
  fare_classes  - multi-class demand (fare, mean, std) and a shared capacity, for
                  seat-protection / capacity allocation.
  overbooking   - capacity, per-passenger show probability, fare, and denied-
                  boarding cost, for the stochastic overbooking decision.

No real pricing, booking, or demand data is used or represented.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# ---- true pricing process ----
TRUE_A = 1000.0      # demand intercept
TRUE_B = 8.0         # price sensitivity (slope)
UNIT_COST = 20.0     # marginal cost per unit


def optimal_price_profit(a=TRUE_A, b=TRUE_B, c=UNIT_COST):
    """Analytic profit-maximizing price for linear demand Q=a-b*p."""
    p_star = (a / b + c) / 2.0
    q_star = a - b * p_star
    profit = (p_star - c) * q_star
    return p_star, q_star, profit


def generate(seed: int = 7, n_price_points: int = 60) -> dict:
    rng = np.random.default_rng(seed)

    prices = rng.uniform(40, 110, n_price_points)
    quantity = np.maximum(0, TRUE_A - TRUE_B * prices + rng.normal(0, 40, n_price_points))
    price_demand = pd.DataFrame({"price": prices.round(2), "quantity": quantity.round(0)})

    p_star, q_star, profit = optimal_price_profit()

    fare_classes = [
        {"fare_class": "Y", "fare": 400.0, "mean_demand": 25.0, "std_demand": 8.0},
        {"fare_class": "B", "fare": 250.0, "mean_demand": 40.0, "std_demand": 12.0},
        {"fare_class": "M", "fare": 150.0, "mean_demand": 60.0, "std_demand": 18.0},
        {"fare_class": "Q", "fare": 90.0,  "mean_demand": 80.0, "std_demand": 20.0},
    ]
    capacity = 100

    overbooking = {"capacity": 100, "show_prob": 0.88, "fare": 200.0, "denied_cost": 400.0}

    return {
        "price_demand": price_demand,
        "pricing_truth": {"a": TRUE_A, "b": TRUE_B, "unit_cost": UNIT_COST,
                          "optimal_price": round(p_star, 2),
                          "optimal_quantity": round(q_star, 1),
                          "optimal_profit": round(profit, 1)},
        "fare_classes": fare_classes,
        "capacity": capacity,
        "overbooking": overbooking,
    }


if __name__ == "__main__":
    d = generate()
    pt = d["pricing_truth"]
    print(f"pricing truth: optimal price ${pt['optimal_price']} -> "
          f"Q {pt['optimal_quantity']}, profit ${pt['optimal_profit']:,}")
    print(f"fare classes: {[c['fare_class'] for c in d['fare_classes']]} | capacity {d['capacity']}")
    print(f"total mean demand {sum(c['mean_demand'] for c in d['fare_classes'])} vs capacity {d['capacity']}")
    print(f"overbooking: {d['overbooking']}")
