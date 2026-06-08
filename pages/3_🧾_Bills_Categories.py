"""
pages/3_🧾_Bills_Categories.py — Bills & Category spend analysis
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from data_loader import load_all

st.set_page_config(page_title="BOC · Bills & Categories", page_icon="🧾", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.page-title{font-size:2rem;font-weight:800;background:linear-gradient(135deg,#F59E0B,#EF4444);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:0.2rem;}
.page-sub{color:#64748b;font-size:0.95rem;margin-bottom:1.5rem;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0F0F1A,#1A1A2E);
  border-right:1px solid rgba(124,58,237,0.2);}
</style>
""", unsafe_allow_html=True)

dfs  = load_all()
bill = dfs.get("bill", pd.DataFrame())
be   = dfs.get("bill_extraction", pd.DataFrame())

st.markdown('<div class="page-title">🧾 Bills & Categories</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Spend breakdown, category trends, and bill amount distributions</div>', unsafe_allow_html=True)

if be.empty:
    st.warning("No bill extraction data found.")
    st.stop()

# Sidebar filters
with st.sidebar:
    st.markdown("### 🔽 Filters")
    all_cats = sorted(be["category"].dropna().unique().tolist())
    sel_cats = st.multiselect("Categories", all_cats, default=all_cats)
    all_curr = sorted(be["currency"].dropna().unique().tolist())
    # Default = ALL currencies (not first 5) so users see full data by default
    sel_curr = st.multiselect("Currency", all_curr, default=all_curr)
    min_amt = float(be["totalAmount"].dropna().min())
    max_amt = float(be["totalAmount"].dropna().max())
    amt_range = st.slider("Amount Range", min_amt, max_amt,
                          (min_amt, max_amt),
                          help="Filter bills by invoice amount (in local currency)")

filtered = be[
    be["category"].isin(sel_cats) &
    be["currency"].isin(sel_curr) &
    be["totalAmount"].between(amt_range[0], amt_range[1])
].copy() if sel_cats and sel_curr else be.copy()

