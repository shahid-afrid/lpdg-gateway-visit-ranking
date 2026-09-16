from __future__ import annotations

import datetime as dt

import pandas as pd

from gateway_ranker.ranking import rank_week


def _fixtures() -> tuple[pd.DataFrame, pd.DataFrame]:
    hours = pd.date_range("2026-01-05", "2026-02-01 23:00", freq="h", tz="UTC")
    rows = []
    for gateway_id in ["AAAAAAAAAAAA", "BBBBBBBBBBBB"]:
        for ts in hours:
            value = 0
            if gateway_id == "BBBBBBBBBBBB" and ts == pd.Timestamp("2026-02-01 22:00", tz="UTC"):
                value = 20
            rows.append(
                {
                    "gateway_id": gateway_id,
                    "ts": ts,
                    "offline_duration_sec": value,
                    "disconnection_cnt": 0,
                    "reboot_cnt": 0,
                }
            )
    telemetry = pd.DataFrame(rows)
    gateways = pd.DataFrame(
        {
            "gateway_id": ["AAAAAAAAAAAA", "BBBBBBBBBBBB"],
            "installed_on": pd.to_datetime(["2025-01-01", "2025-01-01"]),
            "decommissioned_on": pd.to_datetime([None, None]),
        }
    )
    return telemetry, gateways


def test_recent_anomaly_ranks_first() -> None:
    telemetry, gateways = _fixtures()
    result = rank_week(telemetry, gateways, dt.date(2026, 2, 2), sigma=3.0)
    assert result.iloc[0]["gateway_id"] == "BBBBBBBBBBBB"
    assert result.iloc[0]["metric_breaches"] == 1


def test_cutoff_excludes_monday_data() -> None:
    telemetry, gateways = _fixtures()
    future = telemetry.iloc[[0]].copy()
    future["gateway_id"] = "AAAAAAAAAAAA"
    future["ts"] = pd.Timestamp("2026-02-02 00:00", tz="UTC")
    future["offline_duration_sec"] = 10_000
    changed = pd.concat([telemetry, future], ignore_index=True)

    original = rank_week(telemetry, gateways, dt.date(2026, 2, 2), sigma=3.0)
    with_future = rank_week(changed, gateways, dt.date(2026, 2, 2), sigma=3.0)
    columns = ["gateway_id", "score", "rank"]
    pd.testing.assert_frame_equal(original[columns], with_future[columns])


def test_ties_are_broken_by_gateway_id() -> None:
    telemetry, gateways = _fixtures()
    telemetry.loc[:, "offline_duration_sec"] = 0
    result = rank_week(telemetry, gateways, dt.date(2026, 2, 2), sigma=3.0)
    assert result["gateway_id"].tolist() == ["AAAAAAAAAAAA", "BBBBBBBBBBBB"]


def test_gateway_with_history_but_no_recent_rows_remains_visible() -> None:
    telemetry, gateways = _fixtures()
    recent_start = pd.Timestamp("2026-01-26", tz="UTC")
    telemetry = telemetry[
        ~(
            telemetry["gateway_id"].eq("AAAAAAAAAAAA")
            & telemetry["ts"].ge(recent_start)
        )
    ]

    result = rank_week(telemetry, gateways, dt.date(2026, 2, 2), sigma=3.0)
    silent = result[result["gateway_id"].eq("AAAAAAAAAAAA")].iloc[0]
    assert silent["observed_recent_hours"] == 0
    assert silent["missing_recent_hours"] == 168


def test_silent_gateway_uses_type_safe_defaults() -> None:
    telemetry, gateways = _fixtures()
    recent_start = pd.Timestamp("2026-01-26", tz="UTC")
    telemetry = telemetry[
        ~(
            telemetry["gateway_id"].eq("AAAAAAAAAAAA")
            & telemetry["ts"].ge(recent_start)
        )
    ]

    result = rank_week(telemetry, gateways, dt.date(2026, 2, 2), sigma=3.0)
    silent = result[result["gateway_id"].eq("AAAAAAAAAAAA")].iloc[0]

    assert silent["metric_breaches"] == 0
    assert silent["observed_recent_hours"] == 0
    assert silent["worst_metric"] == ""
    assert pd.isna(silent["peak_sigma"])
