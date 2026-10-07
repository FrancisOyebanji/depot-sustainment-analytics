"""Network design: capacitated facility location (which DCs to open).

Minimize total cost = fixed cost of opened DCs + per-unit transport cost of
serving every customer's demand, subject to DC capacity and meeting all demand.

Given an OPEN set of DCs, the customer-to-DC flow is a transportation LP solved
exactly with scipy.linprog. The open/close decision is integer; we solve it with
a "drop" heuristic (start all-open, greedily close the DC that most reduces total
cost while staying feasible) and grade it against the BRUTE-FORCE optimum over all
DC subsets — so the heuristic is validated, not assumed optimal.
"""
from __future__ import annotations

from itertools import combinations

import numpy as np
from scipy.optimize import linprog


def _transport_cost(open_dcs, cust_demand, dc_capacity, transport):
    """Min transport cost to serve all demand from the open DCs (LP). inf if infeasible."""
    open_dcs = list(open_dcs)
    if not open_dcs or dc_capacity[open_dcs].sum() < cust_demand.sum() - 1e-6:
        return np.inf, None
    n_cust = len(cust_demand)
    m = len(open_dcs)
    # variables x[i,j] = units shipped from customer i to open DC j
    c = transport[:, open_dcs].flatten()
    # demand equality: sum_j x[i,j] == demand[i]
    A_eq, b_eq = [], []
    for i in range(n_cust):
        row = np.zeros(n_cust * m)
        row[i * m:(i + 1) * m] = 1
        A_eq.append(row); b_eq.append(cust_demand[i])
    # capacity: sum_i x[i,j] <= cap[j]
    A_ub, b_ub = [], []
    for j in range(m):
        row = np.zeros(n_cust * m)
        for i in range(n_cust):
            row[i * m + j] = 1
        A_ub.append(row); b_ub.append(dc_capacity[open_dcs[j]])
    res = linprog(c, A_ub=np.array(A_ub), b_ub=np.array(b_ub),
                  A_eq=np.array(A_eq), b_eq=np.array(b_eq),
                  bounds=[(0, None)] * (n_cust * m), method="highs")
    if not res.success:
        return np.inf, None
    return float(res.fun), res.x


def total_cost(open_dcs, net):
    tc, _ = _transport_cost(open_dcs, net["cust_demand"], net["dc_capacity"], net["transport"])
    if tc == np.inf:
        return np.inf
    return tc + net["dc_fixed"][list(open_dcs)].sum()


def brute_force_optimum(net) -> dict:
    n_dc = len(net["dc_fixed"])
    best_cost, best_set = np.inf, None
    for k in range(1, n_dc + 1):
        for combo in combinations(range(n_dc), k):
            c = total_cost(combo, net)
            if c < best_cost:
                best_cost, best_set = c, combo
    return {"open_dcs": [int(x) for x in best_set], "cost": round(float(best_cost), 1)}


def drop_heuristic(net) -> dict:
    n_dc = len(net["dc_fixed"])
    open_set = set(range(n_dc))               # start all open (feasible by capacity)
    best = total_cost(open_set, net)
    improved = True
    while improved and len(open_set) > 1:
        improved = False
        candidate = None
        for dc in list(open_set):
            trial = open_set - {dc}
            c = total_cost(trial, net)
            if c < best - 1e-6:
                best, candidate = c, dc
                improved = True
        if candidate is not None:
            open_set.remove(candidate)
    return {"open_dcs": sorted(int(x) for x in open_set), "cost": round(float(best), 1)}


def optimize(net) -> dict:
    opt = brute_force_optimum(net)
    heur = drop_heuristic(net)
    gap = (heur["cost"] - opt["cost"]) / opt["cost"] if opt["cost"] else 0.0
    all_open = total_cost(set(range(len(net["dc_fixed"]))), net)
    return {
        "n_candidate_dcs": int(len(net["dc_fixed"])),
        "optimum": opt,
        "heuristic": heur,
        "optimality_gap_pct": round(gap * 100, 3),
        "heuristic_is_optimal": heur["open_dcs"] == opt["open_dcs"],
        "savings_vs_all_open_pct": round((1 - opt["cost"] / all_open) * 100, 1),
        "cost_all_open": round(float(all_open), 1),
    }
