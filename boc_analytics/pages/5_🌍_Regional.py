"""
pages/5_🌍_Regional.py — Regional and currency-wise analytics
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from data_loader import load_all, CURRENCY_COUNTRY, CURRENCY_ISO3

st.set_page_config(page_title="BOC · Regional", page_icon="🌍", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.page-title{font-size:2rem;font-weight:800;background:linear-gradient(135deg,#10B981,#06B6D4);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:0.2rem;}
.page-sub{color:#64748b;font-size:0.95rem;margin-bottom:1.5rem;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0F0F1A,#1A1A2E);
  border-right:1px solid rgba(124,58,237,0.2);}
</style>
""", unsafe_allow_html=True)

dfs = load_all()
be  = dfs.get("bill_extraction", pd.DataFrame())

st.markdown('<div class="page-title">🌍 Regional Analytics</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Currency and country-wise spend, bill volume, and geographic distribution</div>', unsafe_allow_html=True)

if be.empty or "currency" not in be.columns:
    st.warning("No currency data available.")
    st.stop()

# Enrich with country info — 46 currencies → 46 countries + Unmapped for NULL currency
be_geo = be.copy()
be_geo["country"] = be_geo["currency"].map(CURRENCY_COUNTRY).fillna("Unmapped")
be_geo["iso3"]    = be_geo["currency"].map(CURRENCY_ISO3)

# Currency aggregates
curr_agg = be_geo.groupby(["currency","country","iso3"]).agg(
    bill_count=("totalAmount","count"),
    total_spend=("totalAmount","sum"),
    avg_spend=("totalAmount","mean"),
    unique_merchants=("merchantName","nunique"),
).reset_index().sort_values("bill_count", ascending=False)

# Derived KPI values (computed here so the KPI block can use them)
n_countries     = int(be_geo["country"].nunique())
n_currencies    = int(be_geo["currency"].nunique())
total_bills     = len(be_geo)
total_spend_num = float(be_geo["totalAmount"].sum())
top_country     = be_geo["country"].value_counts().idxmax()
top_curr        = be_geo["currency"].value_counts().idxmax()

# ── KPI ─────────────────────────────────────────────────────────────────────────
k1,k2,k3,k4 = st.columns(4)
for col,(icon,val,lbl) in zip([k1,k2,k3,k4],[
    ("🌍", str(n_countries), "Countries / Regions"),
    ("💱", str(n_currencies), "Currencies"),
    ("🧾", f"{total_bills:,}", "Total Bills"),
    ("💰", f"{total_spend_num:,.0f}", "Global Spend (mixed currencies)"),
]):
    col.markdown(f"""<div style="background:linear-gradient(135deg,#1A1A2E,#16213E);
    border:1px solid rgba(16,185,129,0.2);border-radius:14px;padding:1rem;text-align:center;
    position:relative;overflow:hidden;">
    <div style="position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,#10B981,#06B6D4);"></div>
    <div style="font-size:1.5rem">{icon}</div>
    <div style="font-size:1.7rem;font-weight:800;color:#10B981">{val}</div>
    <div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:1px;color:#64748b;margin-top:2px">{lbl}</div>
    </div>""", unsafe_allow_html=True)

