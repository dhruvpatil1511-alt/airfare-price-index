from datetime import date

from airfare.models import Route
from airfare.sources.amadeus import AmadeusSource


def test_keeps_cheapest_fare_per_carrier(monkeypatch):
    monkeypatch.setenv("AMADEUS_CLIENT_ID", "x")
    monkeypatch.setenv("AMADEUS_CLIENT_SECRET", "y")
    offers = {"data": [
        {"validatingAirlineCodes": ["6E"], "price": {"grandTotal": "5200.50"}},
        {"validatingAirlineCodes": ["6E"], "price": {"grandTotal": "4800.00"}},
        {"validatingAirlineCodes": ["AI"], "price": {"grandTotal": "6100.00"}},
    ]}
    src = AmadeusSource()
    monkeypatch.setattr(
        src, "_json",
        lambda req: offers if "flight-offers" in req.full_url
        else {"access_token": "t", "expires_in": 1799},
    )
    got = src.fetch(Route("DEL", "BOM"), date(2026, 10, 14), date(2026, 10, 21))
    assert {o.carrier: o.fare_inr for o in got} == {"6E": 4800.0, "AI": 6100.0}
