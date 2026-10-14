"""Amadeus Self-Service flight offers: an official API, so no scraping or ToS risk.

Free keys: https://developers.amadeus.com  ->  export AMADEUS_CLIENT_ID / AMADEUS_CLIENT_SECRET
Default is the test environment (cached, limited data). AMADEUS_ENV=production for live fares.
"""

from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from datetime import date

from ..models import FareObservation, Route
from .base import FareSource

HOSTS = {"test": "https://test.api.amadeus.com", "production": "https://api.amadeus.com"}


class AmadeusSource(FareSource):
    name = "amadeus"
    live_only = True  # the API only quotes future flights, so no backfill

    def __init__(self) -> None:
        try:
            self._id = os.environ["AMADEUS_CLIENT_ID"]
            self._secret = os.environ["AMADEUS_CLIENT_SECRET"]
        except KeyError as e:
            raise SystemExit(f"Set {e.args[0]} (free keys at developers.amadeus.com)") from None
        self._host = HOSTS[os.environ.get("AMADEUS_ENV", "test")]
        self._token, self._expires = "", 0.0

    def _json(self, req: urllib.request.Request) -> dict:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)

    def _auth(self) -> str:
        if time.time() >= self._expires:
            body = urllib.parse.urlencode(
                {"grant_type": "client_credentials", "client_id": self._id,
                 "client_secret": self._secret}
            ).encode()
            tok = self._json(urllib.request.Request(f"{self._host}/v1/security/oauth2/token", body))
            self._token, self._expires = tok["access_token"], time.time() + tok["expires_in"] - 30
        return self._token

    def fetch(self, route: Route, collected_on: date, travel_date: date) -> list[FareObservation]:
        q = urllib.parse.urlencode(
            {"originLocationCode": route.origin, "destinationLocationCode": route.destination,
             "departureDate": travel_date.isoformat(), "adults": 1, "currencyCode": "INR",
             "nonStop": "true", "max": 20}  # nonstop only, so every day compares like with like
        )
        req = urllib.request.Request(
            f"{self._host}/v2/shopping/flight-offers?{q}",
            headers={"Authorization": f"Bearer {self._auth()}"},
        )
        cheapest: dict[str, float] = {}  # one fare per carrier, matching the DB unique key
        for offer in self._json(req)["data"]:
            carrier = offer["validatingAirlineCodes"][0]
            fare = float(offer["price"]["grandTotal"])
            cheapest[carrier] = min(fare, cheapest.get(carrier, fare))
        return [
            FareObservation(route, self.name, collected_on, travel_date, c, f)
            for c, f in cheapest.items()
        ]
