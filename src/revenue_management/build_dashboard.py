"""Revenue-management dashboard from reports/revenue_management.json."""
from __future__ import annotations

import json
from pathlib import Path

R = json.loads(Path("reports/revenue_management.json").read_text())
po, ca, ob = R["price_optimization"], R["capacity_allocation"], R["overbooking"]

# price-profit curve around the optimum
a, b = po["demand_estimate"]["a_hat"], po["demand_estimate"]["b_hat"]
c = 20.0
prices = list(range(30, 121, 3))
profit = [round((p - c) * max(0, a - b * p), 0) for p in prices]

ob_curve = ob["profit_curve"]
ob_labels = [n for n, _ in ob_curve]
ob_profit = [v for _, v in ob_curve]

kpis = [
    ("Optimal price", f"${po['optimization']['optimal_price']:.0f}"),
    ("Price vs truth", f"±${po['price_abs_error']:.1f}"),
    ("EMSR revenue uplift", f"+{ca['revenue_uplift_pct']:.0f}%"),
    ("Overbook seats", f"+{ob['overbooking_seats']}"),
    ("Overbooking profit gain", f"${ob['profit_gain_vs_no_overbooking']:,.0f}"),
    ("Elasticity @ optimum", f"{po['optimization']['elasticity_at_optimum']:.2f}"),
]
kpi_html = "".join(f"<div class='kpi'><div class='l'>{l}</div><div class='v'>{v}</div></div>" for l, v in kpis)

html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Revenue Management</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
 body{{font-family:'Segoe UI',system-ui,sans-serif;background:#f5f6f8;color:#14223a;margin:0}}
 header{{background:#123a5e;color:#fff;padding:16px 30px}} h1{{font-size:20px;margin:0}}
 .sub{{color:#b7cde0;font-size:13px}}
 main{{max-width:1080px;margin:22px auto;padding:0 18px}}
 .kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px;margin-bottom:20px}}
 .kpi{{background:#fff;border:1px solid #e2e8ef;border-radius:12px;padding:16px}}
 .kpi .l{{color:#5c7086;font-size:13px}}.kpi .v{{font-size:21px;font-weight:700;margin-top:4px;color:#123a5e}}
 .grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
 .panel{{background:#fff;border:1px solid #e2e8ef;border-radius:12px;padding:18px;margin-bottom:18px}}
 .panel h2{{font-size:15px;margin:0 0 12px}} canvas{{max-height:280px}}
 table{{width:100%;border-collapse:collapse;font-size:13px}} th,td{{padding:7px 9px;border-bottom:1px solid #eef2f6;text-align:center}}
 th{{color:#5c7086}}
 .note{{background:#e8eff6;border-left:4px solid #123a5e;padding:10px 14px;border-radius:6px;font-size:14px}}
 @media(max-width:800px){{.grid{{grid-template-columns:1fr}}}}
 footer{{color:#5c7086;font-size:12px;text-align:center;margin:24px 0}}
</style></head><body>
<header><h1>Revenue Management &amp; Pricing &mdash; decision science</h1>
<div class="sub">Nonlinear price optimization &middot; EMSR capacity allocation &middot; stochastic overbooking &middot; simulation-validated</div></header>
<main>
<div class="kpis">{kpi_html}</div>
<div class="grid">
 <div class="panel"><h2>Profit vs price (nonlinear optimum)</h2><canvas id="c1"></canvas>
   <p style="font-size:13px;color:#5c7086;margin-top:10px">Recovered demand curve; optimal price
   ${po['optimization']['optimal_price']:.0f} matches the true optimum ${po['true_optimal_price']:.0f}.</p></div>
 <div class="panel"><h2>Capacity allocation &mdash; EMSR vs FCFS revenue</h2><canvas id="c2"></canvas>
   <p style="font-size:13px;color:#5c7086;margin-top:10px">Booking limits {ca['booking_limits']} protect
   high-fare seats for a +{ca['revenue_uplift_pct']:.0f}% revenue uplift.</p></div>
</div>
<div class="panel"><h2>Overbooking &mdash; expected profit vs sell limit</h2><canvas id="c3"></canvas>
 <p style="font-size:13px;color:#5c7086;margin-top:10px">Optimal sell limit {ob['optimal_sell_limit']}
 (overbook {ob['overbooking_seats']} seats; expected {ob['expected_denied_at_optimal']:.1f} denied boardings);
 analytic ${ob['expected_profit_optimal']:,.0f} matches simulation ${ob['sim_profit_optimal']:,.0f}.</p></div>
<div class="panel"><h2>Why it maps to the role</h2><div class="note">
 Revenue management, pricing and resource allocation via nonlinear optimization (pricing),
 a seat-protection heuristic (EMSR), and stochastic optimization (overbooking) &mdash; each validated by
 Monte Carlo simulation and graded against a known optimum.
</div></div>
</main>
<footer>Synthetic data &middot; src/revenue_management/build_dashboard.py &middot; optima graded vs ground truth + simulation</footer>
<script>
new Chart(c1,{{type:'line',data:{{labels:{json.dumps(prices)},datasets:[{{label:'profit',data:{json.dumps(profit)},borderColor:'#123a5e',tension:.3,pointRadius:0}}]}},
  options:{{plugins:{{legend:{{display:false}}}},scales:{{x:{{title:{{display:true,text:'price ($)'}}}}}}}}}});
new Chart(c2,{{type:'bar',data:{{labels:['EMSR-b','FCFS (naive)'],datasets:[{{data:[{ca['revenue_emsr']},{ca['revenue_fcfs']}],backgroundColor:['#14804a','#b42318']}}]}},
  options:{{plugins:{{legend:{{display:false}}}},scales:{{y:{{title:{{display:true,text:'expected revenue ($)'}}}}}}}}}});
new Chart(c3,{{type:'line',data:{{labels:{json.dumps(ob_labels)},datasets:[{{label:'expected profit',data:{json.dumps(ob_profit)},borderColor:'#e8a33d',tension:.2,pointRadius:0}}]}},
  options:{{plugins:{{legend:{{display:false}}}},scales:{{x:{{title:{{display:true,text:'seats sold (capacity={R['overbooking']['optimal_sell_limit']-ob['overbooking_seats']})'}}}}}}}}}});
</script></body></html>"""
Path("reports").mkdir(exist_ok=True)
Path("reports/revenue_dashboard.html").write_text(html, encoding="utf-8")
print("Dashboard written to reports/revenue_dashboard.html")
