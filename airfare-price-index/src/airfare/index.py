"""Price index computation.

Method (follows standard CPI practice):

1. Elementary aggregate - for each route, day and booking window, take the
   geometric mean of all quoted fares (Jevons). Geometric means are what most
   national statistics offices use because they are robust to one extreme fare.
2. Route relative   - elementary price today / elementary price in base period.
   Averaged over booking windows so each route has one relative per day.
3. Aggregate index  - weighted arithmetic mean of route relatives using fixed
   base-period weights (Laspeyres-type), scaled so base period = 100.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _geo_mean(s: pd.Series) -> float:
    return float(np.exp(np.log(s).mean()))


def elementary_prices(obs: pd.DataFrame) -> pd.DataFrame:
    """Geometric-mean fare per route x day x booking window."""
    if obs.empty:
        return pd.DataFrame(columns=["route", "collected_on", "days_ahead", "weight", "price"])
    return (
        obs.groupby(["route", "collected_on", "days_ahead"], as_index=False)
        .agg(weight=("weight", "first"), price=("fare_inr", _geo_mean))
    )


def base_dates(obs: pd.DataFrame, base_days: int) -> list[pd.Timestamp]:
    days = sorted(obs["collected_on"].unique())
    if len(days) < base_days:
        raise ValueError(
            f"Need at least {base_days} collection days for the base period, have {len(days)}"
        )
    return days[:base_days]


def route_relatives(obs: pd.DataFrame, base_days: int = 7) -> pd.DataFrame:
    """Price relative (today / base) per route per day, averaged over windows."""
    elem = elementary_prices(obs)
    base = elem[elem["collected_on"].isin(base_dates(obs, base_days))]
    base_price = (
        base.groupby(["route", "days_ahead"])["price"].apply(_geo_mean).rename("base_price")
    )
    merged = elem.join(base_price, on=["route", "days_ahead"], how="inner")
    merged["relative"] = merged["price"] / merged["base_price"]
    return (
        merged.groupby(["route", "collected_on"], as_index=False)
        .agg(weight=("weight", "first"), relative=("relative", _geo_mean))
    )


def aggregate_index(obs: pd.DataFrame, base_days: int = 7) -> pd.DataFrame:
    """Daily all-routes index (base = 100) plus how many routes fed each day."""
    rel = route_relatives(obs, base_days)
    rel["w_rel"] = rel["weight"] * rel["relative"]
    daily = rel.groupby("collected_on").agg(
        w_rel=("w_rel", "sum"), w=("weight", "sum"), routes=("route", "nunique")
    )
    daily["index"] = 100 * daily["w_rel"] / daily["w"]
    return daily[["index", "routes"]].reset_index()


def route_indices(obs: pd.DataFrame, base_days: int = 7) -> pd.DataFrame:
    """Per-route index series (base = 100), wide format: one column per route."""
    rel = route_relatives(obs, base_days)
    rel["index"] = 100 * rel["relative"]
    return rel.pivot(index="collected_on", columns="route", values="index")
