"""Data mining for planning: ABC/XYZ segmentation + a predictive fast-mover model.

ABC/XYZ is the classic demand data-mining frame:
  * ABC - Pareto by annual revenue (A = top 80% of revenue, B = next 15%, C = last 5%).
  * XYZ - demand predictability by coefficient of variation (X stable, Y variable,
    Z erratic). Together they tell planners where to focus forecasting + inventory.

The predictive model forecasts product behavior: will a SKU be a FAST MOVER next
period (top-quartile demand)? A gradient-boosted classifier is trained on product
attributes + demand history and graded by ROC-AUC, with its drivers reported.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split


def abc_classify(skus: pd.DataFrame) -> pd.DataFrame:
    df = skus.sort_values("annual_revenue", ascending=False).copy()
    total = df["annual_revenue"].sum()
    df["cum_share"] = df["annual_revenue"].cumsum() / total
    def _abc(c):
        return "A" if c <= 0.80 else ("B" if c <= 0.95 else "C")
    df["abc"] = df["cum_share"].apply(_abc)
    return df


def xyz_classify(skus: pd.DataFrame, demand: pd.DataFrame) -> pd.Series:
    stats = demand.groupby("sku")["demand"].agg(["mean", "std"])
    cv = (stats["std"] / stats["mean"]).fillna(0)
    def _xyz(v):
        return "X" if v <= 0.25 else ("Y" if v <= 0.50 else "Z")
    return cv.apply(_xyz).rename("xyz")


def segment(skus: pd.DataFrame, demand: pd.DataFrame) -> dict:
    abc = abc_classify(skus)
    xyz = xyz_classify(skus, demand)
    merged = abc.merge(xyz, left_on="sku", right_index=True)

    a_rev_share = merged.loc[merged["abc"] == "A", "annual_revenue"].sum() / merged["annual_revenue"].sum()
    counts = merged.groupby(["abc", "xyz"]).size().unstack(fill_value=0)
    abc_counts = merged["abc"].value_counts().to_dict()
    return {
        "abc_counts": {k: int(v) for k, v in abc_counts.items()},
        "xyz_counts": {k: int(v) for k, v in xyz.value_counts().to_dict().items()},
        "a_class_revenue_share": round(float(a_rev_share), 3),
        "a_class_sku_share": round(float((merged["abc"] == "A").mean()), 3),
        "matrix": {f"{a}{x}": int(counts.loc[a, x]) if (a in counts.index and x in counts.columns) else 0
                   for a in ["A", "B", "C"] for x in ["X", "Y", "Z"]},
    }


def predict_fast_movers(skus: pd.DataFrame, demand: pd.DataFrame, seed=0) -> dict:
    """Classify SKUs likely to be top-quartile demand (fast movers) next period."""
    n_weeks = demand["week"].max() + 1
    split = n_weeks - 13
    hist = demand[demand["week"] < split]
    future = demand[demand["week"] >= split]

    feat = hist.groupby("sku")["demand"].agg(
        hist_mean="mean", hist_std="std", hist_max="max").fillna(0)
    # recent trend: slope of last-26-week mean vs prior
    recent = hist[hist["week"] >= split - 26].groupby("sku")["demand"].mean()
    older = hist[hist["week"] < split - 26].groupby("sku")["demand"].mean()
    feat["recent_trend"] = (recent - older).reindex(feat.index).fillna(0)

    X = skus.set_index("sku").join(feat)
    X["cv"] = (X["hist_std"] / X["hist_mean"]).replace([np.inf, -np.inf], 0).fillna(0)
    fut_mean = future.groupby("sku")["demand"].mean()
    y = (fut_mean >= fut_mean.quantile(0.75)).astype(int).reindex(X.index).fillna(0)

    cols = ["unit_cost", "price", "lead_time_wk", "hist_mean", "hist_std",
            "hist_max", "recent_trend", "cv"]
    Xm = X[cols].fillna(0).to_numpy()
    Xtr, Xte, ytr, yte = train_test_split(Xm, y.to_numpy(), test_size=0.3,
                                          random_state=seed, stratify=y)
    clf = GradientBoostingClassifier(random_state=seed, n_estimators=150, max_depth=3)
    clf.fit(Xtr, ytr)
    auc = roc_auc_score(yte, clf.predict_proba(Xte)[:, 1])
    imp = pd.Series(clf.feature_importances_, index=cols).sort_values(ascending=False)
    return {
        "auc": round(float(auc), 3),
        "n_skus": int(len(X)),
        "fast_mover_rate": round(float(y.mean()), 3),
        "top_drivers": imp.index[:3].tolist(),
    }
