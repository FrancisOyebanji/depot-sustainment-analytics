"""Supply Chain Planning dashboard from reports/supply_chain_results.json."""
from __future__ import annotations

import json
from pathlib import Path

R = json.loads(Path("reports/supply_chain_results.json").read_text())
fc, inv, net, seg, fast = (R["forecasting"], R["inventory"], R["network"],
                           R["segmentation"], R["fast_mover_model"])

matrix = seg["matrix"]
mat_rows = "".join(
    "<tr><th>{}</th>{}</tr>".format(
        a, "".join(f"<td>{matrix.get(f'{a}{x}',0)}</td>" for x in ['X', 'Y', 'Z']))
    for a in ['A', 'B', 'C'])

kpis = [
    ("Forecast WAPE (ML)", f"{fc['wape_ml']:.2f}"),
    ("vs naive baseline", f"+{fc['improvement_vs_naive_pct']:.0f}%"),
    ("Inventory fill rate", f"{inv['mean_achieved_fill_rate']*100:.1f}%"),
    ("Network savings", f"{net['savings_vs_all_open_pct']:.1f}%"),
    ("A-class revenue share", f"{seg['a_class_revenue_share']*100:.0f}%"),
    ("Fast-mover AUC", f"{fast['auc']:.2f}"),
]
kpi_html = "".join(
    f"<div class='kpi'><div class='l'>{l}</div><div class='v'>{v}</div></div>" for l, v in kpis)

abc = seg["abc_counts"]
abc_labels = ["A", "B", "C"]
abc_vals = [abc.get(k, 0) for k in abc_labels]

html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Supply Chain Planning</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
 body{{font-family:'Segoe UI',system-ui,sans-serif;background:#f4f6f8;color:#14232e;margin:0}}
 header{{background:#17405e;color:#fff;padding:16px 30px}} h1{{font-size:20px;margin:0}}
 .sub{{color:#bcd3e6;font-size:13px}}
 main{{max-width:1120px;margin:22px auto;padding:0 18px}}
 .kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:14px;margin-bottom:20px}}
 .kpi{{background:#fff;border:1px solid #e1e8ee;border-radius:12px;padding:16px}}
 .kpi .l{{color:#5d7384;font-size:13px}}.kpi .v{{font-size:22px;font-weight:700;margin-top:4px;color:#17405e}}
 .grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
 .panel{{background:#fff;border:1px solid #e1e8ee;border-radius:12px;padding:18px;margin-bottom:18px}}
 .panel h2{{font-size:15px;margin:0 0 12px}} canvas{{max-height:270px}}
 table{{width:100%;border-collapse:collapse;font-size:13px}} th,td{{padding:7px 9px;border-bottom:1px solid #eef2f5;text-align:center}}
 th{{color:#5d7384}}
 .note{{background:#eaf1f7;border-left:4px solid #17405e;padding:10px 14px;border-radius:6px;font-size:14px}}
 @media(max-width:800px){{.grid{{grid-template-columns:1fr}}}}
 footer{{color:#5d7384;font-size:12px;text-align:center;margin:24px 0}}
</style></head><body>
<header><h1>Supply Chain Planning COE &mdash; forecasting, inventory, network & demand mining</h1>
<div class="sub">Demand forecasting &middot; inventory optimization &middot; network design &middot; ABC/XYZ + predictive model</div></header>
<main>
<div class="kpis">{kpi_html}</div>
<div class="grid">
 <div class="panel"><h2>ABC segmentation &mdash; SKU count by class</h2><canvas id="c1"></canvas></div>
 <div class="panel"><h2>Network design &mdash; cost (lower is better)</h2><canvas id="c2"></canvas></div>
</div>
<div class="grid">
 <div class="panel"><h2>ABC &times; XYZ matrix (SKU counts)</h2>
   <table><tr><th>ABC &darr; / XYZ &rarr;</th><th>X (stable)</th><th>Y (variable)</th><th>Z (erratic)</th></tr>{mat_rows}</table>
   <p style="font-size:13px;color:#5d7384;margin-top:10px">A-class holds {seg['a_class_revenue_share']*100:.0f}% of revenue in
   {seg['a_class_sku_share']*100:.0f}% of SKUs &mdash; where tight forecasting + inventory control pays off most.</p></div>
 <div class="panel"><h2>Forecast accuracy (backtest)</h2><canvas id="c3"></canvas>
   <p style="font-size:13px;color:#5d7384;margin-top:10px">ML WAPE {fc['wape_ml']:.2f} vs seasonal-naive {fc['wape_naive']:.2f}
   on a held-out quarter; bias {fc['bias_ml']:+.3f}.</p></div>
</div>
<div class="panel"><h2>Planning recommendation</h2><div class="note">
 Open DCs {net['optimum']['open_dcs']} (saves {net['savings_vs_all_open_pct']:.1f}% vs all-open, heuristic verified optimal);
 hold safety stock sized to a 95% service level (achieved fill {inv['mean_achieved_fill_rate']*100:.1f}%);
 focus the ML forecast + tight inventory on A/X&ndash;Y SKUs; watch predicted fast movers (AUC {fast['auc']:.2f}) for stock-up.
</div></div>
</main>
<footer>Synthetic data &middot; src/supply_chain/build_dashboard.py &middot; forecast/network/inventory graded vs known truth</footer>
<script>
new Chart(c1,{{type:'bar',data:{{labels:{json.dumps(abc_labels)},datasets:[{{data:{json.dumps(abc_vals)},backgroundColor:['#17405e','#2f7bb0','#9bc1dc']}}]}},
  options:{{plugins:{{legend:{{display:false}}}}}}}});
new Chart(c2,{{type:'bar',data:{{labels:['All DCs open','Optimized network'],datasets:[{{data:[{net['cost_all_open']},{net['optimum']['cost']}],backgroundColor:['#b42318','#14804a']}}]}},
  options:{{plugins:{{legend:{{display:false}}}}}}}});
new Chart(c3,{{type:'bar',data:{{labels:['ML model','Seasonal-naive'],datasets:[{{label:'WAPE',data:[{fc['wape_ml']},{fc['wape_naive']}],backgroundColor:['#14804a','#9aa7ad']}}]}},
  options:{{plugins:{{legend:{{display:false}}}},scales:{{y:{{min:0}}}}}}}});
</script></body></html>"""
Path("reports").mkdir(exist_ok=True)
Path("reports/supply_chain_dashboard.html").write_text(html, encoding="utf-8")
print("Dashboard written to reports/supply_chain_dashboard.html")
