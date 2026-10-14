"""Plain data objects shared by collectors, storage and index code."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Route:
    origin: str
    destination: str
    weight: float = 1.0

    def __post_init__(self) -> None:
        for code in (self.origin, self.destination):
            if len(code) != 3 or not code.isalpha() or not code.isupper():
                raise ValueError(f"Invalid IATA code: {code!r}")
        if self.origin == self.destination:
            raise ValueError("Origin and destination must differ")
        if self.weight <= 0:
            raise ValueError("Route weight must be positive")

    @property
    def code(self) -> str:
        return f"{self.origin}-{self.destination}"


@dataclass(frozen=True)
class FareObservation:
    route: Route
    source: str
    collected_on: date
    travel_date: date
    carrier: str
    fare_inr: float

    def __post_init__(self) -> None:
        if self.fare_inr <= 0:
            raise ValueError("Fare must be positive")
        if self.travel_date < self.collected_on:
            raise ValueError("Travel date cannot be before collection date")

    @property
    def days_ahead(self) -> int:
        return (self.travel_date - self.collected_on).days
