"""Deterministic implementation of the supplied per-gateway anomaly ranking."""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from .config import (
    BASELINE_DAYS,
    DEFAULT_SIGMA,
    METRICS,
    MIN_BASELINE_HOURS,
    RECENT_DAYS,
    VISITS_PER_WEEK,
)
from .data_loader import active_gateway_ids


def rank_week(
    telemetry: pd.DataFrame,
    gateways: pd.DataFrame,
    monday: dt.date,
    sigma: float = DEFAULT_SIGMA,
) -> pd.DataFrame:
    """Rank active gateways using information strictly before Monday 00:00 UTC."""

    cutoff = pd.Timestamp(monday, tz="UTC")
    start = cutoff - dt.timedelta(days=BASELINE_DAYS)
    recent_start = cutoff - dt.timedelta(days=RECENT_DAYS)
    active = active_gateway_ids(gateways, cutoff)

    window = telemetry.loc[
        telemetry["gateway_id"].isin(active)
        & telemetry["ts"].ge(start)
        & telemetry["ts"].lt(cutoff)
    ].copy()
    if window.empty:
        raise ValueError(f"no telemetry is available before {monday}")

    stats = window.groupby("gateway_id", observed=True)[list(METRICS)].agg(["mean", "std"])
    hours = window.groupby("gateway_id", observed=True)["ts"].nunique()
    eligible = set(hours[hours >= MIN_BASELINE_HOURS].index)
    recent = window.loc[window["ts"].ge(recent_start) & window["gateway_id"].isin(eligible)].copy()

    breach_count = pd.Series(0, index=recent.index, dtype="int64")
    worst_metric = pd.Series("", index=recent.index, dtype="string")
    worst_excess = pd.Series(-np.inf, index=recent.index, dtype="float64")

    for metric in METRICS:
        mean = recent["gateway_id"].map(stats[(metric, "mean")])
        std = recent["gateway_id"].map(stats[(metric, "std")]).replace(0, np.nan)
        z_score = (recent[metric] - mean) / std
        exceeded = z_score.gt(sigma).fillna(False)
        breach_count = breach_count.add(exceeded.astype("int64"), fill_value=0).astype("int64")
        becomes_worst = exceeded & z_score.gt(worst_excess)
        worst_metric = worst_metric.mask(becomes_worst, metric)
        worst_excess = worst_excess.mask(becomes_worst, z_score)

    recent["metric_breaches"] = breach_count
    recent["worst_metric"] = worst_metric
    recent["worst_excess"] = worst_excess.replace(-np.inf, np.nan)

    grouped = recent.groupby("gateway_id", observed=True).agg(
        metric_breaches=("metric_breaches", "sum"),
        observed_recent_hours=("ts", "nunique"),
        peak_sigma=("worst_excess", "max"),
    )
    metric_peaks = (
        recent.loc[recent["worst_excess"].notna()]
        .sort_values(["gateway_id", "worst_excess"], ascending=[True, False])
        .drop_duplicates("gateway_id")
        .set_index("gateway_id")["worst_metric"]
    )
    grouped["worst_metric"] = metric_peaks.reindex(grouped.index).fillna("")

    # Include active gateways with sufficient baseline history even if they had
    # no row in the recent window. Their missing-hour count makes the silence visible.
    grouped = grouped.reindex(sorted(eligible))
    grouped["metric_breaches"] = grouped["metric_breaches"].fillna(0).astype("int64")
    grouped["observed_recent_hours"] = (
        grouped["observed_recent_hours"].fillna(0).astype("int64")
    )
    grouped["worst_metric"] = grouped["worst_metric"].fillna("")
    grouped["missing_recent_hours"] = (
        RECENT_DAYS * 24 - grouped["observed_recent_hours"]
    ).clip(lower=0)
    grouped["score"] = grouped["metric_breaches"].astype(float)

    ranked = (
        grouped.reset_index()
        .rename(columns={"index": "gateway_id"})
        .sort_values(
            ["score", "missing_recent_hours", "peak_sigma", "gateway_id"],
            ascending=[False, False, False, True],
            na_position="last",
            kind="mergesort",
        )
        .reset_index(drop=True)
    )
    ranked["rank"] = np.arange(1, len(ranked) + 1)
    return ranked


def _reason(row: pd.Series, sigma: float) -> str:
    if row["metric_breaches"] > 0:
        metric = str(row["worst_metric"] or "telemetry")
        return (
            f"{int(row['metric_breaches'])} metric breaches above {sigma:g} sigma in the "
            f"previous 7 days; strongest change in {metric}."
        )
    if row["missing_recent_hours"] > 0:
        return (
            f"No metric breach, but {int(row['missing_recent_hours'])} of 168 expected "
            "telemetry hours were absent in the previous 7 days."
        )
    return (
        "No metric breach; included as the next-highest deterministic score "
        "to fill 15 required rows."
    )


def build_predictions(
    telemetry: pd.DataFrame,
    gateways: pd.DataFrame,
    weeks: tuple[dt.date, ...] | list[dt.date],
    sigma: float = DEFAULT_SIGMA,
) -> pd.DataFrame:
    """Build the required five-column output for the supplied weeks."""

    output: list[dict[str, object]] = []
    for monday in weeks:
        ranked = rank_week(telemetry, gateways, monday, sigma=sigma)
        if len(ranked) < VISITS_PER_WEEK:
            raise ValueError(f"only {len(ranked)} eligible gateways are available for {monday}")
        for _, row in ranked.head(VISITS_PER_WEEK).iterrows():
            output.append(
                {
                    "week_start": monday.isoformat(),
                    "rank": int(row["rank"]),
                    "gateway_id": row["gateway_id"],
                    "score": float(row["score"]),
                    "reason": _reason(row, sigma),
                }
            )
    return pd.DataFrame(
        output,
        columns=["week_start", "rank", "gateway_id", "score", "reason"],
    )
