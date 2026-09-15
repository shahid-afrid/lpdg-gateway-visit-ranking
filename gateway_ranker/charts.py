"""Charts designed for the operations-manager analysis report."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .config import COST_PER_FAULT_WEEK_EUR, COST_PER_VISIT_EUR, DEFAULT_SIGMA
from .data_loader import DataBundle
from .ranking import rank_week


def _finish(fig: plt.Figure, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def create_charts(
    bundle: DataBundle,
    comparison: pd.DataFrame,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    ax = axes[0]
    recall = comparison["observed_fault_recall"] * 100
    lower = (comparison["observed_fault_recall"] - comparison["recall_p05"]) * 100
    upper = (comparison["recall_p95"] - comparison["observed_fault_recall"]) * 100
    ax.errorbar(
        comparison["sigma"],
        recall,
        yerr=[lower, upper],
        marker="o",
        capsize=4,
        color="#2563EB",
    )
    ax.axvline(DEFAULT_SIGMA, color="#D97706", linestyle="--", label="Current threshold")
    ax.set(
        title="Observed repairs selected",
        xlabel="Anomaly threshold (sigma)",
        ylabel="Observed repaired faults selected (%)",
        ylim=(0, max(10, comparison["recall_p95"].max() * 115)),
    )
    ax.legend(frameon=False)

    ax = axes[1]
    ax.plot(
        comparison["sigma"],
        comparison["labelled_proxy_total_cost_eur"],
        marker="o",
        color="#0F766E",
    )
    ax.axvline(DEFAULT_SIGMA, color="#D97706", linestyle="--")
    ax.set(
        title="Incomplete historical cost proxy",
        xlabel="Anomaly threshold (sigma)",
        ylabel="Average weekly proxy cost (EUR)",
    )
    ax.text(
        0.02,
        0.04,
        "Uses observed repairs only; not the official cost",
        transform=ax.transAxes,
        fontsize=9,
        color="#555555",
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.8},
    )
    _finish(fig, output_dir / "threshold_evidence_and_cost.png")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(
        comparison["sigma"],
        comparison["top15_overlap_with_3sigma"] * 100,
        marker="o",
        color="#2563EB",
    )
    ax.set(
        title="How much the weekly visit list changes when the threshold moves",
        xlabel="Anomaly threshold (sigma)",
        ylabel="Average overlap with the 3-sigma top 15 (%)",
        ylim=(0, 105),
    )
    _finish(fig, output_dir / "threshold_selection_stability.png")

    first_week = dt.date(2026, 2, 2)
    top = rank_week(bundle.telemetry, bundle.gateways, first_week).head(15).sort_values("score")
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(top["gateway_id"], top["score"], color="#0F766E")
    ax.set(
        title="Recommended visits for 2 February 2026",
        xlabel="Metric breaches above the 3-sigma threshold",
        ylabel="Gateway",
    )
    _finish(fig, output_dir / "first_week_top15.png")

    weeks = list(range(1, 9))
    costs = [week * COST_PER_FAULT_WEEK_EUR + COST_PER_VISIT_EUR for week in weeks]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(weeks, costs, color="#B91C1C")
    ax.set(
        title="Each week of delayed attention adds EUR 600 to a persistent fault",
        xlabel="Week in which the first visit occurs",
        ylabel="Episode cost including one EUR 380 visit",
        xticks=weeks,
    )
    _finish(fig, output_dir / "fault_delay_cost.png")
