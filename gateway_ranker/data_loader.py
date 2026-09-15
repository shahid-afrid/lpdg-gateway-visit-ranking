"""Read the supplied files and apply the cleaning rules used by the project."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import pandas as pd

from .config import METRICS

_GATEWAY_ID = re.compile(r"^[0-9A-F]{12}$")
_TELEMETRY_COLUMNS = ("gateway_id", "ts_utc", *METRICS)


@dataclass(frozen=True)
class DataBundle:
    telemetry: pd.DataFrame
    gateways: pd.DataFrame
    field_visits: pd.DataFrame
    meter_reads: pd.DataFrame
    engineer_review: pd.DataFrame
    duplicate_telemetry_rows_removed: int


def normalise_gateway_id(values: pd.Series) -> pd.Series:
    """Return upper-case 12-character identifiers without separators."""

    result = (
        values.astype("string")
        .str.strip()
        .str.replace(":", "", regex=False)
        .str.upper()
    )
    invalid = result.notna() & ~result.str.fullmatch(_GATEWAY_ID)
    if invalid.any():
        examples = result[invalid].head(3).tolist()
        raise ValueError(f"invalid gateway_id value(s), for example {examples}")
    return result


def _require_columns(frame: pd.DataFrame, required: tuple[str, ...], source: Path) -> None:
    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise ValueError(f"{source} is missing required column(s): {', '.join(missing)}")


def _load_telemetry(data_dir: Path) -> tuple[pd.DataFrame, int]:
    source = data_dir / "telemetry"
    if not source.exists():
        raise FileNotFoundError(f"telemetry directory not found: {source}")

    frame = pd.read_parquet(source, columns=list(_TELEMETRY_COLUMNS))
    _require_columns(frame, _TELEMETRY_COLUMNS, source)
    frame["gateway_id"] = normalise_gateway_id(frame["gateway_id"])
    frame["ts"] = pd.to_datetime(frame.pop("ts_utc"), utc=True, errors="raise")

    key = ["gateway_id", "ts"]
    duplicates = frame.duplicated(key, keep=False)
    if duplicates.any():
        conflicting = (
            frame.loc[duplicates]
            .groupby(key, observed=True)[list(METRICS)]
            .nunique(dropna=False)
            .gt(1)
            .any(axis=1)
        )
        if conflicting.any():
            raise ValueError(
                f"telemetry contains {int(conflicting.sum())} duplicate timestamp(s) "
                "with conflicting ranking values"
            )

    before = len(frame)
    frame = frame.drop_duplicates(key, keep="first").sort_values(key).reset_index(drop=True)
    removed = before - len(frame)

    if frame[list(METRICS)].isna().any().any():
        missing = frame[list(METRICS)].isna().sum()
        detail = ", ".join(f"{name}={count}" for name, count in missing.items() if count)
        raise ValueError(f"ranking metrics contain missing values: {detail}")
    return frame, removed


def _load_gateways(data_dir: Path) -> pd.DataFrame:
    source = data_dir / "gateway_master.csv"
    frame = pd.read_csv(source, encoding="latin-1")
    required = ("gateway_id", "installed_on", "decommissioned_on", "n_meters_installed")
    _require_columns(frame, required, source)
    frame["gateway_id"] = normalise_gateway_id(frame["gateway_id"])
    frame["installed_on"] = pd.to_datetime(frame["installed_on"], errors="raise")
    frame["decommissioned_on"] = pd.to_datetime(frame["decommissioned_on"], errors="coerce")
    if frame["gateway_id"].duplicated().any():
        raise ValueError("gateway_master.csv contains duplicate gateway IDs")
    return frame


def _load_field_visits(data_dir: Path) -> pd.DataFrame:
    source = data_dir / "field_visits.csv"
    frame = pd.read_csv(source)
    required = ("visit_id", "gateway_id", "requested_on", "visited_on", "outcome")
    _require_columns(frame, required, source)
    frame["gateway_id"] = normalise_gateway_id(frame["gateway_id"])
    frame["requested_on"] = pd.to_datetime(frame["requested_on"], errors="raise")
    frame["visited_on"] = pd.to_datetime(frame["visited_on"], errors="raise")
    return frame


def _load_meter_reads(data_dir: Path) -> pd.DataFrame:
    source = data_dir / "meter_read_success.csv"
    frame = pd.read_csv(source)
    required = ("week_start", "gateway_id", "meters_expected", "meters_read")
    _require_columns(frame, required, source)
    frame["gateway_id"] = normalise_gateway_id(frame["gateway_id"])
    frame["week_start"] = pd.to_datetime(frame["week_start"], errors="raise")
    if (frame["meters_expected"] <= 0).any():
        raise ValueError("meter_read_success.csv contains non-positive meters_expected")
    if ((frame["meters_read"] < 0) | (frame["meters_read"] > frame["meters_expected"])).any():
        raise ValueError("meter_read_success.csv contains an invalid meters_read value")
    frame["success_rate"] = frame["meters_read"] / frame["meters_expected"]
    return frame


def _load_engineer_review(data_dir: Path) -> pd.DataFrame:
    source = data_dir / "engineer_review_2026-02.xlsx"
    frame = pd.read_excel(source)
    required = ("gateway_id", "Kategorie", "reviewed_on")
    _require_columns(frame, required, source)
    frame["gateway_id"] = normalise_gateway_id(frame["gateway_id"])
    frame["reviewed_on"] = pd.to_datetime(frame["reviewed_on"], errors="raise")
    return frame


def load_data(data_dir: Path | str) -> DataBundle:
    """Load all supplied sources and return consistently typed tables."""

    root = Path(data_dir)
    if not root.is_dir():
        raise FileNotFoundError(f"data directory not found: {root}")

    telemetry, removed = _load_telemetry(root)
    return DataBundle(
        telemetry=telemetry,
        gateways=_load_gateways(root),
        field_visits=_load_field_visits(root),
        meter_reads=_load_meter_reads(root),
        engineer_review=_load_engineer_review(root),
        duplicate_telemetry_rows_removed=removed,
    )


def active_gateway_ids(gateways: pd.DataFrame, cutoff: pd.Timestamp) -> set[str]:
    """Return gateways commissioned and not decommissioned at the cutoff."""

    day = cutoff.tz_localize(None).normalize()
    active = (
        gateways["installed_on"].le(day)
        & (gateways["decommissioned_on"].isna() | gateways["decommissioned_on"].gt(day))
    )
    return set(gateways.loc[active, "gateway_id"])

