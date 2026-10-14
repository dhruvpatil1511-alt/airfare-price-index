"""End-to-end: sample source -> SQLite -> index."""

from datetime import date

import pytest

from airfare import collect, config, db, index
from airfare.cli import main
from airfare.sources import SampleSource


def test_sample_source_is_deterministic():
    r = config.BASKET[0]
    a = SampleSource(seed=1).fetch(r, date(2026, 10, 1), date(2026, 10, 8))
    b = SampleSource(seed=1).fetch(r, date(2026, 10, 1), date(2026, 10, 8))
    assert a == b and len(a) > 0


def test_last_minute_fares_cost_more():
    r = config.BASKET[0]
    src = SampleSource()
    near = [o.fare_inr for o in src.fetch(r, date(2026, 10, 1), date(2026, 10, 3))]
    far = [o.fare_inr for o in src.fetch(r, date(2026, 10, 1), date(2026, 10, 31))]
    assert sum(near) / len(near) > sum(far) / len(far)


def test_collect_then_index(tmp_path):
    path = tmp_path / "t.db"
    n = collect.run(SampleSource(), date(2026, 9, 1), 10, path)
    assert n > 0
    # Re-running the same days inserts nothing new (idempotent)
    assert collect.run(SampleSource(), date(2026, 9, 1), 10, path) == 0

    with db.session(path) as conn:
        obs = db.load_observations(conn)
    agg = index.aggregate_index(obs, base_days=7)
    assert len(agg) == 10
    assert agg["index"].iloc[:7].mean() == pytest.approx(100, abs=3)
    assert agg["routes"].max() == len(config.BASKET)


def test_cli_roundtrip(tmp_path, capsys):
    path = str(tmp_path / "cli.db")
    main(["--db", path, "collect", "--days", "8", "--start", "2026-09-01"])
    main(["--db", path, "index", "--last", "3"])
    out = capsys.readouterr().out
    assert "Inserted" in out and "index" in out
    csv = tmp_path / "i.csv"
    main(["--db", path, "export", "--out", str(csv)])
    assert csv.read_text().startswith("collected_on,index,routes")
