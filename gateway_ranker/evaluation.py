"""Retrospective evidence for threshold choice, with explicit coverage limits."""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from .config import (
    COST_PER_FAULT_WEEK_EUR,
    COST_PER_VISIT_EUR,
    DEFAULT_SIGMA,
    EVALUATION_WEEKS,
    THRESHOLDS,
    VISITS_PER_WEEK,
)
from .data_loader import DataBundle
from .ranking import rank_week

FAULT_FIXED = "Fehler behoben"
NO_FAULT_FOUND = "Kein Fehler gefunden"
NO_ACCESS = "Kein Zugang"


def episode_cost(episode_weeks: int, first_visit_week: int | None = None) -> int:
    """Return the brief's cost for one continuous fault episode.

    ``first_visit_week`` is one-based and the fault cost includes that week.
    Later visits in the same episode do not change this value.
    """

    if episode_weeks < 1:
        raise ValueError("episode_weeks must be at least one")
    if first_visit_week is not None and not 1 <= first_visit_week <= episode_weeks:
        raise ValueError("first_visit_week must fall inside the episode")
    charged_weeks = episode_weeks if first_visit_week is None else first_visit_week
    visit_cost = 0 if first_visit_week is None else COST_PER_VISIT_EUR
    return charged_weeks * COST_PER_FAULT_WEEK_EUR + visit_cost


def _weekly_visit_labels(visits: pd.DataFrame, monday: dt.date) -> pd.DataFrame:
    """Create at most one retrospective outcome per gateway for a visit week."""

    start = pd.Timestamp(monday)
    end = start + dt.timedelta(days=7)
    week = visits.loc[visits["visited_on"].ge(start) & visits["visited_on"].lt(end)].copy()
    if week.empty:
        return pd.DataFrame(columns=["gateway_id", "outcome"])

    # A repair is the strongest available indication. No access remains unknown.
    priority = {FAULT_FIXED: 2, NO_FAULT_FOUND: 1, NO_ACCESS: 0}
    week["outcome_priority"] = week["outcome"].map(priority).fillna(-1)
    return (
        week.sort_values(["gateway_id", "outcome_priority"], ascending=[True, False])
        .drop_duplicates("gateway_id")[["gateway_id", "outcome"]]
        .reset_index(drop=True)
    )


def _evaluate_one_threshold(
    bundle: DataBundle,
    sigma: float,
    weeks: tuple[dt.date, ...] = EVALUATION_WEEKS,
) -> tuple[dict[str, float], pd.DataFrame, dict[dt.date, set[str]]]:
    labelled_rows: list[pd.DataFrame] = []
    selections: dict[dt.date, set[str]] = {}
    repeat_count = 0
    previous: set[str] = set()

    for monday in weeks:
        ranking = rank_week(bundle.telemetry, bundle.gateways, monday, sigma=sigma)
        selected = set(ranking.head(VISITS_PER_WEEK)["gateway_id"])
        selections[monday] = selected
        if previous:
            repeat_count += len(selected & previous)
        previous = selected

        labels = _weekly_visit_labels(bundle.field_visits, monday)
        if labels.empty:
            continue
        labels["week_start"] = monday
        labels["selected"] = labels["gateway_id"].isin(selected)
        labelled_rows.append(labels)

    labelled = (
        pd.concat(labelled_rows, ignore_index=True)
        if labelled_rows
        else pd.DataFrame(columns=["gateway_id", "outcome", "week_start", "selected"])
    )
    definitive = labelled[labelled["outcome"].isin([FAULT_FIXED, NO_FAULT_FOUND])]
    selected_definitive = definitive[definitive["selected"]]
    fault_rows = definitive[definitive["outcome"].eq(FAULT_FIXED)]

    selected_faults = int(selected_definitive["outcome"].eq(FAULT_FIXED).sum())
    selected_no_fault = int(selected_definitive["outcome"].eq(NO_FAULT_FOUND).sum())
    observed_faults = int(len(fault_rows))
    missed_observed_faults = int((~fault_rows["selected"]).sum())
    weeks_count = len(weeks)

    metrics = {
        "sigma": float(sigma),
        "weeks": float(weeks_count),
        "selected_slots": float(weeks_count * VISITS_PER_WEEK),
        "selected_with_definitive_outcome": float(len(selected_definitive)),
        "labelled_coverage": len(selected_definitive) / (weeks_count * VISITS_PER_WEEK),
        "selected_fault_fixed": float(selected_faults),
        "selected_no_fault_found": float(selected_no_fault),
        "known_precision": (
            selected_faults / len(selected_definitive) if len(selected_definitive) else np.nan
        ),
        "observed_faults": float(observed_faults),
        "observed_fault_recall": (
            selected_faults / observed_faults if observed_faults else np.nan
        ),
        "avg_weekly_repeat_selections": repeat_count / max(1, weeks_count - 1),
        "fixed_weekly_visit_cost_eur": float(VISITS_PER_WEEK * COST_PER_VISIT_EUR),
        "labelled_proxy_missed_cost_eur": (
            missed_observed_faults / weeks_count * COST_PER_FAULT_WEEK_EUR
        ),
    }
    metrics["labelled_proxy_total_cost_eur"] = (
        metrics["fixed_weekly_visit_cost_eur"]
        + metrics["labelled_proxy_missed_cost_eur"]
    )
    return metrics, definitive, selections


