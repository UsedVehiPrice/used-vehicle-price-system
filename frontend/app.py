"""Streamlit dashboard.  Run from the project root:
    streamlit run frontend/app.py
Reads the SQLite database directly (no need to start the API).
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st

from analysis.analyze import average_price_by_model_year, flag_good_deals, load_vehicles
from database.db import init_db

st.set_page_config(page_title="Used Vehicle Price Comparison", layout="wide")
st.title("Used Vehicle Price Comparison")

init_db()
data = load_vehicles()
if data.empty:
    st.warning("The database is empty. Run `python run_pipeline.py --sample` first.")
    st.stop()

# ---- sidebar filters ---------------------------------------------------
st.sidebar.header("Filters")
brands = st.sidebar.multiselect("Brand", sorted(data["brand"].unique()))
view = data[data["brand"].isin(brands)] if brands else data
models = st.sidebar.multiselect("Model", sorted(view["model"].unique()))
if models:
    view = view[view["model"].isin(models)]
fuels = st.sidebar.multiselect("Fuel type", sorted(view["fuel_type"].dropna().unique()))
if fuels:
    view = view[view["fuel_type"].isin(fuels)]
y_min, y_max = int(data["year"].min()), int(data["year"].max())
years = st.sidebar.slider("Year", y_min, y_max, (y_min, y_max))
view = view[view["year"].between(*years)]
max_km = st.sidebar.number_input("Max km driven", 0, 1_000_000, 200_000, step=5_000)
view = view[view["km_driven"].isna() | (view["km_driven"] <= max_km)]

# ---- results -----------------------------------------------------------
deals = flag_good_deals(view)
c1, c2, c3 = st.columns(3)
c1.metric("Listings", len(deals))
c2.metric("Average price", f"₹{deals['price'].mean():,.0f}" if len(deals) else "-")
c3.metric("Good deals", int(deals["good_deal"].sum()))

tab1, tab2, tab3 = st.tabs(["Listings", "Price vs km", "Average price by year"])
with tab1:
    only_deals = st.checkbox("Show only good deals")
    shown = deals[deals["good_deal"]] if only_deals else deals
    st.dataframe(
        shown.sort_values("price")[
            ["brand", "model", "year", "fuel_type", "km_driven", "price",
             "location", "source", "pct_below_avg", "good_deal", "url"]
        ],
        use_container_width=True,
    )
with tab2:
    st.scatter_chart(deals, x="km_driven", y="price", color="source")
with tab3:
    avg = average_price_by_model_year(view)
    if len(avg):
        pivot = avg.pivot_table(index="year", columns="model", values="avg_price")
        st.line_chart(pivot)
