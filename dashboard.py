import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

# load env
load_dotenv()

DB_URL = os.getenv("DB_URL")

st.set_page_config(
    page_title="OLX Secondhand Car Dashboard",
    layout="wide"
)

st.title("🚗 OLX Secondhand Wuling Air EV")
st.caption("A small personal project inspired by my plan to buy a secondhand Wuling Air EV next year. The data is updated weekly using Luigi for orchestration and cron for schedulling")

# -----------------------------
# Load data
# -----------------------------
@st.cache_data(ttl=600)
def load_data():
    engine = create_engine(DB_URL)
    query = "SELECT * FROM scrape_data"
    df = pd.read_sql(query, engine)
    return df

df = load_data()

# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.header("🔎 Filters")

year_min, year_max = int(df["year"].min()), int(df["year"].max())
year_range = st.sidebar.slider(
    "Year Range",
    year_min,
    year_max,
    (year_min, year_max)
)

max_km = st.sidebar.slider(
    "Max Mileage (km)",
    0,
    int(df["upper_km"].max()),
    int(df["upper_km"].max())
)

filtered_df = df[
    (df["year"] >= year_range[0]) &
    (df["year"] <= year_range[1]) &
    (df["upper_km"] <= max_km)
]

# -----------------------------
# Metrics
# -----------------------------
col1, col2, col3 = st.columns(3)

col1.metric("Total Listings", len(filtered_df))
col2.metric("Median Price", f"Rp {filtered_df['price'].median():,.0f}")
col3.metric("Lowest Price", f"Rp {filtered_df['price'].min():,.0f}")

# -----------------------------
# Charts
# -----------------------------
st.subheader("📉 Price vs Mileage")

st.scatter_chart(
    filtered_df,
    x="upper_km",
    y="price"
)

st.subheader("📊 Price Distribution by Year")

st.bar_chart(
    filtered_df.groupby("year")["price"].median()
)

# -----------------------------
# Best Deals
# -----------------------------
st.subheader("🔥 Potential Good Deals")

best_deals = filtered_df.sort_values(
    ["price", "upper_km"],
    ascending=[True, True]
).head(10)

st.dataframe(
    best_deals[
        ["title", "price", "year", "lower_km", "upper_km", "location", "listing_url"]
    ],
    use_container_width=True
)
