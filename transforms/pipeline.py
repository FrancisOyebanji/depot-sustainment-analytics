"""PySpark data pipeline — Palantir Foundry Code Repositories style.

In Foundry these functions are decorated with @transform_df and wired by input/
output dataset paths; here they are plain PySpark functions so the same logic
runs locally on a SparkSession and in Foundry unchanged. The pipeline is the
raw -> clean -> analytical progression:

  clean_work_orders   : enforce schema, drop/flag fidelity issues
  work_center_load    : aggregate processing demand per work center
  work_order_cycle    : per-work-order cycle time (span across steps)

Run standalone:  python transforms/pipeline.py
Foundry mapping:  each function -> a @transform_df with typed dataset I/O.
"""
from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types as T

VALID_WORK_CENTERS = ["Disassembly", "Inspection", "Repair", "Assembly", "Test"]

SCHEMA = T.StructType([
    T.StructField("work_order", T.StringType()),
    T.StructField("asset_type", T.StringType()),
    T.StructField("priority", T.StringType()),
    T.StructField("step_seq", T.IntegerType()),
    T.StructField("work_center", T.StringType()),
    T.StructField("arrival_ts", T.StringType()),
    T.StructField("processing_hours", T.DoubleType()),
])


def read_raw(spark: SparkSession, path: str) -> DataFrame:
    return spark.read.csv(path, header=True, schema=SCHEMA)


def clean_work_orders(raw: DataFrame) -> DataFrame:
    """Silver-equivalent clean: parse timestamps, drop invalid rows, keep provenance."""
    return (raw
        .withColumn("arrival_ts", F.to_timestamp("arrival_ts"))
        .filter(F.col("arrival_ts").isNotNull())                       # drop missing ts
        .filter(F.col("processing_hours") > 0)                         # drop negative/zero
        .filter(F.col("work_center").isin(VALID_WORK_CENTERS))         # drop orphan wc
        .filter(F.col("step_seq").between(1, len(VALID_WORK_CENTERS)))  # drop out-of-seq
        .dropDuplicates(["work_order", "step_seq"]))


def work_center_load(clean: DataFrame) -> DataFrame:
    """Total and mean processing demand per work center — input to capacity analysis."""
    return (clean.groupBy("work_center")
        .agg(F.count("*").alias("n_steps"),
             F.round(F.sum("processing_hours"), 1).alias("total_hours"),
             F.round(F.mean("processing_hours"), 2).alias("mean_hours"),
             F.round(F.expr("percentile_approx(processing_hours, 0.85)"), 2).alias("p85_hours"))
        .orderBy(F.desc("total_hours")))


def work_order_cycle(clean: DataFrame) -> DataFrame:
    """Per-work-order total processing hours and step count (cycle-time input)."""
    return (clean.groupBy("work_order", "asset_type", "priority")
        .agg(F.round(F.sum("processing_hours"), 1).alias("total_processing_hours"),
             F.count("*").alias("steps_recorded")))


def run(spark: SparkSession, raw_path: str) -> dict[str, DataFrame]:
    raw = read_raw(spark, raw_path)
    clean = clean_work_orders(raw).cache()
    return {"raw": raw, "clean": clean,
            "work_center_load": work_center_load(clean),
            "work_order_cycle": work_order_cycle(clean)}


if __name__ == "__main__":
    import os
    os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
    spark = (SparkSession.builder.master("local[*]").appName("depot_pipeline")
             .config("spark.ui.enabled", "false").config("spark.sql.shuffle.partitions", "4")
             .getOrCreate())
    spark.sparkContext.setLogLevel("ERROR")
    out = run(spark, "data/work_orders.csv")
    print(f"raw steps: {out['raw'].count()},  clean steps: {out['clean'].count()}")
    out["work_center_load"].show()
    spark.stop()
