"""Price optimization (nonlinear).

Estimates the demand curve Q(p) = a - b*p from noisy (price, quantity) data, then
solves the nonlinear profit-maximization  max_p (p - c) * (a - b*p)  for the optimal
price. Because the data comes from a known demand process, the recovered optimal
price is graded against the analytic optimum. Also reports price elasticity at the
optimum, the quantity a business partner cares about.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from sklearn.linear_model import LinearRegression


def estimate_demand(price_demand: pd.DataFrame) -> dict:
    X = price_demand[["price"]].to_numpy()
    y = price_demand["quantity"].to_numpy()
    reg = LinearRegression().fit(X, y)
    a_hat = float(reg.intercept_)
    b_hat = float(-reg.coef_[0])          # Q = a - b*p  => coef is -b
    r2 = float(reg.score(X, y))
    return {"a_hat": round(a_hat, 2), "b_hat": round(b_hat, 3), "r_squared": round(r2, 4)}


def optimize_price(a_hat, b_hat, unit_cost, p_bounds=(1, 300)) -> dict:
    def neg_profit(p):
        q = max(0.0, a_hat - b_hat * p)
        return -(p - unit_cost) * q

    res = minimize_scalar(neg_profit, bounds=p_bounds, method="bounded")
    p_opt = float(res.x)
    q_opt = max(0.0, a_hat - b_hat * p_opt)
    profit = (p_opt - unit_cost) * q_opt
    revenue = p_opt * q_opt
    elasticity = -b_hat * p_opt / q_opt if q_opt else float("nan")   # dQ/dp * p/Q
    return {"optimal_price": round(p_opt, 2), "optimal_quantity": round(q_opt, 1),
            "optimal_profit": round(profit, 1), "optimal_revenue": round(revenue, 1),
            "elasticity_at_optimum": round(elasticity, 3)}


def run(data: dict) -> dict:
    est = estimate_demand(data["price_demand"])
    opt = optimize_price(est["a_hat"], est["b_hat"], data["pricing_truth"]["unit_cost"])
    truth = data["pricing_truth"]
    price_err = abs(opt["optimal_price"] - truth["optimal_price"])
    return {
        "demand_estimate": est,
        "true_params": {"a": truth["a"], "b": truth["b"]},
        "optimization": opt,
        "true_optimal_price": truth["optimal_price"],
        "price_abs_error": round(price_err, 2),
        "price_within_5pct": bool(price_err <= 0.05 * truth["optimal_price"]),
    }
