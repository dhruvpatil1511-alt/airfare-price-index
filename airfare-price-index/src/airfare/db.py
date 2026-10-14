"""SQLite storage layer.

SQLite keeps the project zero-setup. The schema is plain SQL, so moving to
PostgreSQL later only needs a different connection and AUTOINCREMENT -> SERIAL.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from importlib import resources
from pathlib import Path

import pandas as pd

from .models import FareObservation, Route


def connect(db_path: Path | str) -> sqlite3.Connection:
    if str(db_path) != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    schema = resources.files("airfare").joinpath("schema.sql").read_text()
    conn.executescript(schema)


@contextmanager
def session(db_path: Path | str) -> Iterator[sqlite3.Connection]:
    conn = connect(db_path)
    try:
        init_db(conn)
        yield conn
        conn.commit()
    finally:
        conn.close()


def upsert_routes(conn: sqlite3.Connection, routes: Iterable[Route]) -> None:
    conn.executemany(
        """INSERT INTO routes (origin, destination, weight) VALUES (?, ?, ?)
           ON CONFLICT(origin, destination) DO UPDATE SET weight = excluded.weight""",
        [(r.origin, r.destination, r.weight) for r in routes],
    )


def _id(conn: sqlite3.Connection, sql: str, params: tuple) -> int:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        raise LookupError(f"No row for {params}")
    return row[0]


def insert_observations(conn: sqlite3.Connection, obs: Iterable[FareObservation]) -> int:
    """Insert observations, ignoring exact duplicates. Returns rows inserted."""
    route_ids: dict[str, int] = {}
    source_ids: dict[str, int] = {}
    rows = []
    for o in obs:
        if o.route.code not in route_ids:
            upsert_routes(conn, [o.route])
            route_ids[o.route.code] = _id(
                conn,
                "SELECT route_id FROM routes WHERE origin=? AND destination=?",
                (o.route.origin, o.route.destination),
            )
        if o.source not in source_ids:
            conn.execute("INSERT OR IGNORE INTO sources (name) VALUES (?)", (o.source,))
            source_ids[o.source] = _id(
                conn, "SELECT source_id FROM sources WHERE name=?", (o.source,)
            )
        rows.append(
            (
                route_ids[o.route.code],
                source_ids[o.source],
                o.collected_on.isoformat(),
                o.travel_date.isoformat(),
                o.days_ahead,
                o.carrier,
                o.fare_inr,
            )
        )
    before = conn.total_changes
    conn.executemany(
        """INSERT OR IGNORE INTO fare_observations
           (route_id, source_id, collected_on, travel_date, days_ahead, carrier, fare_inr)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    return conn.total_changes - before


def load_observations(conn: sqlite3.Connection) -> pd.DataFrame:
    """All observations joined with route info, one row per fare."""
    df = pd.read_sql_query(
        """SELECT r.origin || '-' || r.destination AS route,
                  r.weight, s.name AS source, f.collected_on, f.travel_date,
                  f.days_ahead, f.carrier, f.fare_inr
           FROM fare_observations f
           JOIN routes r  ON r.route_id  = f.route_id
           JOIN sources s ON s.source_id = f.source_id
           ORDER BY f.collected_on, route""",
        conn,
    )
    for col in ("collected_on", "travel_date"):
        df[col] = pd.to_datetime(df[col])
    return df
