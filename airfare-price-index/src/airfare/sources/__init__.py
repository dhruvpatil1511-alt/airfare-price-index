"""Fare sources. Each source turns (route, collection date, travel date) into fares."""

from .amadeus import AmadeusSource
from .base import FareSource
from .sample import SampleSource

SOURCES: dict[str, type[FareSource]] = {
    "sample": SampleSource,
    "amadeus": AmadeusSource,
}

__all__ = ["FareSource", "SampleSource", "SOURCES"]
