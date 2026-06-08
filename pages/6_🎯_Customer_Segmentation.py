"""
pages/7_🎯_Customer_Segmentation.py — Customer Segmentation using RFM and K-Means
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from data_loader import load_all

st.set_page_config(page_title="BOC · Customer Segmentation", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.page-title{font-size:2rem;font-weight:800;background:linear-gradient(135deg,#06B6D4,#3B82F6);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:0.2rem;}
.page-sub{color:#64748b;font-size:0.95rem;margin-bottom:1.5rem;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0F0F1A,#1A1A2E);
  border-right:1px solid rgba(124,58,237,0.2);}
.cluster-card{background:linear-gradient(135deg,#1A1A2E,#16213E);
  border:1px solid rgba(124,58,237,0.3);border-radius:12px;padding:1.5rem;
  margin-bottom:1rem;height:100%;}
.cluster-title{font-size:1.1rem;font-weight:700;margin-bottom:1rem;display:flex;align-items:center;gap:0.5rem;}
.stat-row{display:flex;justify-content:space-between;margin-bottom:0.5rem;font-size:0.9rem;}
.stat-label{color:#94a3b8;}
.stat-value{font-weight:600;color:#e2e8f0;}
</style>
""", unsafe_allow_html=True)

dfs = load_all()
bill = dfs.get("bill", pd.DataFrame())
be = dfs.get("bill_extraction", pd.DataFrame())
users = dfs.get("user", pd.DataFrame())

st.markdown('<div class="page-title">🎯 Customer Segmentation</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">RFM Analysis (Recency, Frequency, Monetary) powered by K-Means Clustering</div>', unsafe_allow_html=True)

if bill.empty or be.empty or users.empty:
    st.warning("Not enough data to perform segmentation.")
    st.stop()

# ── Data Preparation (RFM Calculation) ─────────────────────────────────────────

# Merge bill and bill_extraction to get totalAmount for each bill
merged = bill.merge(be, left_on="id", right_on="billId", how="inner", suffixes=("_bill", "_be"))
# Filter out rows with negative or zero amounts just in case
merged = merged[merged["totalAmount"] > 0].copy()

# Determine the "current" date for Recency calculation (max date in dataset)
max_date = merged["createdAt_bill"].max()

# Calculate RFM metrics per user
rfm = merged.groupby("userId").agg(
    LatestDate=("createdAt_bill", "max"),
    Frequency=("id_bill", "nunique"),
    Monetary=("totalAmount", "sum")
).reset_index()

# Calculate Recency in days
rfm["Recency"] = (max_date - rfm["LatestDate"]).dt.days

# Join with user table to get user details
rfm = rfm.merge(users[["id", "name", "email"]], left_on="userId", right_on="id", how="left")
rfm = rfm.dropna(subset=["Recency", "Frequency", "Monetary"])

if len(rfm) < 10:
    st.warning("Not enough users with valid transaction history to perform clustering.")
    st.stop()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Model Parameters")
    n_clusters = st.slider("Number of Clusters (K)", min_value=2, max_value=8, value=4, step=1)
    
    st.markdown("---")
    st.markdown("### 📚 Glossary")
    st.markdown("**Recency**: Days since last bill.")
    st.markdown("**Frequency**: Total number of bills.")
    st.markdown("**Monetary**: Total amount spent.")

# ── K-Means Clustering ─────────────────────────────────────────────────────────

# 1. Scale the data
scaler = StandardScaler()
rfm_scaled = scaler.fit_transform(rfm[["Recency", "Frequency", "Monetary"]])

# 2. Apply K-Means
kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
rfm["Cluster"] = kmeans.fit_predict(rfm_scaled)

# Make Cluster a string for categorical coloring
rfm["Cluster_Label"] = rfm["Cluster"].apply(lambda x: f"Cluster {x}")

# Calculate summary stats for each cluster
cluster_summary = rfm.groupby("Cluster").agg(
    UserCount=("userId", "count"),
    AvgRecency=("Recency", "mean"),
    AvgFrequency=("Frequency", "mean"),
    AvgMonetary=("Monetary", "mean")
).reset_index()

# Sort clusters roughly by value (Monetary & Frequency high, Recency low is better)
# We'll score them simple: M_rank + F_rank - R_rank
cluster_summary["M_Rank"] = cluster_summary["AvgMonetary"].rank()
cluster_summary["F_Rank"] = cluster_summary["AvgFrequency"].rank()
cluster_summary["R_Rank"] = cluster_summary["AvgRecency"].rank(ascending=False) # Lower recency is better
cluster_summary["Score"] = cluster_summary["M_Rank"] + cluster_summary["F_Rank"] + cluster_summary["R_Rank"]

