"""Small set of documented settings used by prediction and analysis."""

from __future__ import annotations

import datetime as dt

METRICS = ("offline_duration_sec", "disconnection_cnt", "reboot_cnt")

BASELINE_DAYS = 28
RECENT_DAYS = 7
DEFAULT_SIGMA = 3.0
MIN_BASELINE_HOURS = 7 * 24

VISITS_PER_WEEK = 15
COST_PER_VISIT_EUR = 380
COST_PER_FAULT_WEEK_EUR = 600

SCORED_WEEKS = tuple(
    dt.date(2026, 2, 2) + dt.timedelta(days=7 * offset)
    for offset in range(8)
)

THRESHOLDS = (2.0, 2.5, 3.0, 3.5, 4.0)

# These weeks have a full 28-day telemetry history and occur before the
# eight-week scored window. They are used for retrospective evidence only.
EVALUATION_WEEKS = tuple(
    dt.date(2025, 9, 1) + dt.timedelta(days=7 * offset)
    for offset in range(22)
)
