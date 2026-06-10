"""
pages/8_💰_Spend_Optimization.py — Spend Optimization
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import plotly.express as px
import pandas as pd
from data_loader import load_all
from shared_styles import inject_shared_styles, inject_sidebar_brand

st.set_page_config(page_title="BOC · Spend Optimization", page_icon="💰", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;background:#FFFFFF;color:#1E293B;}
.page-title{font-size:2rem;font-weight:800;color:#1E293B;margin-bottom:0.2rem;}
.page-sub{color:#64748B;font-size:0.95rem;margin-bottom:1.5rem;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0F172A,#1E293B) !important;
  border-right:1px solid #334155;}

/* KPI Cards */
.kpi-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.kpi-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg,#CBD5E1,#94A3B8);
}
.kpi-val { font-size: 1.5rem; font-weight: 800; color: #1E293B; }
.kpi-lbl { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; color: #94A3B8; margin-top: 8px; }
</style>
""", unsafe_allow_html=True)

inject_shared_styles()
inject_sidebar_brand()

dfs = load_all()
be = dfs.get("bill_extraction", pd.DataFrame())

st.markdown('<div class="page-title">💰 Spend Optimization</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">A detailed, easy-to-understand breakdown of your spending habits across categories and merchants.</div>', unsafe_allow_html=True)

if be.empty:
    st.warning("No bill extraction data found.")
    st.stop()

# Data Prep
opt_df = be.dropna(subset=["category", "totalAmount", "merchantName"]).copy()
opt_df = opt_df[opt_df["totalAmount"] > 0]
opt_df = opt_df[opt_df["totalAmount"] < opt_df["totalAmount"].quantile(0.99)] # Remove massive anomalies

with st.sidebar:
    st.markdown("### 🔽 Filter by Currency")
    currencies = sorted(opt_df["currency"].dropna().unique().tolist())
    default_curr = "USD" if "USD" in currencies else (currencies[0] if currencies else None)
    selected_curr = st.selectbox("Select Currency", currencies, index=currencies.index(default_curr) if default_curr in currencies else 0)

df_curr = opt_df[opt_df["currency"] == selected_curr].copy()

if df_curr.empty:
    st.info(f"No data for {selected_curr}.")
    st.stop()

# Basic Metrics
total_spend = df_curr["totalAmount"].sum()
tx_count = len(df_curr)
avg_spend = total_spend / tx_count if tx_count > 0 else 0

st.markdown("### 📊 Executive Summary")
st.info("This section provides a high-level view of your total expenditure. It shows exactly how much money has left your account and the average size of your transactions.")

k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-val">${total_spend:,.0f} {selected_curr}</div>
        <div class="kpi-lbl">Total Spend</div>
    </div>
    """, unsafe_allow_html=True)
with k2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-val">{tx_count:,}</div>
        <div class="kpi-lbl">Total Transactions</div>
    </div>
    """, unsafe_allow_html=True)
