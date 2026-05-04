import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder
import os
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DB_URL")

st.set_page_config(
    page_title="Wuling Air EV Tracker",
    page_icon="💨",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# STYLING
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { 
    font-family: 'Inter', sans-serif; 
}

/* Layout lebih lega */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 1rem !important;
    padding-left: 2.5rem !important;
    padding-right: 2.5rem !important;
    max-width: 100% !important;
}

/* HEADER */
.deck-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}
.deck-title {
    font-size: 2.6rem;
    font-weight: 600;
    color: #111827;
    line-height: 1.2;
}
.deck-subtitle {
    font-size: 0.9rem;
    color: #6b7280;
    margin-top: 4px;
}
.deck-meta { 
    font-size: 0.8rem; 
    color: #9ca3af; 
    text-align: right; 
}

/* KPI CARDS */
.kpi-card {
    background: #f9fafb;
    border-radius: 14px;
    padding: 18px;
    border: 1px solid #f1f5f9;
}
.kpi-label {
    font-size: 1rem;
    color: #6b7280;
    margin-bottom: 6px;
}
.kpi-value {
    font-size: 2rem;
    font-weight: 600;
    color: #111827;
}
.kpi-note { 
    font-size: 1rem; 
    color: #9ca3af; 
    margin-top: 6px; 
}
.kpi-accent { color: #2563eb !important; }

/* CHART */
.chart-title {
    font-size: 2rem;
    font-weight: 600;
    color: #111827;
    margin-bottom: 4px;
}
.chart-insight {
    font-size: 0.9rem;
    color: #6b7280;
    margin-bottom: 8px;
}

/* TABLE */
[data-testid="stDataFrame"] {
    font-size: 0.85rem;
}

/* CLEAN UI */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# HELPERS
CHART_H = 320
CHART_THEME = dict(
    template="plotly_white",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", size=13, color="#374151"),
    margin=dict(l=40, r=10, t=10, b=40),
    legend=dict(font=dict(size=11), bgcolor="rgba(0,0,0,0)", borderwidth=0),
)
COLORS = {
    "Long Range":"#1d4ed8",
    "Standard Range":"#0891b2",
    "Unknown":"#9ca3af",
    "Dealer":"#1d4ed8",
    "Individual":"#0891b2",
}

def chart_header(title, insight):
    st.markdown(
        f'<div class="chart-title">{title}</div>'
        f'<div class="chart-insight">{insight}</div>',
        unsafe_allow_html=True
    )

def kpi(label, value, note="", accent=False):
    note_cls = "kpi-note kpi-accent" if accent else "kpi-note"
    st.markdown(
        f'<div class="kpi-card">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="{note_cls}">{note}</div>'
        f'</div>',
        unsafe_allow_html=True
    )


# DATA LOADING
@st.cache_data(ttl=600)
def load_data():
    engine = create_engine(DB_URL)
    df = pd.read_sql("SELECT * FROM final.scrape_data", engine)
    df["km"]= (df["lower_km"] + df["upper_km"]) / 2
    df["variant_label"] = df["variant"].apply(
        lambda x: "Long Range" if "Long" in str(x)
        else ("Standard Range" if "Standard" in str(x) else "Unknown")
    )
    df["seller_label"]  = df["seller_type"].apply(
        lambda x: "Dealer" if str(x).lower() in ["diler", "dealer"] else "Individual"
    )
    df["city"]= df["location"].str.split(",").str[-1].str.strip()
    df["price_juta"]= df["price"] / 1_000_000
    df["age"]= 2026 - df["year"]
    return df.dropna(subset=["price", "year", "km"])

@st.cache_data(ttl=600)
def build_model(df):
    le = LabelEncoder()
    d  = df.copy()
    d["variant_enc"] = le.fit_transform(d["variant_label"])
    X  = d[["year", "km", "variant_enc"]]
    y  = d["price"]
    mdl = LinearRegression().fit(X, y)
    d["expected_price"] = mdl.predict(X)
    d["deal_score"]= ((d["expected_price"] - d["price"]) / d["expected_price"] * 100).round(1)
    def lbl(s):
        if s >= 15: return "Hot Deal"
        if s >= 5: return "Good Value"
        if s >= -5: return "Market Price"
        return "Overpriced"
    d["deal_label"] = d["deal_score"].apply(lbl)
    return d, mdl.coef_[0], mdl.coef_[1]

HARGA_BARU = {"Standard Range": 243_000_000, "Long Range": 281_500_000}

try:
    df_raw= load_data()
    df, coef_yr, coef_km = build_model(df_raw)
except Exception as e:
    st.error(f"Gagal load data: {e}")
    st.stop()

# SIDEBAR
with st.sidebar:
    st.markdown("### Filters")
    sel_years = st.multiselect("Year", sorted(df["year"].dropna().unique().astype(int).tolist()),
                                  default=sorted(df["year"].dropna().unique().astype(int).tolist()))
    sel_variants = st.multiselect("Variant", df["variant_label"].unique().tolist(),
                                  default=df["variant_label"].unique().tolist())
    sel_sellers = st.multiselect("Seller type", df["seller_label"].unique().tolist(),
                                  default=df["seller_label"].unique().tolist())
    km_max = st.slider("Max mileage (km)", 0, int(df["km"].max()), int(df["km"].max()), step=5000)
    budget_max = st.number_input("Max budget (Rp Jt)", 50, 300, int(df["price_juta"].max()), step=5)

status_filter = 'active'

f = df[
    df["year"].isin(sel_years) &
    df["variant_label"].isin(sel_variants) &
    df["seller_label"].isin(sel_sellers) &
    (df["km"] <= km_max) &
    (df["price_juta"] <= budget_max)
]

n_hot= len(f[f["deal_label"] == "Hot Deal"])
dealer_med= f[f["seller_label"] == "Dealer"]["price_juta"].median()
indiv_med= f[f["seller_label"] == "Individual"]["price_juta"].median()
km_drop_10k= abs(coef_km) * 10_000 / 1_000_000
yr_gain= abs(coef_yr) / 1_000_000
pct_below= round((len(f[f["deal_label"].isin(["Hot Deal","Good Deal"])]) / max(len(f),1)) * 100)
depr_data= df.groupby(["year","variant_label"])["price_juta"].median().reset_index()
depr_data.columns = ["year","variant_label","median_secondhand"]
last_scraped = df["scraped_at"].max()
last_scraped = pd.to_datetime(last_scraped).strftime("%Y-%m-%d")


# HEADER

st.markdown(f"""
<div class="deck-header">
  <div>
    <div class="deck-title">🚗Wuling Air EV Secondhand Car Tracker💨💨💨</div>
    <div class="deck-subtitle">My fun little project. The data is scraped from OLX, processed and transformed using Python and Luigi, and then loaded into database for exploration. For personal and educational use only.</div>
    <div class="deck-subtitle">last update: {last_scraped}</div>
  </div>
""", unsafe_allow_html=True)


df_active = f[f['status'] == 'active']

k1, k2, k3, k4 = st.columns(4)
with k1: kpi("Total iklan", f"{len(df_active)}", "aktif di website")
with k2: kpi("Median", f"Rp {df_active['price_juta'].median():.0f} Jt", "dari semua iklan aktif")
with k3: kpi("Paling murah", f"Rp {df_active['price_juta'].min():.0f} Jt", "dari semua iklan aktif")
with k4: kpi("Paling mahal", f"Rp {df_active['price_juta'].max():.0f} Jt", "mungkin unit baru")
# with k4: kpi("Hot deals", str(n_hot), ">15% below fair value", accent=True)
# with k5: kpi("Price drop / 10k km", f"−Rp {km_drop_10k:.1f} Jt", f"+Rp {yr_gain:.1f} Jt per newer year")

st.markdown('<hr class="rule">', unsafe_allow_html=True)


c1, c2, c3, c4= st.columns(4)

with c1:
    chart_header(
        "Harga berdasarkan varian",
        f"Kebanyakan Long Range ada di kisaran <b>Rp 120–145 Jt</b>, "
        f"sementara Standard Range biasanya sekitar Rp 20 Jt lebih murah. "
        f"Harga di atas Rp 170 Jt biasanya unit mobil baru."
    )
    fig1 = px.histogram(
        f, x="price_juta", color="variant_label", nbins=18, barmode="overlay",
        labels={"price_juta": "Harga", "variant_label": "Varian"},
        color_discrete_map=COLORS, opacity=0.75,
    )
    fig1.update_layout(height=CHART_H, **CHART_THEME, legend_title_text="")
    fig1.update_xaxes(title_text="Harga", title_font_size=9)
    fig1.update_yaxes(title_text="Listings", title_font_size=9)
    st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

with c2:
    chart_header(
        "Hubungan harga berdasarkan km",
        f"Semakin tinggi kilometer, biasanya harga makin turun. "
        f"Long Range tetap lebih mahal dibanding Standard Range."
    )
    fig2 = px.scatter(
        f, x="km", y="price_juta", color="variant_label", trendline="ols",
        hover_data=["year", "city", "seller_label", "deal_score"],
        labels={"km": "KM", "price_juta": "Harga", "variant_label": "Varian"},
        color_discrete_map=COLORS, opacity=0.65,
    )
    fig2.update_traces(marker=dict(size=6))
    fig2.update_layout(height=CHART_H, **CHART_THEME, legend_title_text="")
    fig2.update_xaxes(title_text="KM", title_font_size=9, tickformat=",")
    fig2.update_yaxes(title_text="Harga", title_font_size=9)
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

with c3:
    chart_header(
        "Harga dealer vs pribadi",
        f"Harga mobil dari dealer di <b>Rp {dealer_med:.0f} Jt</b>, "
        f"sedangkan dari pemilik langsung sekitar <b>Rp {indiv_med:.0f} Jt</b>. "
        f"Listing dari individu cenderung lebih mahal."
    )
    ds = f.groupby("seller_label").agg(
        count=("price","count"), median=("price_juta","median")
    ).reset_index()
    fig3 = px.bar(
        ds, x="seller_label", y="median", color="seller_label",
        text="median", color_discrete_map=COLORS,
        labels={"median": "Median (Rp Jt)", "seller_label": ""},
    )
    fig3.update_traces(
        texttemplate="Rp %{text:.0f} Juta", textposition="inside",
        marker_line_width=0, width=0.4
    )
    fig3.update_layout(
        height=CHART_H, **CHART_THEME, showlegend=False,
        yaxis_range=[0, ds["median"].max() * 1.3]
    )
    fig3.update_xaxes(title_text="")
    fig3.update_yaxes(title_text="Harga", title_font_size=9)
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

with c4:
    chart_header(
        "Harga berdasarkan daerah",
        f"<b>Jatinegara</b> memiliki harga rata-rata paling murah "
        f"Kebanyakan iklan ada di Jakarta. "
    )
    city_df = (
        f.groupby("city")["price"].median().reset_index()
        .rename(columns={"price": "harga"})
        .sort_values("harga", ascending=False)
        .tail(10)
    )

    fig6 = px.bar(
        city_df, x="harga", y="city", orientation="h",
        labels={"harga": "Harga", "city": ""},
        color_discrete_sequence=["#1d4ed8"],
    )
    fig6.update_traces(marker_line_width=0)
    fig6.update_layout(height=CHART_H, **CHART_THEME)
    fig6.update_xaxes(title_text="Harga", title_font_size=9)
    st.plotly_chart(fig6, use_container_width=True, config={"displayModeBar": False})

st.markdown('<hr class="rule">', unsafe_allow_html=True)


left, right = st.columns([1, 2])

with left:
    deal_counts = {
        "Hot Deal":   len(f[f["deal_label"] == "Hot Deal"]),
        "Good Value":  len(f[f["deal_label"] == "Good Value"]),
        "Market Price": len(f[f["deal_label"] == "Market Price"]),
        "Overpriced": len(f[f["deal_label"] == "Overpriced"]),
    }
    deal_df = pd.DataFrame({
        "Category": list(deal_counts.keys()),
        "Count":    list(deal_counts.values())
    })
    deal_colors = {
        "Hot Deal":   "#035520",
        "Good Value":  "#19685d",
        "Market Price": "#dbeb25",
        "Overpriced": "#d97706"
    }

    chart_header(
        "Distribusi berdasarkan deal score",
        f"<b>{pct_below}% of listings</b> at or below fair value. "
        f"Only <b>{deal_counts['Hot Deal']} hot deals</b> (>15% below) — limited, act fast."
    )

    deal_df = pd.DataFrame({
        "Category": list(deal_counts.keys()),
        "Count":    list(deal_counts.values())
    })

    fig5 = px.bar(
        deal_df, x="Category", y="Count",
        color="Category", text="Count",
        color_discrete_map=deal_colors,
        labels={"Count": "Listings", "Category": ""},
    )

    fig5.update_traces(textposition="outside", marker_line_width=0)
    fig5.update_layout(
        height=250, 
        **CHART_THEME,
        showlegend=False,
        yaxis_range=[0, deal_df["Count"].max() * 1.3]
    )

    st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar": False})


with right:
    st.markdown('<div class="chart-title">Top listing berdasarkan deal score</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="chart-insight"> Perkiraan harga didapatkan dari perhitungan dari tahun, mileage, dan varian. '
        'Deal score = (perkiraan harga − harga) / perkiraan harga × 100.</div>',
        unsafe_allow_html=True
    )

    best = (
        f.sort_values("deal_score", ascending=False)
        [["deal_label","deal_score","price_juta","expected_price",
          "year","km","variant_label","seller_label","city","listing_url"]]
        .copy()
    )

    best["expected_price"] = (best["expected_price"] / 1_000_000).round(1)
    best.columns = ["Label","Deal Score (%)","Harga (juta)","Perkiraan Harga (juta)",
                    "Tahun","KM","Varian","Tipe Penjual","Daerah","Link"]

    st.dataframe(
        best,
        use_container_width=True,
        height=300,
        column_config={
            "Link": st.column_config.LinkColumn("Link"),
            "Score (%)": st.column_config.ProgressColumn(
                "Score (%)", min_value=-30, max_value=40, format="%.1f%%"
            ),
            "KM": st.column_config.NumberColumn("KM", format="%,.0f"),
        }
    )


st.markdown("""
<div style="display:flex;justify-content:space-between;margin-top:6px;">
  <span style="font-size:0.62rem;color:#9ca3af;">
    Some OLX prices reflect installment (kredit) rates, not cash price. Use as directional reference only.
  </span>
  <span style="font-size:0.62rem;color:#9ca3af;">
    Built by Adila Zahra Faradisa · github.com/dilafaradisa · educational purposes only
  </span>
</div>
""", unsafe_allow_html=True)