# Note about currency mapping
unmapped_count = int((be_geo["country"] == "Unmapped").sum())
st.markdown(f"""
<div style="background:rgba(16,185,129,0.07);border-left:3px solid #10B981;
border-radius:0 8px 8px 0;padding:0.7rem 1rem;margin:0.5rem 0 1rem 0;font-size:0.82rem;color:#94a3b8">
<b style="color:#10B981">ℹ️ About the {n_countries} countries:</b>
46 real countries/regions (one per currency) + 1 <b>"Unmapped"</b> group
({unmapped_count:,} bills with no currency — these are failed extractions
where the AI couldn't read the invoice currency, shown as <code>[Company Name]</code> merchants).
<b>Currency totals cannot be summed in a single dollar figure</b> since they represent different local currencies
(73.6% of bills are IDR — Indonesian Rupiah).
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── World Choropleth Map ───────────────────────────────────────────────────────
map_df = curr_agg.dropna(subset=["iso3"])
map_metric = st.radio("Map metric:", ["Bill Count","Total Spend","Avg Spend","Unique Merchants"],
                       horizontal=True)
metric_col = {"Bill Count":"bill_count","Total Spend":"total_spend",
              "Avg Spend":"avg_spend","Unique Merchants":"unique_merchants"}[map_metric]

fig_map = px.choropleth(
    map_df, locations="iso3", color=metric_col,
    hover_name="country",
    hover_data={"currency":True,"bill_count":True,"total_spend":":.0f","avg_spend":":.1f"},
    color_continuous_scale=["#0F0F1A","#10B981","#06B6D4"],
    title=f"🗺️ World Map — {map_metric} by Country",
    projection="natural earth",
)
fig_map.update_layout(
    paper_bgcolor="#0F0F1A",
    plot_bgcolor="#0F0F1A",
    geo=dict(bgcolor="#0F0F1A", lakecolor="#0F0F1A",
             landcolor="#1A1A2E", coastlinecolor="#334155",
             showframe=False, showcoastlines=True),
    font=dict(color="#e2e8f0"),
    title_font=dict(color="#10B981", size=16),
    height=480,
    margin=dict(l=0,r=0,t=50,b=0),
    coloraxis_colorbar=dict(
        title=map_metric, tickfont=dict(color="#e2e8f0"),
        title_font=dict(color="#e2e8f0"),
    ),
)
st.plotly_chart(fig_map, width='stretch')

# ── Side-by-side: Bill Share by Country  +  Country × Category Heatmap ────────
ch1, ch2 = st.columns(2)

with ch1:
    fig = px.pie(
        curr_agg.head(12), values="bill_count", names="country",
        title="🌐 Bill Share by Country",
        hole=0.5,
        color_discrete_sequence=px.colors.qualitative.Vivid,
    )
    fig.update_traces(textinfo="label+percent", textfont=dict(size=10))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0"), title_font=dict(color="#10B981", size=15),
        height=400, margin=dict(l=10, r=10, t=55, b=10),
        legend=dict(font=dict(size=9), bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig, width='stretch')

with ch2:
    top_countries = curr_agg.head(10)["country"].tolist()
    hmap = be_geo[be_geo["country"].isin(top_countries)].groupby(
        ["country", "category"]
    ).size().reset_index(name="count")
    hpivot = hmap.pivot(index="country", columns="category", values="count").fillna(0)
    fig = px.imshow(
        hpivot, title="🔥 Country × Category Heatmap",
        color_continuous_scale=["#0F0F1A", "#10B981", "#06B6D4"],
        aspect="auto", text_auto=True,
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"),
        title_font=dict(color="#10B981", size=15),
        height=400, margin=dict(l=10, r=10, t=55, b=10),
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig, width='stretch')

# ── Regional Table ─────────────────────────────────────────────────────────────
st.markdown("### 📋 Regional Summary Table")
disp = curr_agg.copy()
disp["total_spend"] = disp["total_spend"].apply(lambda x: f"${x:,.2f}")
disp["avg_spend"]   = disp["avg_spend"].apply(lambda x: f"${x:,.2f}")
disp.columns = ["Currency","Country","ISO3","Bill Count","Total Spend","Avg Spend","Unique Merchants"]
disp = disp.drop(columns=["ISO3"])
st.dataframe(disp, width='stretch', hide_index=True, height=400)

with st.sidebar:
    st.markdown("### 🌍 Regional")
    for _, row in curr_agg.head(5).iterrows():
        st.markdown(f"🏴 **{row['currency']}** — {row['country']}: {int(row['bill_count'])} bills")
