"""Collection run: ask a source for fares on every route and booking window."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from pathlib import Path

from . import config, db
from .models import FareObservation
from .sources import FareSource

log = logging.getLogger(__name__)


def collect_day(source: FareSource, collected_on: date) -> list[FareObservation]:
    out: list[FareObservation] = []
    for route in config.BASKET:
        for window in config.BOOKING_WINDOWS:
            travel = collected_on + timedelta(days=window)
            try:
                out.extend(source.fetch(route, collected_on, travel))
            except Exception:  # one broken route must not kill the whole run
                log.exception("Failed %s %s -> %s", source.name, route.code, travel)
    return out


def run(source: FareSource, start: date, days: int, db_path: Path | str) -> int:
    """Collect `days` consecutive days starting at `start`. Returns rows inserted."""
    inserted = 0
    with db.session(db_path) as conn:
        db.upsert_routes(conn, config.BASKET)
        for i in range(days):
            day = start + timedelta(days=i)
            n = db.insert_observations(conn, collect_day(source, day))
            log.info("%s: %d fares", day, n)
            inserted += n
    return inserted