with k3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-val">${avg_spend:,.0f} {selected_curr}</div>
        <div class="kpi-lbl">Average Transaction Value</div>
    </div>
    """, unsafe_allow_html=True)

# ── Category Analysis ────────────────────────────────────────────────────────
st.markdown("### 🏷️ Category-Wise Spend Analysis")
st.info('Understanding **what** you spend your money on is the first step to optimization. The chart below shows your total spending divided into distinct categories. Look for large bars in categories like "Food", "Entertainment", or "Shopping" to identify where you can easily cut back.')

cat_spend = df_curr.groupby("category")["totalAmount"].sum().reset_index().sort_values("totalAmount", ascending=True)
# Calculate percentages for explainability
cat_spend["Percentage"] = (cat_spend["totalAmount"] / total_spend) * 100

c1, c2 = st.columns([6, 4])
with c1:
    fig_cat = px.bar(
        cat_spend, 
        x="totalAmount", 
        y="category", 
        orientation="h",
        title="Total Spend per Category",
        color="totalAmount",
        color_continuous_scale="Teal",
        labels={"totalAmount": f"Amount ({selected_curr})", "category": "Category"}
    )
    fig_cat.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#334155"),
        xaxis=dict(gridcolor="rgba(0,0,0,0.06)"), yaxis=dict(title="", tickfont=dict(color="#475569")), coloraxis_showscale=False
    )
    st.plotly_chart(fig_cat, width='stretch')

with c2:
    st.markdown("#### 📊 Category Breakdown")
    # Display a clean table showing the breakdown
    disp_cat = cat_spend.sort_values("totalAmount", ascending=False).copy()
    disp_cat["Spend"] = disp_cat["totalAmount"].apply(lambda x: f"${x:,.0f}")
    disp_cat["Share"] = disp_cat["Percentage"].apply(lambda x: f"{x:.1f}%")
    st.dataframe(disp_cat[["category", "Spend", "Share"]].rename(columns={"category": "Category"}), hide_index=True, width='stretch')

# ── Merchant Analysis ────────────────────────────────────────────────────────
st.markdown("### 🏪 Merchant Spend Analysis")
st.info('Knowing **where** you spend your money helps identify specific stores where you might be overspending. The chart below highlights the merchants that consume the largest portion of your budget. If you see a merchant you visit frequently, consider switching to a cheaper alternative or signing up for their loyalty program.')

merch_spend = df_curr.groupby("merchantName")["totalAmount"].sum().reset_index().sort_values("totalAmount", ascending=True).tail(10)

m1, m2 = st.columns([6, 4])
with m1:
    fig_merch = px.bar(
        merch_spend, 
        x="totalAmount", 
        y="merchantName", 
        orientation="h",
        title="Top 10 Merchants by Spend",
        color="totalAmount",
        color_continuous_scale=[[0, "#93C5FD"], [0.4, "#3B82F6"], [1, "#1E3A8A"]],
        labels={"totalAmount": f"Amount ({selected_curr})", "merchantName": "Merchant"}
    )
    fig_merch.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#334155"),
        xaxis=dict(gridcolor="rgba(0,0,0,0.06)"), yaxis=dict(title="", tickfont=dict(color="#475569")), coloraxis_showscale=False
    )
    st.plotly_chart(fig_merch, width='stretch')

with m2:
    st.markdown("#### 🏆 Your Top Merchants")
    disp_m = merch_spend.sort_values("totalAmount", ascending=False).copy()
    disp_m["Spend"] = disp_m["totalAmount"].apply(lambda x: f"${x:,.0f}")
    st.dataframe(disp_m[["merchantName", "Spend"]].rename(columns={"merchantName": "Merchant Name"}), hide_index=True, width='stretch')

# ── Actionable Advice ────────────────────────────────────────────────────────
st.markdown("### 💡 How to Optimize Your Spend")

insights = []
cat_desc = cat_spend.sort_values("totalAmount", ascending=False)
if not cat_desc.empty:
    top_c = cat_desc.iloc[0]
    insights.append(f"🔴 **Reduce Top Category:** Your highest spend is in **{top_c['category']}** (${top_c['totalAmount']:,.0f}, which is {top_c['Percentage']:.1f}% of your budget). Try setting a strict monthly limit for this specific category.")

if "food" in [c.lower() for c in cat_desc["category"]]:
    food_row = cat_desc[cat_desc["category"].str.lower() == "food"].iloc[0]
    if food_row["Percentage"] > 15:
        insights.append(f"🍔 **Cut Dining Costs:** Food takes up **{food_row['Percentage']:.1f}%** of your spend. Cooking at home just two more days a week can drastically reduce this number.")

top_m = merch_spend.sort_values("totalAmount", ascending=False)
if not top_m.empty:
    top_merch = top_m.iloc[0]
    insights.append(f"🏬 **Evaluate Top Vendor:** You spent **${top_merch['totalAmount']:,.0f}** at **{top_merch['merchantName']}**. Are there cheaper alternatives for the products you buy here?")

for ins in insights:
    st.markdown(f"""
    <div style="background:rgba(5,150,105,0.06); border-left:4px solid #059669; padding:1.2rem; margin-bottom:1rem; border-radius:0 8px 8px 0; color:#334155; font-size:1rem;">
        {ins}
    </div>
    """, unsafe_allow_html=True)