# ── KPI Strip ─────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
kv = [
    ("🧾", f"{len(filtered):,}", "Bills (filtered)"),
    ("💰", f"{filtered['totalAmount'].sum():,.0f}", "Total Spend (mixed currencies)"),
    ("📊", f"{filtered['totalAmount'].mean():,.1f}", "Avg Bill Amount"),
    ("📈", f"{filtered['totalAmount'].median():,.1f}", "Median Bill"),
    ("🏷️", str(filtered["category"].nunique()), "Categories"),
]
for col,(icon,val,lbl) in zip([k1,k2,k3,k4,k5],kv):
    col.markdown(f"""<div style="background:linear-gradient(135deg,#1A1A2E,#16213E);
    border:1px solid rgba(245,158,11,0.2);border-radius:14px;padding:1rem;text-align:center;
    position:relative;overflow:hidden;">
    <div style="position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,#F59E0B,#EF4444);"></div>
    <div style="font-size:1.4rem">{icon}</div>
    <div style="font-size:1.6rem;font-weight:800;color:#F59E0B">{val}</div>
    <div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:1px;color:#64748b;margin-top:2px">{lbl}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Row 1: Bills by Category (date-picker) + Category Total Count ───────────────
r1, r2 = st.columns(2)

with r1:
    # Join bill.createdAt (reliable) to bill_extraction for date filtering.
    # Keep the column name as bill_createdAt throughout to avoid collision with
    # bill_extraction's own createdAt column (would create duplicate column names).
    _date_col = "bill_createdAt"
    if not bill.empty and "createdAt" in bill.columns:
        bill_slim = bill[["id", "createdAt"]].rename(columns={"id": "billId", "createdAt": _date_col})
        inv_clean = (
            filtered
            .merge(bill_slim, on="billId", how="left")
            .dropna(subset=[_date_col, "category"])
            .copy()
        )
    elif "invoiceDate" in filtered.columns:
        # Fallback: clamp invoiceDate to realistic range (removes OCR garbage like year 202)
        inv_clean = filtered.dropna(subset=["invoiceDate", "category"]).copy()
        inv_clean = inv_clean[
            (inv_clean["invoiceDate"] >= pd.Timestamp("2020-01-01")) &
            (inv_clean["invoiceDate"] <= pd.Timestamp("2030-12-31"))
        ].copy()
        inv_clean[_date_col] = inv_clean["invoiceDate"]
    else:
        inv_clean = pd.DataFrame()

    if len(inv_clean) > 0:
        inv_min = inv_clean[_date_col].min().date()
        inv_max = inv_clean[_date_col].max().date()
    else:
        inv_min = pd.Timestamp.now().date()
        inv_max = inv_min

    dc1, dc2 = st.columns(2)
    with dc1:
        cat_from = st.date_input("📅 From", value=inv_min, key="cat_from")
    with dc2:
        cat_to   = st.date_input("📅 To",   value=inv_max, key="cat_to")
    st.caption(f"ℹ️ Data available: {inv_min.strftime('%b %d, %Y')} — {inv_max.strftime('%b %d, %Y')}")

    if len(inv_clean) > 0:
        ts_from = pd.Timestamp(cat_from).normalize()
        ts_to   = pd.Timestamp(cat_to).normalize() + pd.Timedelta(days=1)
        inv_clean["_date"] = inv_clean[_date_col].dt.normalize()
        date_mask = (inv_clean["_date"] >= ts_from) & (inv_clean["_date"] < ts_to)
        cat_date_df = inv_clean[date_mask]

        if len(cat_date_df) == 0:
            st.warning("No bills in the selected date range.")
        else:
            cat_count = (
                cat_date_df.groupby("category")
                .size()
                .reset_index(name="bill_count")
                .sort_values("bill_count", ascending=False)
            )
            COLORS = ["#7C3AED","#F59E0B","#10B981","#EF4444","#06B6D4",
                      "#EC4899","#84CC16","#F97316","#3B82F6","#34d399",
                      "#a78bfa","#60a5fa","#fbbf24"]
            bar_colors = [COLORS[i % len(COLORS)] for i in range(len(cat_count))]

            fig = go.Figure(go.Bar(
                x=cat_count["category"],
                y=cat_count["bill_count"],
                marker=dict(color=bar_colors, line=dict(width=0)),
                text=cat_count["bill_count"].apply(lambda v: f"{v:,}"),
                textposition="outside",
                textfont=dict(size=11, color="#e2e8f0"),
            ))
            total_in_range = int(cat_count["bill_count"].sum())
            fig.update_layout(
                title=f"🏷️ Bills by Category  ·  {total_in_range:,} bills in range",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0", family="Inter"),
                title_font=dict(color="#F59E0B", size=15),
                height=400,
                margin=dict(l=10, r=10, t=55, b=10),
                xaxis=dict(
                    title="Category",
                    tickangle=-30,
                    gridcolor="rgba(255,255,255,0.05)",
                    tickfont=dict(size=11),
                ),
                yaxis=dict(
                    title="Number of Bills",
                    gridcolor="rgba(255,255,255,0.05)",
                    title_font=dict(color="#F59E0B"),
                    tickfont=dict(color="#F59E0B"),
                ),
                showlegend=False,
            )
            st.plotly_chart(fig, width='stretch')
    else:
        st.info("No bill date data available.")

with r2:
    # Total bill count per category (all filtered data, no date restriction)
    cat_total = (
        filtered.dropna(subset=["category"])
        .groupby("category")
        .size()
        .reset_index(name="bill_count")
        .sort_values("bill_count", ascending=True)   # ascending so longest bar is on top
    )

    COLORS = ["#7C3AED","#F59E0B","#10B981","#EF4444","#06B6D4",
              "#EC4899","#84CC16","#F97316","#3B82F6","#34d399",
              "#a78bfa","#60a5fa","#fbbf24"]
    hbar_colors = [COLORS[i % len(COLORS)] for i in range(len(cat_total))]

    fig2 = go.Figure(go.Bar(
        x=cat_total["bill_count"],
        y=cat_total["category"],
        orientation="h",
        marker=dict(color=hbar_colors, line=dict(width=0)),
        text=cat_total["bill_count"].apply(lambda v: f"{v:,} bills"),
        textposition="outside",
        textfont=dict(size=11, color="#e2e8f0"),
    ))
    fig2.update_layout(
        title="📊 Total Bill Count by Category",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0", family="Inter"),
        title_font=dict(color="#F59E0B", size=15),
        height=400,
        margin=dict(l=10, r=120, t=55, b=10),
        xaxis=dict(
            title="Number of Bills",
            gridcolor="rgba(255,255,255,0.05)",
            title_font=dict(color="#F59E0B"),
            tickfont=dict(color="#F59E0B"),
        ),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        showlegend=False,
    )
    st.plotly_chart(fig2, width='stretch')

# ── Row 2: Spend Distribution by Category  +  Avg Tax Rate — side by side ─────
r3, r4 = st.columns(2)

with r3:
    box_df = filtered[filtered["totalAmount"] < filtered["totalAmount"].quantile(0.95)].copy()
    fig = px.box(
        box_df, x="category", y="totalAmount",
        title="📦 Spend Distribution by Category",
        color="category",
        color_discrete_sequence=["#7C3AED","#06B6D4","#10B981","#F59E0B","#EF4444",
                                  "#3B82F6","#EC4899","#84CC16","#F97316","#8B5CF6",
                                  "#34d399","#60a5fa"],
        points=False,
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0"), title_font=dict(color="#F59E0B", size=15),
        height=400, margin=dict(l=10,r=10,t=50,b=60),
        xaxis=dict(tickangle=-30, gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        showlegend=False,
    )
    st.plotly_chart(fig, width='stretch')

with r4:
    tax_df = filtered.dropna(subset=["taxAmount","totalAmount"]).copy()
    tax_df = tax_df[tax_df["taxAmount"] > 0]
    if len(tax_df) > 0:
        tax_df["tax_rate"] = (tax_df["taxAmount"] / tax_df["totalAmount"] * 100).clip(0, 50)
        tax_cat = tax_df.groupby("category").agg(
            avg_tax_rate=("tax_rate","mean"),
            bill_count=("totalAmount","count"),
        ).reset_index().sort_values("avg_tax_rate", ascending=True)

        fig = go.Figure(go.Bar(
            x=tax_cat["avg_tax_rate"],
            y=tax_cat["category"],
            orientation="h",
            marker=dict(
                color=tax_cat["avg_tax_rate"],
                colorscale=[[0,"#0d1b4b"],[0.4,"#7C3AED"],[0.7,"#F59E0B"],[1,"#EF4444"]],
                showscale=True,
                colorbar=dict(
                    title="Tax %",
                    tickfont=dict(color="#94a3b8", size=9),
                    title_font=dict(color="#94a3b8", size=10),
                    thickness=12, len=0.8,
                ),
            ),
            text=[f"{v:.1f}%  ({int(c):,} bills)" for v, c in
                  zip(tax_cat["avg_tax_rate"], tax_cat["bill_count"])],
            textposition="outside",
            textfont=dict(size=10, color="#e2e8f0"),
        ))
        fig.update_layout(
            title="📐 Avg Tax Rate by Category (%)",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e2e8f0"), title_font=dict(color="#F59E0B", size=15),
            height=400, margin=dict(l=10,r=140,t=50,b=10),
            xaxis=dict(title="Average Tax Rate (%)", gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.0)"),
            showlegend=False,
        )
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No tax data available for current filter.")

st.markdown("<br>", unsafe_allow_html=True)

# ── Raw data table ─────────────────────────────────────────────────────────────
with st.expander("📋 View Raw Bill Extractions"):
    cols_show = [c for c in ["merchantName","category","totalAmount","taxAmount","currency","invoiceDate"] if c in filtered.columns]
    st.dataframe(filtered[cols_show].sort_values("totalAmount", ascending=False).head(200),
                 width='stretch', hide_index=True)