def _cluster_bootstrap(
    definitive: pd.DataFrame,
    samples: int = 1_000,
    seed: int = 2026,
) -> dict[str, float]:
    """Resample gateways with their full histories kept together."""

    gateways = definitive["gateway_id"].drop_duplicates().to_numpy()
    if len(gateways) < 2:
        return {
            "precision_p05": np.nan,
            "precision_p95": np.nan,
            "recall_p05": np.nan,
            "recall_p95": np.nan,
        }

    grouped = {gateway: definitive[definitive["gateway_id"].eq(gateway)] for gateway in gateways}
    rng = np.random.default_rng(seed)
    precisions: list[float] = []
    recalls: list[float] = []
    for _ in range(samples):
        draw = rng.choice(gateways, size=len(gateways), replace=True)
        sample = pd.concat([grouped[gateway] for gateway in draw], ignore_index=True)
        selected = sample[sample["selected"]]
        faults = sample[sample["outcome"].eq(FAULT_FIXED)]
        if len(selected):
            precisions.append(float(selected["outcome"].eq(FAULT_FIXED).mean()))
        if len(faults):
            recalls.append(float(faults["selected"].mean()))

    return {
        "precision_p05": float(np.quantile(precisions, 0.05)),
        "precision_p95": float(np.quantile(precisions, 0.95)),
        "recall_p05": float(np.quantile(recalls, 0.05)),
        "recall_p95": float(np.quantile(recalls, 0.95)),
    }


def _meter_read_evidence(
    bundle: DataBundle,
    selections: dict[dt.date, set[str]],
) -> dict[str, float]:
    differences: list[float] = []
    selected_rates: list[float] = []
    other_rates: list[float] = []
    for monday, selected in selections.items():
        week = bundle.meter_reads[
            bundle.meter_reads["week_start"].eq(pd.Timestamp(monday))
        ]
        if week.empty:
            continue
        selected_week = week[week["gateway_id"].isin(selected)]["success_rate"]
        other_week = week[~week["gateway_id"].isin(selected)]["success_rate"]
        if selected_week.empty or other_week.empty:
            continue
        selected_rates.extend(selected_week.tolist())
        other_rates.extend(other_week.tolist())
        differences.append(float(selected_week.mean() - other_week.mean()))

    return {
        "meter_weeks": float(len(differences)),
        "selected_mean_success": float(np.mean(selected_rates)) if selected_rates else np.nan,
        "other_mean_success": float(np.mean(other_rates)) if other_rates else np.nan,
        "weekly_difference_min": float(np.min(differences)) if differences else np.nan,
        "weekly_difference_max": float(np.max(differences)) if differences else np.nan,
    }


def evaluate_thresholds(bundle: DataBundle) -> tuple[pd.DataFrame, dict[str, object]]:
    """Compare thresholds and return detailed evidence for the default threshold."""

    evaluations: list[dict[str, float]] = []
    selection_sets: dict[float, dict[dt.date, set[str]]] = {}
    default_labels = pd.DataFrame()

    for sigma in THRESHOLDS:
        metrics, labels, selections = _evaluate_one_threshold(bundle, sigma)
        metrics.update(_cluster_bootstrap(labels))
        evaluations.append(metrics)
        selection_sets[sigma] = selections
        if sigma == DEFAULT_SIGMA:
            default_labels = labels

    comparison = pd.DataFrame(evaluations)
    reference = selection_sets[DEFAULT_SIGMA]
    stability = []
    for sigma in comparison["sigma"]:
        overlaps = [
            len(selection_sets[float(sigma)][week] & reference[week]) / VISITS_PER_WEEK
            for week in EVALUATION_WEEKS
        ]
        stability.append(float(np.mean(overlaps)))
    comparison["top15_overlap_with_3sigma"] = stability

    details: dict[str, object] = {
        "bootstrap": {
            key: float(
                comparison.loc[comparison["sigma"].eq(DEFAULT_SIGMA), key].iloc[0]
            )
            for key in ("precision_p05", "precision_p95", "recall_p05", "recall_p95")
        },
        "meter_reads": _meter_read_evidence(bundle, reference),
        "default_labels": default_labels,
        "default_selections": reference,
    }
    return comparison, details
