"""Project configuration: the basket of routes and collection settings.

Weights approximate each route's share of passenger spend. Replace them with
real DGCA traffic x average fare figures when you have them.
"""

from __future__ import annotations

import os
from pathlib import Path

from .models import Route

DB_PATH = Path(os.environ.get("AIRFARE_DB", "data/airfare.db"))

# Booking windows (days before departure) sampled on every collection run.
# CPI practice: keep the window fixed so the index compares like with like.
BOOKING_WINDOWS: tuple[int, ...] = (7, 14, 30)

# Number of initial collection days averaged to form the base period (= 100).
BASE_PERIOD_DAYS = 7

BASKET: tuple[Route, ...] = (
    Route("DEL", "BOM", 14.0),
    Route("BOM", "DEL", 14.0),
    Route("DEL", "BLR", 10.0),
    Route("BLR", "DEL", 10.0),
    Route("BOM", "BLR", 8.0),
    Route("DEL", "CCU", 7.0),
    Route("DEL", "HYD", 7.0),
    Route("BOM", "GOI", 5.0),
    Route("MAA", "DEL", 6.0),
    Route("BLR", "CCU", 4.0),
)
