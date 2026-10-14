"""Streamlit dashboard.  Run:  streamlit run dashboard/app.py"""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from airfare import config, db, index

st.set_page_config(page_title="Airfare Price Index", page_icon="✈️", layout="wide")


@st.cache_data(ttl=600)
def load():
    with db.session(config.DB_PATH) as conn:
        return db.load_observations(conn)


obs = load()
st.title("✈️ Airfare Price Index — India domestic")
st.caption(
    "CPI-style daily index of domestic airfares. Base period (first "
    f"{config.BASE_PERIOD_DAYS} collection days) = 100."
)

if obs.empty:
    st.warning("No data yet. Run `airfare collect --days 60` and refresh.")
    st.stop()

sources = sorted(obs["source"].unique())
if sources == ["sample"]:
    st.info("Showing **synthetic sample data**. Plug in a real source to see live fares.")

agg = index.aggregate_index(obs, config.BASE_PERIOD_DAYS)
routes = index.route_indices(obs, config.BASE_PERIOD_DAYS)

latest, prev = agg.iloc[-1], agg.iloc[-2] if len(agg) > 1 else agg.iloc[-1]
week_ago = agg.iloc[-8] if len(agg) >= 8 else agg.iloc[0]

c1, c2, c3, c4 = st.columns(4)
day_change = latest["index"] - prev["index"]
c1.metric("Index (latest)", f"{latest['index']:.1f}", f"{day_change:+.1f} vs yesterday")
c2.metric("7-day change", f"{(latest['index'] / week_ago['index'] - 1) * 100:+.1f}%")
c3.metric("Routes in basket", int(latest["routes"]))
c4.metric("Fares collected", f"{len(obs):,}")

st.subheader("All-routes index")
agg["7-day average"] = agg["index"].rolling(7, min_periods=1).mean()
plot = agg.rename(columns={"index": "Daily"}).melt(
    "collected_on", ["Daily", "7-day average"], var_name="series", value_name="value"
)
fig = px.line(plot, x="collected_on", y="value", color="series",
              labels={"collected_on": "", "value": "Index", "series": ""},
              color_discrete_map={"Daily": "#9ab8d8", "7-day average": "#0b5cad"})
fig.add_hline(y=100, line_dash="dot", opacity=0.5)
st.plotly_chart(fig, use_container_width=True)

left, right = st.columns([2, 1])
with left:
    st.subheader("By route")
    pick = st.multiselect("Routes", list(routes.columns), default=list(routes.columns)[:4])
    if pick:
        long = routes[pick].reset_index().melt("collected_on", var_name="route", value_name="index")
        st.plotly_chart(
            px.line(long, x="collected_on", y="index", color="route",
                    labels={"collected_on": "", "index": "Index"}),
            use_container_width=True,
        )
with right:
    st.subheader("Booking-window effect")
    by_window = obs.groupby("days_ahead", as_index=False)["fare_inr"].median()
    st.plotly_chart(
        px.bar(by_window, x="days_ahead", y="fare_inr",
               labels={"days_ahead": "Days before departure", "fare_inr": "Median fare (₹)"}),
        use_container_width=True,
    )

with st.expander("Methodology"):
    st.markdown(
        """
1. **Elementary price**: geometric mean (Jevons) of carrier fares per route, day, window.
2. **Route relative**: elementary price ÷ its base-period price, averaged across booking windows.
3. **Index**: weighted mean of route relatives, fixed base weights (Laspeyres) × 100.
"""
    )
    st.dataframe(agg.tail(14), use_container_width=True, hide_index=True)
