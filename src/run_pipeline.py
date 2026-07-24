"""End-to-end orchestration.

Runs the PySpark pipeline if available; otherwise falls back to a pandas
implementation of the identical clean logic so the analysis always executes.
Then runs fidelity monitoring, IE analysis, simulation, and the briefing.
"""
from __future__ import annotations

import os
from pathlib import Path

import briefing
import data_fidelity
import generate_workorders
import industrial_engineering
import simulation

VALID = ["Disassembly", "Inspection", "Repair", "Assembly", "Test"]


def clean_with_spark() -> bool:
    try:
        import sys
        sys.path.insert(0, "transforms")
        os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
        from pyspark.sql import SparkSession
        import pipeline
        spark = (SparkSession.builder.master("local[*]").appName("depot")
                 .config("spark.ui.enabled", "false")
                 .config("spark.sql.shuffle.partitions", "4").getOrCreate())
        spark.sparkContext.setLogLevel("ERROR")
        out = pipeline.run(spark, "data/work_orders.csv")
        out["clean"].toPandas().to_csv("data/work_orders_clean.csv", index=False)
        n_raw, n_clean = out["raw"].count(), out["clean"].count()
        spark.stop()
        print(f"   [PySpark] raw {n_raw} -> clean {n_clean}")
        return True
    except Exception as e:
        print(f"   [PySpark unavailable: {type(e).__name__}] using pandas fallback")
        return False


def clean_with_pandas() -> None:
    import pandas as pd
    df = pd.read_csv("data/work_orders.csv")
    df["arrival_ts"] = pd.to_datetime(df["arrival_ts"], errors="coerce")
    df = df[df["arrival_ts"].notna()]
    df = df[pd.to_numeric(df["processing_hours"], errors="coerce") > 0]
    df = df[df["work_center"].isin(VALID)]
    df = df[df["step_seq"].between(1, len(VALID))]
    df = df.drop_duplicates(["work_order", "step_seq"])
    df.to_csv("data/work_orders_clean.csv", index=False)
    print(f"   [pandas] clean rows: {len(df)}")


def main() -> None:
    Path("data").mkdir(exist_ok=True)
    print("=== 1/5 Generating synthetic MRO work orders ===")
    generate_workorders.generate()
    print("=== 2/5 Data-fidelity scan ===")
    fid = data_fidelity.scan()
    print(f"   fidelity score {fid['fidelity_score_pct']}%, {fid['total_issues_found']} issues")
    print("=== 3/5 Cleaning pipeline ===")
    if not clean_with_spark():
        clean_with_pandas()
    print("=== 4/5 Industrial-engineering / constraint analysis ===")
    ie = industrial_engineering.analyze()
    print(f"   bottleneck: {ie['bottleneck']['work_center']} "
          f"@ {ie['bottleneck']['utilization_pct']}% utilization")
    print("=== 5/5 Discrete-event simulation (what-if scenarios) ===")
    sim = simulation.run_scenarios()
    for c in sim["comparison"]:
        print(f"   {c['scenario']:<24} thru {c['throughput_per_day']}/day "
              f"(+{c['throughput_gain_pct']}%)")
    briefing.generate()


if __name__ == "__main__":
    main()
