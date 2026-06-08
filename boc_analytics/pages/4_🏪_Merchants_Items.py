"""
pages/4_🏪_Merchants_Items.py — Merchant and item-level analysis
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from collections import Counter
from data_loader import load_all

st.set_page_config(page_title="BOC · Merchants & Items", page_icon="🏪", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.page-title{font-size:2rem;font-weight:800;background:linear-gradient(135deg,#06B6D4,#3B82F6);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:0.2rem;}
.page-sub{color:#64748b;font-size:0.95rem;margin-bottom:1.5rem;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0F0F1A,#1A1A2E);
  border-right:1px solid rgba(124,58,237,0.2);}
.merch-kpi{background:linear-gradient(135deg,#1A1A2E,#16213E);
  border:1px solid rgba(6,182,212,0.2);border-radius:16px;padding:1.2rem 1rem;
  text-align:center;position:relative;overflow:hidden;}
.merch-kpi::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;
  background:linear-gradient(90deg,#06B6D4,#3B82F6);}
.merch-kpi-val{font-size:1.8rem;font-weight:900;color:#06B6D4;}
.merch-kpi-lbl{font-size:0.7rem;text-transform:uppercase;letter-spacing:1.2px;color:#64748b;margin-top:2px;}
</style>
""", unsafe_allow_html=True)

dfs  = load_all()
be   = dfs.get("bill_extraction", pd.DataFrame())
bill = dfs.get("bill", pd.DataFrame())

st.markdown('<div class="page-title">🏪 Merchants & Items</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Top vendors, item-level purchases, merchant affinity and product trends</div>', unsafe_allow_html=True)

if be.empty:
    st.warning("No data found.")
    st.stop()

be_clean = be.dropna(subset=["merchantName"]).copy()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔽 Filters")
    top_n = st.slider("Top N Merchants", 5, 50, 20)
    all_cats = sorted(be["category"].dropna().unique().tolist())
    sel_cats = st.multiselect("Category Filter", all_cats, default=all_cats)
    st.markdown("---")
    st.markdown(f"**Unique Merchants:** {be_clean['merchantName'].nunique():,}")
    st.markdown(f"**With Line Items:** {(be['lineItems_parsed'].apply(len) > 0).sum():,}")

cat_filtered = be_clean[be_clean["category"].isin(sel_cats)] if sel_cats else be_clean

# ── Merchant Stats ─────────────────────────────────────────────────────────────
merchant_freq  = cat_filtered.groupby("merchantName").agg(
    bill_count=("totalAmount","count"),
    total_spend=("totalAmount","sum"),
    avg_spend=("totalAmount","mean"),
    category=("category", lambda x: x.mode()[0] if len(x) else "other"),
).reset_index().sort_values("bill_count", ascending=False)

top_merch = merchant_freq.head(top_n)

