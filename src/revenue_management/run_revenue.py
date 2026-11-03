"""End-to-end revenue management run: pricing -> capacity allocation -> overbooking."""
from __future__ import annotations

import json
from pathlib import Path

from revenue_management import (capacity_allocation, generate_demand_data,
                               overbooking, price_optimization)


def main() -> dict:
    print("=== Generating revenue-management data (known ground truth) ===")
    d = generate_demand_data.generate()

    print("=== 1/3 Price optimization (nonlinear) ===")
    po = price_optimization.run(d)
    print(f"   estimated demand Q = {po['demand_estimate']['a_hat']} - "
          f"{po['demand_estimate']['b_hat']}*p (R2 {po['demand_estimate']['r_squared']})")
    print(f"   optimal price ${po['optimization']['optimal_price']} vs true "
          f"${po['true_optimal_price']} (err {po['price_abs_error']}) | "
          f"profit ${po['optimization']['optimal_profit']:,}")

    print("=== 2/3 Capacity allocation (EMSR-b vs FCFS) ===")
    ca = capacity_allocation.evaluate(d)
    print(f"   booking limits {ca['booking_limits']} | protection {ca['protection_levels']}")
    print(f"   revenue EMSR ${ca['revenue_emsr']:,} vs FCFS ${ca['revenue_fcfs']:,} "
          f"(+{ca['revenue_uplift_pct']}%)")

    print("=== 3/3 Overbooking (stochastic optimization) ===")
    ob = overbooking.evaluate(d["overbooking"])
    print(f"   optimal sell limit {ob['optimal_sell_limit']} (overbook "
          f"{ob['overbooking_seats']}) | profit gain ${ob['profit_gain_vs_no_overbooking']:,}")
    print(f"   analytic ${ob['expected_profit_optimal']:,} vs simulation "
          f"${ob['sim_profit_optimal']:,} (validated)")

    result = {"price_optimization": po, "capacity_allocation": ca, "overbooking": ob}
    Path("reports").mkdir(exist_ok=True)
    Path("reports/revenue_management.json").write_text(json.dumps(result, indent=2, default=str))
    print("\nResults -> reports/revenue_management.json")
    return result


if __name__ == "__main__":
    main()
