"""Synthetic fare generator so the whole pipeline runs with no internet.

The numbers are made up, but shaped like real Indian domestic fares:
- a base fare scaled by route distance
- fares rise as departure gets closer (booking-window effect)
- Friday/Sunday departures cost more
- a slow festive-season surge around Diwali (late Oct - mid Nov)
- each carrier prices a little differently, plus random noise

Seeded, so the same inputs always give the same fares (tests rely on this).
"""

from __future__ import annotations

import hashlib
import math
import random
from datetime import date

from ..models import FareObservation, Route
from .base import FareSource

# Approximate great-circle distances in km
DISTANCE_KM = {
    frozenset({"DEL", "BOM"}): 1150,
    frozenset({"DEL", "BLR"}): 1740,
    frozenset({"BOM", "BLR"}): 840,
    frozenset({"DEL", "CCU"}): 1300,
    frozenset({"DEL", "HYD"}): 1250,
    frozenset({"BOM", "GOI"}): 440,
    frozenset({"MAA", "DEL"}): 1760,
    frozenset({"BLR", "CCU"}): 1560,
}

CARRIERS = {"IndiGo": 1.00, "Air India": 1.12, "Akasa Air": 0.95, "SpiceJet": 0.97}

# Diwali 2026 is on 8 November
FESTIVE_PEAK = date(2026, 11, 8)


class SampleSource(FareSource):
    name = "sample"

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed

    def _rng(self, *parts: object) -> random.Random:
        key = "|".join(map(str, (self.seed, *parts))).encode()
        return random.Random(int(hashlib.sha256(key).hexdigest()[:16], 16))

    def fetch(self, route: Route, collected_on: date, travel_date: date) -> list[FareObservation]:
        km = DISTANCE_KM.get(frozenset({route.origin, route.destination}), 1200)
        base = 1800 + 3.2 * km
        days_ahead = (travel_date - collected_on).days

        window = 1 + 0.9 * math.exp(-days_ahead / 6)            # last-minute premium
        weekday = 1.15 if travel_date.weekday() in (4, 6) else 1.0  # Fri / Sun
        festive = 1 + 0.45 * math.exp(-((travel_date - FESTIVE_PEAK).days / 9) ** 2)

        fares = []
        for carrier, factor in CARRIERS.items():
            rng = self._rng(route.code, collected_on, travel_date, carrier)
            if rng.random() < 0.15:  # not every carrier flies/quotes every day
                continue
            noise = rng.lognormvariate(0, 0.08)
            fare = round(base * window * weekday * festive * factor * noise, -1)
            fares.append(
                FareObservation(route, self.name, collected_on, travel_date, carrier, fare)
            )
        return fares
