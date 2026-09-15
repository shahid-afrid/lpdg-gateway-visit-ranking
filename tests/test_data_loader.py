from __future__ import annotations

import pandas as pd
import pytest

from gateway_ranker.data_loader import active_gateway_ids, normalise_gateway_id


def test_gateway_ids_are_normalised() -> None:
    values = pd.Series(["aa:bb:cc:dd:ee:ff", "112233445566"])
    assert normalise_gateway_id(values).tolist() == ["AABBCCDDEEFF", "112233445566"]


def test_invalid_gateway_id_is_rejected() -> None:
    with pytest.raises(ValueError, match="invalid gateway_id"):
        normalise_gateway_id(pd.Series(["not-a-gateway"]))


def test_active_gateways_respect_lifecycle_dates() -> None:
    gateways = pd.DataFrame(
        {
            "gateway_id": ["AAAAAAAAAAAA", "BBBBBBBBBBBB", "CCCCCCCCCCCC"],
            "installed_on": pd.to_datetime(["2025-01-01", "2026-03-01", "2025-01-01"]),
            "decommissioned_on": pd.to_datetime([None, None, "2026-02-01"]),
        }
    )
    active = active_gateway_ids(gateways, pd.Timestamp("2026-02-02", tz="UTC"))
    assert active == {"AAAAAAAAAAAA"}

