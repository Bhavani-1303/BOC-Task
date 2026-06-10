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
from shared_styles import inject_shared_styles, inject_sidebar_brand

st.set_page_config(page_title="BOC · Merchants & Items", page_icon="🏪", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;background:#FFFFFF;color:#1E293B;}
.page-title{font-size:2rem;font-weight:800;color:#1E293B;margin-bottom:0.2rem;}
.page-sub{color:#64748B;font-size:0.95rem;margin-bottom:1.5rem;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0F172A,#1E293B) !important;
  border-right:1px solid #334155;}
.merch-kpi{background:#FFFFFF;
  border:1px solid #E2E8F0;border-radius:16px;padding:1.2rem 1rem;
  text-align:center;position:relative;overflow:hidden;
  box-shadow:0 1px 3px rgba(0,0,0,0.06);}
.merch-kpi::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;
  background:linear-gradient(90deg,#CBD5E1,#94A3B8);}
.merch-kpi-val{font-size:1.8rem;font-weight:900;color:#1E293B;}
.merch-kpi-lbl{font-size:0.7rem;text-transform:uppercase;letter-spacing:1.2px;color:#94A3B8;margin-top:2px;}
</style>
""", unsafe_allow_html=True)

inject_shared_styles()
inject_sidebar_brand()

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
    
    all_merchants = sorted(be_clean["merchantName"].dropna().unique().tolist())
    sel_merchants = st.multiselect("Search Merchant(s)", all_merchants, default=[], placeholder="All Merchants")
    
    all_cats = sorted(be["category"].dropna().unique().tolist())
    sel_cats = st.multiselect("Category Filter", all_cats, default=[], placeholder="All Categories")
    st.markdown("---")
    st.markdown(f"**Unique Merchants:** {be_clean['merchantName'].nunique():,}")
    st.markdown(f"**With Line Items:** {(be['lineItems_parsed'].apply(len) > 0).sum():,}")

cat_filtered = be_clean.copy()
if sel_cats:
    cat_filtered = cat_filtered[cat_filtered["category"].isin(sel_cats)]
if sel_merchants:
    cat_filtered = cat_filtered[cat_filtered["merchantName"].isin(sel_merchants)]

# ── Merchant Stats ─────────────────────────────────────────────────────────────
merchant_freq  = cat_filtered.groupby("merchantName").agg(
    bill_count=("totalAmount","count"),
    total_spend=("totalAmount","sum"),
    avg_spend=("totalAmount","mean"),
    category=("category", lambda x: x.mode()[0] if len(x) else "other"),
).reset_index().sort_values("bill_count", ascending=False)

top_merch = merchant_freq.head(top_n)

# ── KPI Strip ─────────────────────────────────────────────────────────────────
k1, k2, k3 = st.columns(3)
kpi_data = [
    ("🏪", f"{be_clean['merchantName'].nunique():,}", "Unique Merchants"),
    ("🧾", f"{len(be):,}", "Completed Bills"),
    ("🏷️", f"{cat_filtered['category'].nunique():,}", "Categories"),
]
for col, (icon, val, lbl) in zip([k1, k2, k3], kpi_data):
    col.markdown(f"""
    <div class="merch-kpi">
      <div style="font-size:1.6rem">{icon}</div>
      <div class="merch-kpi-val">{val}</div>
      <div class="merch-kpi-lbl">{lbl}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

st.info('🏪 **Merchant Intelligence** — Discover which merchants drive the most transactions and revenue. The bar chart ranks vendors by bill count, while the donut reveals category distribution across your merchant base.')

# ── Row 1: Top Merchants by Bill Count  +  Category Donut ─────────────────────
r1, r2 = st.columns([3, 2])

with r1:
    fig = go.Figure(go.Bar(
        x=top_merch["bill_count"][::-1],
        y=top_merch["merchantName"][::-1],
        orientation="h",
        marker=dict(
            color=top_merch["bill_count"][::-1],
            colorscale=[[0,"#CFFAFE"],[0.4,"#22D3EE"],[1,"#0891B2"]],
            showscale=False,
        ),
        text=top_merch["bill_count"][::-1],
        textposition="outside",
        textfont=dict(color="#334155", size=10),
    ))
    fig.update_layout(
        title=f"🏆 Top {top_n} Merchants by Bill Count",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#334155"), title_font=dict(color="#1E293B", size=15),
        height=max(420, top_n * 22),
        margin=dict(l=10,r=80,t=50,b=10),
        xaxis=dict(title="Number of Bills", gridcolor="rgba(0,0,0,0.06)"),
        yaxis=dict(gridcolor="rgba(0,0,0,0.0)", tickfont=dict(size=10, color="#475569")),
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
        textfont=dict(size=10, color="#334155"),
        pull=[0.05] + [0] * (len(cat_top) - 1),
    )
    fig2.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#334155", family="Inter"),
        title_font=dict(color="#1E293B", size=15),
        height=420,
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(font=dict(size=9, color="#475569"), bgcolor="rgba(0,0,0,0)"),
        annotations=[dict(
            text="<b>Categories</b>",
            x=0.5, y=0.5,
            font=dict(size=13, color="#1E293B"),
            showarrow=False,
        )],
    )
    st.plotly_chart(fig2, width='stretch')

st.markdown("<br>", unsafe_allow_html=True)

# ── Item Analysis ──────────────────────────────────────────────────────────────
st.markdown("### 🛒 Item-Level Analysis")

# Extract all items
all_items = []
for items in cat_filtered["lineItems_parsed"].dropna():
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
                colorscale=[[0,"#CFFAFE"],[0.5,"#0891B2"],[1,"#059669"]],
            ),
            text=top_items["count"][::-1],
            textposition="outside",
            textfont=dict(size=9, color="#334155"),
        ))
        fig.update_layout(
            title="📦 Top 25 Most Purchased Items",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#334155"), title_font=dict(color="#1E293B", size=15),
            height=600, margin=dict(l=10,r=80,t=50,b=10),
            xaxis=dict(gridcolor="rgba(0,0,0,0.06)"),
            yaxis=dict(tickfont=dict(size=9, color="#475569")),
        )
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No line item data available yet.")

with i2:
    # Merchant drill-down — only show merchants that have line items
    st.markdown("#### 🔍 Merchant → Item Drill-Down")

    # Build list of merchants that actually have items
    merchants_with_items = []
    for merch_name in cat_filtered["merchantName"].unique():
        merch_rows = cat_filtered[cat_filtered["merchantName"] == merch_name]
        has_items = False
        for items in merch_rows["lineItems_parsed"].dropna():
            if isinstance(items, list) and any(i and len(str(i).strip()) > 2 for i in items):
                has_items = True
                break
        if has_items:
            merchants_with_items.append(merch_name)

    # Deduplicate: group merchants by lowercase name, keep the most common casing
    from collections import defaultdict
    merch_case_map = defaultdict(list)
    for m in merchants_with_items:
        merch_case_map[m.strip().lower()].append(m)
    deduped_merchants = []
    seen_lower = set()
    for m_lower, variants in merch_case_map.items():
        if m_lower not in seen_lower:
            seen_lower.add(m_lower)
            best = max(variants, key=lambda v: len(cat_filtered[cat_filtered["merchantName"] == v]))
            deduped_merchants.append(best)
    deduped_merchants = sorted(deduped_merchants)

    sel_merchant = st.selectbox(
        "Select a merchant:",
        options=deduped_merchants,
        key="merch_select"
    )
    if sel_merchant:
        merch_bills = cat_filtered[cat_filtered["merchantName"].str.lower() == sel_merchant.lower()].copy()
        m_items = []
        for items in merch_bills["lineItems_parsed"].dropna():
            if isinstance(items, list):
                m_items.extend([str(i).strip() for i in items if i and len(str(i).strip()) > 2])
        if m_items:
            mc = Counter(m_items)
            mdf = pd.DataFrame(mc.most_common(20), columns=["Item", "Count"])
            st.markdown(f"**🧾 Items at {sel_merchant}** ({len(mdf)} unique items)")
            table_height = min(500, 38 + len(mdf) * 35 + 2)
            st.dataframe(mdf, width='stretch', hide_index=True, height=table_height)
            st.markdown(f"""
            <div style="display:flex;gap:1rem;flex-wrap:wrap;margin-top:0.5rem;">
            <span style="background:rgba(8,145,178,0.08);border:1px solid rgba(8,145,178,0.25);
              border-radius:20px;padding:0.3rem 0.8rem;font-size:0.8rem;color:#0891B2;">
              📋 {len(merch_bills)} bills</span>
            <span style="background:rgba(5,150,105,0.08);border:1px solid rgba(5,150,105,0.25);
              border-radius:20px;padding:0.3rem 0.8rem;font-size:0.8rem;color:#059669;">
              💰 Avg {merch_bills['totalAmount'].mean():,.1f}</span>
            <span style="background:rgba(79,70,229,0.08);border:1px solid rgba(79,70,229,0.25);
              border-radius:20px;padding:0.3rem 0.8rem;font-size:0.8rem;color:#4F46E5;">
              🏷️ {merch_bills['category'].mode()[0] if len(merch_bills) else 'N/A'}</span>
            </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Merchant Table (ALL merchants, with search) ────────────────────────────────
st.markdown("### 📋 Full Merchant Table")

all_merchant_stats = be_clean.groupby("merchantName").agg(
    bill_count=("totalAmount","count"),
    total_spend=("totalAmount","sum"),
    avg_spend=("totalAmount","mean"),
    category=("category", lambda x: x.mode()[0] if len(x) else "other"),
).reset_index().sort_values("bill_count", ascending=False)

search_term = st.text_input("🔍 Search merchants", placeholder="Type merchant name (e.g. Dmart, Indomaret)...", key="merch_search")

disp = all_merchant_stats.copy()
if search_term:
    disp = disp[disp["merchantName"].str.contains(search_term, case=False, na=False)]

disp_fmt = disp.copy()
disp_fmt["total_spend"] = disp_fmt["total_spend"].apply(lambda x: f"{x:,.2f}")
disp_fmt["avg_spend"]   = disp_fmt["avg_spend"].apply(lambda x: f"{x:,.2f}")
disp_fmt.columns = ["Merchant","Bill Count","Total Spend","Avg Spend","Top Category"]

_ROWS = 20
_total = len(disp_fmt)
_pages = max(1, (_total + _ROWS - 1) // _ROWS)
if "merch_pg" not in st.session_state:
    st.session_state["merch_pg"] = 1
_cpg = min(st.session_state["merch_pg"], _pages)
_s = (_cpg - 1) * _ROWS
_e = min(_s + _ROWS, _total)
st.dataframe(disp_fmt.iloc[_s:_e], width='stretch', hide_index=True)
st.number_input("Page", min_value=1, max_value=_pages, value=_cpg, step=1, key="merch_page",
                on_change=lambda: st.session_state.update({"merch_pg": st.session_state["merch_page"]}))
st.caption(f"Showing {_s+1}–{_e} of {_total:,} merchants  ·  Page {_cpg} of {_pages}")
