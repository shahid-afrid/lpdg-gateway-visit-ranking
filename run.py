#!/usr/bin/env python3
"""Generate and validate the eight-week gateway visit submission."""

from __future__ import annotations

import argparse
from pathlib import Path

from gateway_ranker.config import DEFAULT_SIGMA, SCORED_WEEKS
from gateway_ranker.data_loader import load_data
from gateway_ranker.ranking import build_predictions
from validate_submission import validate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"), help="supplied data folder")
    parser.add_argument(
        "--out", type=Path, default=Path("predictions.csv"), help="submission CSV path"
    )
    parser.add_argument(
        "--sigma", type=float, default=DEFAULT_SIGMA, help="anomaly threshold"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.sigma <= 0:
        raise SystemExit("--sigma must be greater than zero")

    bundle = load_data(args.data)
    predictions = build_predictions(
        bundle.telemetry,
        bundle.gateways,
        SCORED_WEEKS,
        sigma=args.sigma,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.out.with_suffix(args.out.suffix + ".tmp")
    predictions.to_csv(temporary, index=False)
    temporary.replace(args.out)

    problems = validate(args.out)
    if problems:
        print(f"{args.out}: validation failed")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(f"Removed {bundle.duplicate_telemetry_rows_removed:,} exact telemetry duplicates.")
    print(
        f"Wrote {len(predictions)} rows for {len(SCORED_WEEKS)} weeks to {args.out}."
    )
    print("Submission validation: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

