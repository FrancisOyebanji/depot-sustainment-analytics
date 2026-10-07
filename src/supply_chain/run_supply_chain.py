"""End-to-end Supply Chain Planning run: forecast -> inventory -> network -> mining."""
from __future__ import annotations

import json
from pathlib import Path

from supply_chain import (abc_xyz, demand_forecasting, generate_supply_chain_data,
                          inventory_optimization, network_design)


def main() -> dict:
    print("=== 1/5 Generating supply-chain data (known demand process) ===")
    d = generate_supply_chain_data.generate()
    print(f"   SKUs={len(d['skus'])} | demand weeks={d['n_weeks']}")

    print("=== 2/5 Demand forecasting (backtest) ===")
    fc = demand_forecasting.backtest(d["demand"], holdout=d["holdout_weeks"])
    print(f"   WAPE ml {fc['wape_ml']} vs naive {fc['wape_naive']} "
          f"(+{fc['improvement_vs_naive_pct']}% better) | bias {fc['bias_ml']}")

    print("=== 3/5 Inventory optimization (service-level validated) ===")
    inv = inventory_optimization.optimize(d["skus"], d["demand"], service_level=0.95)
    print(f"   target {inv['service_level_target']} | achieved fill {inv['mean_achieved_fill_rate']} | "
          f"{int(inv['pct_skus_meeting_target']*100)}% SKUs meet target")

    print("=== 4/5 Network design (facility location) ===")
    net = network_design.optimize(d["network"])
    print(f"   optimum opens DCs {net['optimum']['open_dcs']} @ {net['optimum']['cost']} | "
          f"heuristic optimal: {net['heuristic_is_optimal']} (gap {net['optimality_gap_pct']}%)")
    print(f"   saves {net['savings_vs_all_open_pct']}% vs opening all DCs")

    print("=== 5/5 ABC/XYZ data mining + fast-mover prediction ===")
    seg = abc_xyz.segment(d["skus"], d["demand"])
    fast = abc_xyz.predict_fast_movers(d["skus"], d["demand"])
    print(f"   ABC: A-class {seg['a_class_sku_share']*100:.0f}% of SKUs hold "
          f"{seg['a_class_revenue_share']*100:.0f}% of revenue | fast-mover AUC {fast['auc']}")

    result = {"forecasting": fc, "inventory": inv, "network": net,
              "segmentation": seg, "fast_mover_model": fast}
    Path("reports").mkdir(exist_ok=True)
    Path("reports/supply_chain_results.json").write_text(json.dumps(result, indent=2, default=str))
    print("\nResults -> reports/supply_chain_results.json")
    return result


if __name__ == "__main__":
    main()
