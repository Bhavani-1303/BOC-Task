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
from shared_styles import inject_shared_styles, inject_sidebar_brand

st.set_page_config(page_title="BOC · Regional", page_icon="🌍", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;background:#FFFFFF;color:#1E293B;}
.page-title{font-size:2rem;font-weight:800;color:#1E293B;margin-bottom:0.2rem;}
.page-sub{color:#64748B;font-size:0.95rem;margin-bottom:1.5rem;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0F172A,#1E293B) !important;
  border-right:1px solid #334155;}
.country-detail-card{background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;
  padding:1.2rem;box-shadow:0 2px 8px rgba(0,0,0,0.06);margin-bottom:1rem;}
.country-detail-card h3{margin:0 0 0.8rem 0;font-size:1.1rem;color:#1E293B;}
.detail-row{display:flex;justify-content:space-between;padding:0.35rem 0;border-bottom:1px solid #F1F5F9;font-size:0.88rem;}
.detail-row:last-child{border-bottom:none;}
.detail-label{color:#64748B;}
.detail-value{font-weight:700;color:#1E293B;}
</style>
""", unsafe_allow_html=True)

inject_shared_styles()
inject_sidebar_brand()

dfs = load_all()
be  = dfs.get("bill_extraction", pd.DataFrame())
bill = dfs.get("bill", pd.DataFrame())
user = dfs.get("user", pd.DataFrame())

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
k1,k2 = st.columns(2)
for col,(icon,val,lbl) in zip([k1,k2],[
    ("💱", str(n_currencies), "Currencies"),
    ("🧾", f"{total_bills:,}", "Total Bills"),
]):
    col.markdown(f"""<div style="background:#FFFFFF;
    border:1px solid #E2E8F0;border-radius:14px;padding:1rem;text-align:center;
    position:relative;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
    <div style="position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,#CBD5E1,#94A3B8);"></div>
    <div style="font-size:1.5rem">{icon}</div>
    <div style="font-size:1.7rem;font-weight:800;color:#1E293B">{val}</div>
    <div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:1px;color:#94A3B8;margin-top:2px">{lbl}</div>
    </div>""", unsafe_allow_html=True)

# Note about currency mapping
unmapped_count = int((be_geo["country"] == "Unmapped").sum())
st.markdown(f"""
<div style="background:rgba(5,150,105,0.06);border-left:3px solid #059669;
border-radius:0 8px 8px 0;padding:0.7rem 1rem;margin:0.5rem 0 1rem 0;font-size:0.82rem;color:#475569">
<b style="color:#475569">ℹ️ About the data:</b>
Only <b>completed (NFT-minted) bills</b> are shown. {n_countries} countries/regions detected from {n_currencies} currencies.
{f'{unmapped_count:,} bills have no currency information and are grouped as <b>"Unmapped"</b>.' if unmapped_count > 0 else ''}
<b>Currency totals cannot be summed in a single dollar figure</b> since they represent different local currencies.
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

st.info('🗺️ **Geographic Distribution** — The world map visualizes transaction density by country, derived from bill currencies. Toggle between bill count, total spend, average spend, or unique merchants to understand regional adoption patterns. Select a country below to see detailed stats.')

# ── Top Vendor Filter ─────────────────────────────────────────────────────────
top_vendors = be_geo["merchantName"].value_counts().head(10).index.tolist()
vendor_options = ["All Vendors"] + top_vendors
selected_vendor = st.radio("🏪 Filter by Top Vendor:", vendor_options, horizontal=True, key="vendor_filter")

# Apply vendor filter
if selected_vendor != "All Vendors":
    be_geo_filtered = be_geo[be_geo["merchantName"] == selected_vendor]
    # Recalculate aggregates for filtered data
    curr_agg_filtered = be_geo_filtered.groupby(["currency","country","iso3"]).agg(
        bill_count=("totalAmount","count"),
        total_spend=("totalAmount","sum"),
        avg_spend=("totalAmount","mean"),
        unique_merchants=("merchantName","nunique"),
    ).reset_index().sort_values("bill_count", ascending=False)
    map_source = curr_agg_filtered
else:
    map_source = curr_agg

# ── World Choropleth Map + Country Detail Panel ────────────────────────────────
map_df = map_source.dropna(subset=["iso3"])
map_metric = st.radio("Map metric:", ["Bill Count","Total Spend","Avg Spend","Unique Merchants"],
                       horizontal=True)
metric_col = {"Bill Count":"bill_count","Total Spend":"total_spend",
              "Avg Spend":"avg_spend","Unique Merchants":"unique_merchants"}[map_metric]

map_col, detail_col = st.columns([3, 1])

with map_col:
    fig_map = px.choropleth(
        map_df, locations="iso3", color=metric_col,
        hover_name="country",
        hover_data={"currency":True,"bill_count":True,"total_spend":":.0f","avg_spend":":.1f"},
        color_continuous_scale=["#F0FDF4","#34D399","#0891B2"],
        title=f"🗺️ World Map — {map_metric} by Country" + (f" ({selected_vendor})" if selected_vendor != "All Vendors" else ""),
        projection="natural earth",
    )
    fig_map.update_layout(
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        geo=dict(bgcolor="#FFFFFF", lakecolor="#EFF6FF",
                 landcolor="#F1F5F9", coastlinecolor="#CBD5E1",
                 showframe=False, showcoastlines=True),
        font=dict(color="#334155"),
        title_font=dict(color="#1E293B", size=16),
        height=480,
        margin=dict(l=0,r=0,t=50,b=0),
        coloraxis_colorbar=dict(
            title=map_metric, tickfont=dict(color="#475569"),
            title_font=dict(color="#475569"),
        ),
    )
    st.plotly_chart(fig_map, width='stretch')

with detail_col:
    # Country selector for detailed stats
    available_countries = sorted(map_source["country"].unique().tolist())
    if "Unmapped" in available_countries:
        available_countries.remove("Unmapped")

    selected_country = st.selectbox("🔍 Select Country", available_countries, key="country_detail")

    if selected_country:
        # Get country data from bill_extraction
        country_bills = be_geo[be_geo["country"] == selected_country]
        country_currency = country_bills["currency"].mode().iloc[0] if len(country_bills) > 0 else "N/A"

        # Get users from that country by matching bills to users
        if not bill.empty and "userId" in bill.columns and not user.empty:
            # Get billIds from this country's bill_extraction
            country_bill_ids = set(country_bills["billId"].unique()) if "billId" in country_bills.columns else set()
            # Match bill IDs to userId through bill table
            if len(country_bill_ids) > 0:
                country_user_ids = bill[bill["id"].isin(country_bill_ids)]["userId"].dropna().unique()
            else:
                country_user_ids = []
            country_users = user[user["id"].isin(country_user_ids)]
            total_country_users = len(country_users)
            # Users with bills are active by definition (they uploaded bills in this country)
            active_country = total_country_users  # All matched users have at least 1 bill in this country
            # Count how many of these are globally inactive (0 total bills)
            if "bill_count" in country_users.columns and len(country_users) > 0:
                inactive_country = int((country_users["bill_count"] == 0).sum())
                active_country = total_country_users - inactive_country
            else:
                inactive_country = 0
        else:
            total_country_users = 0
            active_country = 0
            inactive_country = 0

        # Country stats
        country_total_bills = len(country_bills)
        country_total_spend = float(country_bills["totalAmount"].sum()) if "totalAmount" in country_bills.columns else 0
        country_merchants = int(country_bills["merchantName"].nunique()) if "merchantName" in country_bills.columns else 0
        country_categories = int(country_bills["category"].nunique()) if "category" in country_bills.columns else 0

        st.markdown(f"""
        <div class="country-detail-card">
            <h3>🏴 {selected_country}</h3>
            <div class="detail-row"><span class="detail-label">Currency</span><span class="detail-value">{country_currency}</span></div>
            <div class="detail-row"><span class="detail-label">Total Users</span><span class="detail-value">{total_country_users:,}</span></div>
            <div class="detail-row"><span class="detail-label">Active Users</span><span class="detail-value" style="color:#10B981">{active_country:,}</span></div>
            <div class="detail-row"><span class="detail-label">Inactive Users</span><span class="detail-value" style="color:#EF4444">{inactive_country:,}</span></div>
            <div class="detail-row"><span class="detail-label">Total Bills</span><span class="detail-value">{country_total_bills:,}</span></div>
            <div class="detail-row"><span class="detail-label">Total Spend</span><span class="detail-value">{country_total_spend:,.0f}</span></div>
            <div class="detail-row"><span class="detail-label">Merchants</span><span class="detail-value">{country_merchants:,}</span></div>
            <div class="detail-row"><span class="detail-label">Categories</span><span class="detail-value">{country_categories:,}</span></div>
        </div>
        """, unsafe_allow_html=True)

        # Top categories in this country
        if "category" in country_bills.columns and len(country_bills) > 0:
            cat_counts = country_bills["category"].value_counts().head(5)
            st.markdown("**Top Categories:**")
            for cat, cnt in cat_counts.items():
                pct = cnt / country_total_bills * 100
                st.markdown(f"<div style='font-size:0.82rem;color:#475569;padding:2px 0'>"
                           f"<b style='color:#1E293B'>{cat}</b> — {cnt:,} ({pct:.1f}%)</div>",
                           unsafe_allow_html=True)

# ── Side-by-side: Bill Share by Country  +  Country × Category Heatmap ────────
ch1, ch2 = st.columns(2)

with ch1:
    # Group smaller countries as "Others" to prevent label clutter
    _top = map_source.head(8).copy()
    _other_count = map_source.iloc[8:]["bill_count"].sum() if len(map_source) > 8 else 0
    if _other_count > 0:
        _top = pd.concat([_top, pd.DataFrame([{"country": "Others", "bill_count": _other_count}])], ignore_index=True)

    fig = px.pie(
        _top, values="bill_count", names="country",
        title="🌐 Bill Share by Country",
        hole=0.5,
        color_discrete_sequence=px.colors.qualitative.Vivid,
    )
    fig.update_traces(textinfo="percent", textposition="inside", textfont=dict(size=11, color="#FFFFFF"))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#334155"), title_font=dict(color="#1E293B", size=15),
        height=450, margin=dict(l=10, r=10, t=80, b=20),
        legend=dict(font=dict(size=10, color="#475569"), bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig, width='stretch')

with ch2:
    top_countries = map_source.head(10)["country"].tolist()
    _src = be_geo_filtered if selected_vendor != "All Vendors" else be_geo
    hmap = _src[_src["country"].isin(top_countries)].groupby(
        ["country", "category"]
    ).size().reset_index(name="count")
    if not hmap.empty:
        hpivot = hmap.pivot(index="country", columns="category", values="count").fillna(0)
        fig = px.imshow(
            hpivot, title="🔥 Country × Category Heatmap",
            color_continuous_scale=["#F8FAFC", "#34D399", "#0891B2"],
            aspect="auto", text_auto=True,
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#334155"),
            title_font=dict(color="#1E293B", size=15),
            height=450, margin=dict(l=10, r=10, t=80, b=20),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No data available for the selected vendor in these countries.")

# ── Regional Table (ALL currencies) ────────────────────────────────────────────
st.markdown("### 📋 Regional Summary Table")

# Build table from ALL currencies (not grouped by iso3 which drops NaN)
CURRENCY_TO_USD = {
    "IDR": 1/15500, "INR": 1/83, "NGN": 1/1550, "VND": 1/24500, "PHP": 1/56,
    "USD": 1.0, "DZD": 1/135, "PKR": 1/280, "TRY": 1/32, "UAH": 1/41,
    "IRR": 1/42000, "BDT": 1/110, "GBP": 1.27, "MYR": 1/4.7, "EUR": 1.08,
    "HKD": 1/7.8, "MMK": 1/2100, "BRL": 1/5.0, "AED": 1/3.67, "CHF": 1.12,
    "ZAR": 1/18.5, "ETB": 1/57, "TWD": 1/32, "KES": 1/153, "EGP": 1/49,
    "THB": 1/36, "JPY": 1/155, "UZS": 1/12600, "XOF": 1/610, "KHR": 1/4100,
    "NPR": 1/133, "CAD": 1/1.36, "RUB": 1/92, "MXN": 1/17.2, "SGD": 1/1.35,
    "PEN": 1/3.75, "AUD": 1/1.53, "PLN": 1/4.0, "NZD": 1/1.63, "MAD": 1/10,
    "LKR": 1/310, "KRW": 1/1350, "CNY": 1/7.25, "SAR": 1/3.75, "SEK": 1/10.5,
    "CRC": 1/530, "ISK": 1/138, "KWD": 3.26, "LYD": 1/4.85, "SYP": 1/13000,
    "TND": 1/3.12, "ZMW": 1/26, "UGX": 1/3750, "XAF": 1/610, "AZN": 1/1.7,
}

all_curr_agg = be_geo.groupby(["currency","country"]).agg(
    bill_count=("totalAmount","count"),
    total_spend=("totalAmount","sum"),
    avg_spend=("totalAmount","mean"),
    unique_merchants=("merchantName","nunique"),
).reset_index().sort_values("bill_count", ascending=False)

# Add USD column
all_curr_agg["total_spend_usd"] = all_curr_agg.apply(
    lambda r: r["total_spend"] * CURRENCY_TO_USD.get(r["currency"], 0), axis=1
)

disp = all_curr_agg.copy()
disp["total_spend"] = disp.apply(lambda r: f"{r['total_spend']:,.0f} {r['currency']}", axis=1)
disp["total_spend_usd"] = disp["total_spend_usd"].apply(lambda x: f"${x:,.2f}")
disp["avg_spend"]   = disp["avg_spend"].apply(lambda x: f"{x:,.2f}")
disp = disp[["currency","country","bill_count","total_spend","total_spend_usd","avg_spend","unique_merchants"]]
disp.columns = ["Currency","Country","Bill Count","Total Spend (Local)","Total Spend (USD)","Avg Spend","Unique Merchants"]

_ROWS = 15
_total = len(disp)
_pages = max(1, (_total + _ROWS - 1) // _ROWS)
if "reg_pg" not in st.session_state:
    st.session_state["reg_pg"] = 1
_cpg = min(st.session_state["reg_pg"], _pages)
_s = (_cpg - 1) * _ROWS
_e = min(_s + _ROWS, _total)
st.dataframe(disp.iloc[_s:_e], width='stretch', hide_index=True)
st.number_input("Page", min_value=1, max_value=_pages, value=_cpg, step=1, key="regional_page",
                on_change=lambda: st.session_state.update({"reg_pg": st.session_state["regional_page"]}))
st.caption(f"Showing {_s+1}–{_e} of {_total:,} currencies  ·  Page {_cpg} of {_pages}")

with st.sidebar:
    st.markdown("### 🌍 Regional")
    for _, row in curr_agg.head(5).iterrows():
        st.markdown(f"🏴 **{row['currency']}** — {row['country']}: {int(row['bill_count'])} bills")
