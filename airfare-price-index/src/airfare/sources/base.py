"""Interface every fare source implements.

Adding a real website = one new subclass. The rest of the pipeline (storage,
index, dashboard) never changes. This is the Strategy pattern.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from ..models import FareObservation, Route


class FareSource(ABC):
    name: str = "base"
    live_only: bool = False  # True if the source can only quote today's prices (no backfill)

    @abstractmethod
    def fetch(self, route: Route, collected_on: date, travel_date: date) -> list[FareObservation]:
        """Return all fares quoted today for one route and travel date."""