cluster_summary = cluster_summary.sort_values("Score", ascending=False).reset_index(drop=True)

# Assign names based on rank (index)
def get_segment_name(idx, recency, mean_recency):
    if idx == 0:
        return "👑 Champions"
    elif idx == n_clusters - 1:
        return "⚠️ At Risk / Low Value"
    elif recency > mean_recency:
        return "⏳ Needs Attention"
    else:
        return "⭐ Loyal / Promising"

mean_recency = cluster_summary["AvgRecency"].mean()
cluster_summary["SegmentName"] = [get_segment_name(i, row["AvgRecency"], mean_recency) for i, row in cluster_summary.iterrows()]

# Now sort by Cluster ID for display
cluster_summary = cluster_summary.sort_values("Cluster", ascending=True).reset_index(drop=True)

# Assign a dynamic color to clusters based on sorted rank for consistent visualization
color_palette = px.colors.qualitative.Plotly
cluster_colors = {row["Cluster"]: color_palette[i % len(color_palette)] for i, row in cluster_summary.iterrows()}

# ── Visualizations ─────────────────────────────────────────────────────────────

# --- Row 1: 2D Scatter Plots ---
st.markdown("### 🌌 Customer Segments Analysis")

c1, c2 = st.columns(2)

with c1:
    fig_fm = px.scatter(
        rfm, 
        x="Frequency", 
        y="Monetary", 
        color="Cluster_Label",
        hover_name="name",
        hover_data={"email": True, "Cluster_Label": False, "Recency": True, "Frequency": True, "Monetary": ":.2f"},
        color_discrete_sequence=[cluster_colors[c] for c in sorted(rfm["Cluster"].unique())],
        opacity=0.8,
        log_y=True, # Log scale handles the massive monetary outliers!
        title="Frequency vs Monetary (Log Scale)"
    )
    fig_fm.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Frequency (Bills)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Monetary ($)"),
        margin=dict(l=10, r=10, b=10, t=40),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor="rgba(0,0,0,0.5)")
    )
    st.plotly_chart(fig_fm, width='stretch')

with c2:
    fig_rf = px.scatter(
        rfm, 
        x="Recency", 
        y="Frequency", 
        color="Cluster_Label",
        hover_name="name",
        hover_data={"email": True, "Cluster_Label": False, "Recency": True, "Frequency": True, "Monetary": ":.2f"},
        color_discrete_sequence=[cluster_colors[c] for c in sorted(rfm["Cluster"].unique())],
        opacity=0.8,
        title="Recency vs Frequency"
    )
    fig_rf.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Recency (Days)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Frequency (Bills)"),
        margin=dict(l=10, r=10, b=10, t=40),
        showlegend=False
    )
    st.plotly_chart(fig_rf, width='stretch')

st.markdown("<br>", unsafe_allow_html=True)

# --- Row 2: Cluster Profiles ---
st.markdown("### 📊 Cluster Profiles")

cols = st.columns(n_clusters)

for i, col in enumerate(cols):
    row = cluster_summary.iloc[i]
    c_id = int(row["Cluster"])
    color = cluster_colors[c_id]
    
    segment_name = row["SegmentName"]
    
    with col:
        st.markdown(f"""
        <div class="cluster-card" style="border-top: 4px solid {color}">
            <div class="cluster-title">
                <span style="display:inline-block;width:12px;height:12px;border-radius:50%;background-color:{color};"></span>
                {segment_name} (Cluster {c_id})
            </div>
            <div class="stat-row">
                <span class="stat-label">Users</span>
                <span class="stat-value">{int(row["UserCount"]):,}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Avg Recency</span>
                <span class="stat-value">{row["AvgRecency"]:.1f} days</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Avg Frequency</span>
                <span class="stat-value">{row["AvgFrequency"]:.1f} bills</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Avg Monetary</span>
                <span class="stat-value">${row["AvgMonetary"]:,.2f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- Row 3: Detail Dataframes ---
with st.expander("📋 View Full User Segment Data"):
    display_df = rfm[["name", "email", "Recency", "Frequency", "Monetary", "Cluster_Label"]].copy()
    display_df = display_df.rename(columns={"name": "Name", "email": "Email", "Cluster_Label": "Segment"})
    # Format
    display_df["Monetary"] = display_df["Monetary"].apply(lambda x: f"{x:,.2f}")
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
