"""Synthetic supply-chain planning data with KNOWN ground truth.

Produces:
  * demand   - weekly demand history per SKU from a KNOWN process
               (base x seasonal x trend + noise), so forecast accuracy and the
               recovered trend can be graded.
  * skus     - product master: category, unit cost, price, lead time, order cost,
               holding cost, plus the TRUE trend sign and demand CV used to grade
               ABC/XYZ segmentation and the fast-mover classifier.
  * network  - a small capacitated facility-location instance (customers,
               candidate DCs, fixed + transport costs, capacities) whose optimum
               is brute-forceable, so the network-design heuristic can be graded.

No real company, customer, or ERP data is used or represented.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

CATEGORIES = ["Electronics", "Apparel", "Home", "Grocery", "Industrial"]
N_WEEKS = 156            # 3 years of weekly history
HOLDOUT_WEEKS = 13       # last quarter held out for forecast backtest


def generate(seed: int = 5, n_skus: int = 60) -> dict:
    rng = np.random.default_rng(seed)
    weeks = np.arange(N_WEEKS)
    season = 1.0 + 0.30 * np.sin(2 * np.pi * weeks / 52.0)   # annual seasonality

    sku_rows, demand_rows = [], []
    for i in range(n_skus):
        sku = f"SKU{i:04d}"
        cat = rng.choice(CATEGORIES)
        base = float(rng.uniform(20, 400))
        trend = float(rng.choice([-0.004, -0.002, 0.0, 0.003, 0.006],
                                 p=[0.15, 0.2, 0.2, 0.25, 0.2]))   # weekly growth
        noise_cv = float(rng.uniform(0.08, 0.55))                  # demand variability
        unit_cost = float(rng.uniform(2, 120))
        price = round(unit_cost * rng.uniform(1.25, 2.4), 2)
        lead_time_wk = int(rng.integers(1, 7))
        order_cost = float(rng.uniform(40, 150))                   # fixed cost per order
        holding_rate = 0.25                                        # annual holding % of cost

        level = base * (1.0 + trend * weeks) * season
        demand = np.maximum(0, rng.normal(level, noise_cv * level)).round()
        for w in range(N_WEEKS):
            demand_rows.append((sku, int(w), float(demand[w])))

        mean_d = float(demand.mean())
        sku_rows.append({
            "sku": sku, "category": cat, "unit_cost": round(unit_cost, 2),
            "price": price, "lead_time_wk": lead_time_wk,
            "order_cost": round(order_cost, 2), "holding_rate": holding_rate,
            "mean_weekly_demand": round(mean_d, 2),
            "annual_revenue": round(mean_d * 52 * price, 2),
            "true_trend": trend, "true_noise_cv": round(noise_cv, 3),
        })

    skus = pd.DataFrame(sku_rows)
    demand = pd.DataFrame(demand_rows, columns=["sku", "week", "demand"])

    # ----- network-design instance (small, brute-forceable) -----
    n_cust, n_dc = 12, 5
    cust_demand = rng.integers(40, 160, n_cust).astype(float)
    dc_fixed = rng.integers(800, 1600, n_dc).astype(float)
    dc_capacity = rng.integers(350, 650, n_dc).astype(float)
    # transport cost ~ geographic distance proxy
    cust_xy = rng.uniform(0, 100, (n_cust, 2))
    dc_xy = rng.uniform(0, 100, (n_dc, 2))
    transport = np.linalg.norm(cust_xy[:, None, :] - dc_xy[None, :, :], axis=2) * 0.5

    network = {
        "cust_demand": cust_demand,
        "dc_fixed": dc_fixed,
        "dc_capacity": dc_capacity,
        "transport": transport,       # shape (n_cust, n_dc) per-unit cost
    }

    return {"skus": skus, "demand": demand, "network": network,
            "n_weeks": N_WEEKS, "holdout_weeks": HOLDOUT_WEEKS}


if __name__ == "__main__":
    d = generate()
    print(f"SKUs={len(d['skus'])} | demand rows={len(d['demand'])}")
    print(d["skus"][["sku", "category", "mean_weekly_demand", "true_trend",
                     "true_noise_cv", "annual_revenue"]].head())
    net = d["network"]
    print(f"network: {len(net['cust_demand'])} customers, {len(net['dc_fixed'])} candidate DCs, "
          f"total demand {net['cust_demand'].sum():.0f}, total capacity {net['dc_capacity'].sum():.0f}")
