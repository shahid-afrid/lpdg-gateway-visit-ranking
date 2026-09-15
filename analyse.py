#!/usr/bin/env python3
"""Run the retrospective threshold analysis and generate report inputs."""

from __future__ import annotations

import argparse
from pathlib import Path

from gateway_ranker.charts import create_charts
from gateway_ranker.config import DEFAULT_SIGMA
from gateway_ranker.data_loader import load_data
from gateway_ranker.evaluation import evaluate_thresholds


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--charts", type=Path, default=Path("charts"))
    parser.add_argument(
        "--table", type=Path, default=Path("threshold_comparison.csv")
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    bundle = load_data(args.data)
    comparison, details = evaluate_thresholds(bundle)
    comparison.to_csv(args.table, index=False)
    create_charts(bundle, comparison, details, args.charts)

    default = comparison[comparison["sigma"].eq(DEFAULT_SIGMA)].iloc[0]
    bootstrap = details["bootstrap"]
    meter = details["meter_reads"]

    print(f"Removed {bundle.duplicate_telemetry_rows_removed:,} exact telemetry duplicates.")
    print(f"Analysed {int(default['weeks'])} historical weeks.")
    print(
        "Known outcome coverage among selected slots: "
        f"{default['labelled_coverage']:.1%} "
        f"({int(default['selected_with_definitive_outcome'])} of "
        f"{int(default['selected_slots'])})."
    )
    print(
        f"Known precision at 3 sigma: {default['known_precision']:.1%} "
        f"(gateway-bootstrap 90% range {bootstrap['precision_p05']:.1%} to "
        f"{bootstrap['precision_p95']:.1%})."
    )
    print(
        f"Observed repaired-fault recall: {default['observed_fault_recall']:.1%} "
        f"(gateway-bootstrap 90% range {bootstrap['recall_p05']:.1%} to "
        f"{bootstrap['recall_p95']:.1%})."
    )
    print(
        f"Meter-read evidence covers {int(meter['meter_weeks'])} weeks: selected "
        f"gateways averaged {meter['selected_mean_success']:.1%} success versus "
        f"{meter['other_mean_success']:.1%} for the rest."
    )
    print(f"Wrote {args.table} and four charts to {args.charts}.")
    print("These are retrospective indicators from biased labels, not hidden-ground-truth scores.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

