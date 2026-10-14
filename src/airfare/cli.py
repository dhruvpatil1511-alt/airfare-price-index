"""Command line entry point.

    airfare collect --days 60            # backfill 60 days of sample data
    airfare collect                      # collect today only (use in a daily cron)
    airfare index                        # print the latest index values
    airfare export --out index.csv       # save index series to CSV
"""

from __future__ import annotations

import argparse
import logging
from datetime import date, timedelta

from . import collect, config, db, index
from .sources import SOURCES


def _cmd_collect(args: argparse.Namespace) -> None:
    source = SOURCES[args.source]()
    if source.live_only and (args.start or args.days != 1):
        raise SystemExit(f"{source.name} is live-only: run `collect` daily, no --days/--start.")
    if args.start:
        start = date.fromisoformat(args.start)
    else:
        start = date.today() - timedelta(days=args.days - 1)
    n = collect.run(source, start, args.days, args.db)
    print(f"Inserted {n} fare observations into {args.db}")


def _load_index(args: argparse.Namespace):
    with db.session(args.db) as conn:
        obs = db.load_observations(conn)
    if obs.empty:
        raise SystemExit("No data yet. Run `airfare collect --days 30` first.")
    return index.aggregate_index(obs, config.BASE_PERIOD_DAYS)


def _cmd_index(args: argparse.Namespace) -> None:
    idx = _load_index(args)
    print(idx.tail(args.last).to_string(index=False, float_format=lambda v: f"{v:7.2f}"))


def _cmd_export(args: argparse.Namespace) -> None:
    _load_index(args).to_csv(args.out, index=False, float_format="%.3f")
    print(f"Wrote {args.out}")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="airfare", description="Airfare Price Index")
    p.add_argument("--db", default=str(config.DB_PATH), help="SQLite database path")
    p.add_argument("-v", "--verbose", action="store_true")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("collect", help="collect fares")
    c.add_argument("--source", choices=sorted(SOURCES), default="sample")
    c.add_argument("--days", type=int, default=1, help="number of days to collect")
    c.add_argument("--start", help="first collection date, YYYY-MM-DD")
    c.set_defaults(func=_cmd_collect)

    i = sub.add_parser("index", help="show latest index values")
    i.add_argument("--last", type=int, default=10)
    i.set_defaults(func=_cmd_index)

    e = sub.add_parser("export", help="export index to CSV")
    e.add_argument("--out", default="data/index.csv")
    e.set_defaults(func=_cmd_export)

    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(levelname)s %(message)s")
    args.func(args)


if __name__ == "__main__":
    main()
