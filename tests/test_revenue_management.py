"""Tests for the revenue management module (graded vs known optima + simulation)."""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(scope="module")
def result(tmp_path_factory):
    os.chdir(tmp_path_factory.mktemp("rm"))
    from revenue_management import run_revenue
    return run_revenue.main()


# ---------------- price optimization ----------------
def test_price_optimization_recovers_optimum(result):
    po = result["price_optimization"]
    assert po["price_within_5pct"] is True
    assert po["demand_estimate"]["r_squared"] > 0.85
    # elasticity at the profit optimum should be elastic (|e| > 1)
    assert abs(po["optimization"]["elasticity_at_optimum"]) > 1.0


# ---------------- capacity allocation ----------------
def test_emsr_beats_fcfs(result):
    ca = result["capacity_allocation"]
    assert ca["emsr_beats_fcfs"] is True
    assert ca["revenue_uplift_pct"] > 0
    # booking limits are nested non-increasing from high to low fare class
    bl = ca["booking_limits"]
    assert all(bl[i] >= bl[i + 1] for i in range(len(bl) - 1))


# ---------------- overbooking ----------------
def test_overbooking_optimal_and_validated(result):
    ob = result["overbooking"]
    assert ob["overbooking_seats"] > 0                 # no-shows make overbooking worthwhile
    assert ob["overbooking_beats_baseline"] is True
    # analytic optimum matches the Monte Carlo simulation within 2%
    rel = abs(ob["expected_profit_optimal"] - ob["sim_profit_optimal"]) / ob["expected_profit_optimal"]
    assert rel < 0.02
