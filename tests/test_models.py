from datetime import date

import pytest

from airfare.models import FareObservation, Route


def test_route_code():
    assert Route("DEL", "BOM").code == "DEL-BOM"


@pytest.mark.parametrize("o,d", [("del", "BOM"), ("DELH", "BOM"), ("DEL", "DEL"), ("D3L", "BOM")])
def test_route_rejects_bad_codes(o, d):
    with pytest.raises(ValueError):
        Route(o, d)


def test_route_rejects_non_positive_weight():
    with pytest.raises(ValueError):
        Route("DEL", "BOM", 0)


def test_observation_days_ahead():
    o = FareObservation(Route("DEL", "BOM"), "t", date(2026, 10, 1), date(2026, 10, 15), "X", 5000)
    assert o.days_ahead == 14


def test_observation_rejects_bad_values():
    r = Route("DEL", "BOM")
    with pytest.raises(ValueError):
        FareObservation(r, "t", date(2026, 10, 1), date(2026, 10, 2), "X", -1)
    with pytest.raises(ValueError):
        FareObservation(r, "t", date(2026, 10, 5), date(2026, 10, 1), "X", 5000)
