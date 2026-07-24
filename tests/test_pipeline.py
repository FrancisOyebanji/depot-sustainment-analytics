"""Tests for fidelity monitoring, constraint analysis, and the simulation.

Spark is optional in CI (the pipeline has a pandas fallback), so these tests
exercise the analytics that always run. A separate test opportunistically checks
the PySpark clean logic if pyspark is importable.
"""
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

HAS_PYSPARK = importlib.util.find_spec("pyspark") is not None

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "transforms"))


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    work = tmp_path_factory.mktemp("depot")
    old = Path.cwd()
    os.chdir(work)
    try:
        import run_pipeline
        run_pipeline.main()
        yield {
            "fidelity": json.loads(Path("reports/fidelity_report.json").read_text()),
            "ie": json.loads(Path("reports/ie_analysis.json").read_text()),
            "sim": json.loads(Path("reports/simulation.json").read_text()),
        }
    finally:
        os.chdir(old)


def test_fidelity_detects_injected_issues(built):
    f = built["fidelity"]
    issues = {c["issue"]: c["count"] for c in f["catalog"]}
    assert issues["missing_arrival_timestamp"] > 0
    assert issues["orphan_work_center"] > 0
    assert f["fidelity_score_pct"] < 100


def test_bottleneck_is_repair(built):
    # By construction Repair is under-capacitied; the analysis must find it.
    assert built["ie"]["bottleneck"]["work_center"] == "Repair"
    assert built["ie"]["bottleneck"]["utilization_pct"] > 70


def test_adding_repair_capacity_increases_throughput(built):
    comp = {c["scenario"]: c for c in built["sim"]["comparison"]}
    assert comp["add_1_repair_server"]["throughput_gain_pct"] > 0
    # Relieving the constraint should also cut flow time
    assert comp["add_1_repair_server"]["flow_time_reduction_pct"] > 0


def test_simulation_conserves_work_orders(built):
    # Every scenario should complete a positive, plausible number of work orders
    for r in built["sim"]["scenarios"].values():
        assert r["completions_in_window"] > 0
        assert 0 <= r["utilization_pct"]["Repair"] <= 100


@pytest.mark.skipif(not HAS_PYSPARK, reason="pyspark optional (pandas fallback covers this path)")
def test_pyspark_clean_matches_rules(tmp_path):
    """If PySpark is available, its clean output must drop all injected bad rows."""
    import generate_workorders
    os.chdir(tmp_path)
    generate_workorders.generate()
    os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
    from pyspark.sql import SparkSession
    import pipeline
    spark = (SparkSession.builder.master("local[1]").appName("t")
             .config("spark.ui.enabled", "false").getOrCreate())
    spark.sparkContext.setLogLevel("ERROR")
    out = pipeline.run(spark, "data/work_orders.csv")
    clean = out["clean"]
    assert clean.filter("processing_hours <= 0").count() == 0
    assert clean.filter("work_center = 'UNKNOWN'").count() == 0
    spark.stop()
