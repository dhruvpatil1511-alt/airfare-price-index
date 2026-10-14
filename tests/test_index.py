import pandas as pd
import pytest

from airfare import index


def make_obs(rows):
    """rows: (route, weight, day, days_ahead, fare)"""
    df = pd.DataFrame(rows, columns=["route", "weight", "collected_on", "days_ahead", "fare_inr"])
    df["collected_on"] = pd.to_datetime(df["collected_on"])
    return df


def test_geometric_mean_elementary_price():
    obs = make_obs([("A-B", 1, "2026-10-01", 7, 4000), ("A-B", 1, "2026-10-01", 7, 9000)])
    elem = index.elementary_prices(obs)
    assert elem["price"].iloc[0] == pytest.approx(6000)  # sqrt(4000*9000)


def test_base_period_equals_100():
    obs = make_obs([("A-B", 1, f"2026-10-0{d}", 7, 5000) for d in range(1, 4)])
    agg = index.aggregate_index(obs, base_days=3)
    assert agg["index"].tolist() == pytest.approx([100, 100, 100])


def test_uniform_price_rise_moves_index_by_same_percent():
    rows = []
    for route, w in (("A-B", 3), ("C-D", 1)):
        rows += [(route, w, "2026-10-01", 7, 5000), (route, w, "2026-10-02", 7, 5500)]
    agg = index.aggregate_index(make_obs(rows), base_days=1)
    assert agg["index"].iloc[-1] == pytest.approx(110)


def test_weights_are_applied():
    rows = [
        ("A-B", 3, "2026-10-01", 7, 1000), ("A-B", 3, "2026-10-02", 7, 1200),  # +20%, weight 3
        ("C-D", 1, "2026-10-01", 7, 1000), ("C-D", 1, "2026-10-02", 7, 1000),  #   0%, weight 1
    ]
    agg = index.aggregate_index(make_obs(rows), base_days=1)
    assert agg["index"].iloc[-1] == pytest.approx(100 * (3 * 1.2 + 1 * 1.0) / 4)


def test_needs_enough_base_days():
    obs = make_obs([("A-B", 1, "2026-10-01", 7, 5000)])
    with pytest.raises(ValueError):
        index.aggregate_index(obs, base_days=7)


def test_route_indices_wide_format():
    rows = [
        ("A-B", 1, "2026-10-01", 7, 1000), ("A-B", 1, "2026-10-02", 7, 1100),
        ("C-D", 1, "2026-10-01", 7, 2000), ("C-D", 1, "2026-10-02", 7, 1800),
    ]
    wide = index.route_indices(make_obs(rows), base_days=1)
    assert list(wide.columns) == ["A-B", "C-D"]
    assert wide["A-B"].iloc[-1] == pytest.approx(110)
    assert wide["C-D"].iloc[-1] == pytest.approx(90)
