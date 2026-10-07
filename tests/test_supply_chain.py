"""Tests for the Supply Chain Planning module.

Each component is graded against the known data-generating process or a brute-force
optimum. The pipeline runs once and is shared across tests.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(scope="module")
def result(tmp_path_factory):
    import os
    os.chdir(tmp_path_factory.mktemp("sc"))
    from supply_chain import run_supply_chain
    return run_supply_chain.main()


# ---------------- forecasting ----------------
def test_ml_forecast_beats_naive(result):
    fc = result["forecasting"]
    assert fc["ml_beats_naive"] is True
    assert fc["wape_ml"] < fc["wape_naive"]
    assert abs(fc["bias_ml"]) < 0.10        # low systematic bias


# ---------------- inventory ----------------
def test_inventory_meets_service_level(result):
    inv = result["inventory"]
    # achieved fill rate should meet or exceed the cycle-service target
    assert inv["mean_achieved_fill_rate"] >= inv["service_level_target"]
    assert inv["pct_skus_meeting_target"] >= 0.8


# ---------------- network design ----------------
def test_network_heuristic_matches_bruteforce(result):
    net = result["network"]
    assert net["heuristic_is_optimal"] is True
    assert net["optimality_gap_pct"] == 0.0
    assert net["optimum"]["cost"] <= net["cost_all_open"]   # opening all is never cheaper


def test_network_opens_subset(result):
    net = result["network"]
    assert 1 <= len(net["optimum"]["open_dcs"]) <= net["n_candidate_dcs"]


# ---------------- data mining + prediction ----------------
def test_abc_pareto_holds(result):
    seg = result["segmentation"]
    # A-class is a minority of SKUs but the majority of revenue (Pareto)
    assert seg["a_class_sku_share"] < 0.6
    assert seg["a_class_revenue_share"] >= 0.7


def test_fast_mover_model_skillful(result):
    fast = result["fast_mover_model"]
    assert fast["auc"] >= 0.65
    assert fast["top_drivers"]