# ── KPI Strip ─────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
kpi_data = [
    ("🏪", f"{be_clean['merchantName'].nunique():,}", "Unique Merchants"),
    ("🧾", f"{len(cat_filtered):,}", "Total Bills"),
    ("🏷️", f"{cat_filtered['category'].nunique():,}", "Categories"),
    ("📦", f"{(be['lineItems_parsed'].apply(len) > 0).sum():,}", "Bills with Items"),
]
for col, (icon, val, lbl) in zip([k1, k2, k3, k4], kpi_data):
    col.markdown(f"""
    <div class="merch-kpi">
      <div style="font-size:1.6rem">{icon}</div>
      <div class="merch-kpi-val">{val}</div>
      <div class="merch-kpi-lbl">{lbl}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Row 1: Top Merchants by Bill Count  +  Category Donut ─────────────────────
r1, r2 = st.columns([3, 2])

with r1:
    fig = go.Figure(go.Bar(
        x=top_merch["bill_count"][::-1],
        y=top_merch["merchantName"][::-1],
        orientation="h",
        marker=dict(
            color=top_merch["bill_count"][::-1],
            colorscale=[[0,"#0d1b4b"],[0.4,"#3B82F6"],[1,"#06B6D4"]],
            showscale=False,
        ),
        text=top_merch["bill_count"][::-1],
        textposition="outside",
        textfont=dict(color="#e2e8f0", size=10),
    ))
    fig.update_layout(
        title=f"🏆 Top {top_n} Merchants by Bill Count",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0"), title_font=dict(color="#06B6D4", size=15),
        height=max(420, top_n * 22),
        margin=dict(l=10,r=80,t=50,b=10),
        xaxis=dict(title="Number of Bills", gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.0)", tickfont=dict(size=10)),
    )
    st.plotly_chart(fig, width='stretch')

with r2:
    # Category breakdown donut
    cat_cnt = cat_filtered["category"].value_counts().reset_index()
    cat_cnt.columns = ["category", "count"]
    cat_top = cat_cnt.head(10)

    fig2 = px.pie(
        cat_top, values="count", names="category",
        title="🏷️ Bills by Category",
        hole=0.55,
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    fig2.update_traces(
        textinfo="label+percent",
        textfont=dict(size=10),
        pull=[0.05] + [0] * (len(cat_top) - 1),
    )
    fig2.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0", family="Inter"),
        title_font=dict(color="#06B6D4", size=15),
        height=420,
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(font=dict(size=9), bgcolor="rgba(0,0,0,0)"),
        annotations=[dict(
            text="<b>Categories</b>",
            x=0.5, y=0.5,
            font=dict(size=13, color="#06B6D4"),
            showarrow=False,
        )],
    )
    st.plotly_chart(fig2, width='stretch')

st.markdown("<br>", unsafe_allow_html=True)

# ── Item Analysis ──────────────────────────────────────────────────────────────
st.markdown("### 🛒 Item-Level Analysis")

# Extract all items
all_items = []
for items in be["lineItems_parsed"].dropna():
    if isinstance(items, list):
        all_items.extend([str(i).strip() for i in items if i and len(str(i).strip()) > 2])

item_counter = Counter(all_items)
item_df = pd.DataFrame(item_counter.most_common(50), columns=["item","count"])

i1, i2 = st.columns(2)

with i1:
    top_items = item_df.head(25)
    if len(top_items) > 0:
        fig = go.Figure(go.Bar(
            y=top_items["item"][::-1],
            x=top_items["count"][::-1],
            orientation="h",
            marker=dict(
                color=top_items["count"][::-1],
                colorscale=[[0,"#0d1b4b"],[0.5,"#06B6D4"],[1,"#34d399"]],
            ),
            text=top_items["count"][::-1],
            textposition="outside",
            textfont=dict(size=9, color="#e2e8f0"),
        ))
        fig.update_layout(
            title="📦 Top 25 Most Purchased Items",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e2e8f0"), title_font=dict(color="#06B6D4", size=15),
            height=600, margin=dict(l=10,r=80,t=50,b=10),
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(tickfont=dict(size=9)),
        )
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No line item data available yet.")

with i2:
    # Merchant drill-down
    st.markdown("#### 🔍 Merchant → Item Drill-Down")
    sel_merchant = st.selectbox(
        "Select a merchant:",
        options=merchant_freq.head(50)["merchantName"].tolist(),
        key="merch_select"
    )
    if sel_merchant:
        merch_bills = be[be["merchantName"] == sel_merchant].copy()
        m_items = []
        for items in merch_bills["lineItems_parsed"].dropna():
            if isinstance(items, list):
                m_items.extend([str(i).strip() for i in items if i and len(str(i).strip()) > 2])
        if m_items:
            mc = Counter(m_items)
            mdf = pd.DataFrame(mc.most_common(20), columns=["item","count"])
            fig = px.bar(
                mdf, x="count", y="item", orientation="h",
                title=f"🧾 Items at {sel_merchant}",
                color="count",
                color_continuous_scale=["#0d1b4b","#3B82F6","#06B6D4"],
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"), title_font=dict(color="#06B6D4", size=14),
                height=500, margin=dict(l=10,r=10,t=50,b=10),
                xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.0)", tickfont=dict(size=9)),
                coloraxis_showscale=False,
                showlegend=False,
            )
            st.plotly_chart(fig, width='stretch')
            # Stats
            st.markdown(f"""
            <div style="display:flex;gap:1rem;flex-wrap:wrap;margin-top:0.5rem;">
            <span style="background:rgba(6,182,212,0.1);border:1px solid rgba(6,182,212,0.3);
              border-radius:20px;padding:0.3rem 0.8rem;font-size:0.8rem;color:#06B6D4;">
              📋 {len(merch_bills)} bills</span>
            <span style="background:rgba(52,211,153,0.1);border:1px solid rgba(52,211,153,0.3);
              border-radius:20px;padding:0.3rem 0.8rem;font-size:0.8rem;color:#34d399;">
              💰 Avg {merch_bills['totalAmount'].mean():,.1f}</span>
            <span style="background:rgba(124,58,237,0.1);border:1px solid rgba(124,58,237,0.3);
              border-radius:20px;padding:0.3rem 0.8rem;font-size:0.8rem;color:#a78bfa;">
              🏷️ {merch_bills['category'].mode()[0] if len(merch_bills) else 'N/A'}</span>
            </div>""", unsafe_allow_html=True)
        else:
            st.info("No line item data available for this merchant.")

st.markdown("<br>", unsafe_allow_html=True)

# ── Merchant Table ──────────────────────────────────────────────────────────────
with st.expander("📋 Full Merchant Table"):
    disp = merchant_freq.copy()
    disp["total_spend"] = disp["total_spend"].apply(lambda x: f"{x:,.2f}")
    disp["avg_spend"]   = disp["avg_spend"].apply(lambda x: f"{x:,.2f}")
    disp.columns = ["Merchant","Bill Count","Total Spend","Avg Spend","Top Category"]
    st.dataframe(disp, width='stretch', hide_index=True, height=400)
