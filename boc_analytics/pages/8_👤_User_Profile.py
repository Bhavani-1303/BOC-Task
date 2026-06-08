"""
pages/6_👤_User_Profile.py — Per-user deep dive analytics
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from data_loader import load_all

st.set_page_config(page_title="BOC · User Profile", page_icon="👤", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.page-title{font-size:2rem;font-weight:800;background:linear-gradient(135deg,#8B5CF6,#EC4899);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:0.2rem;}
.page-sub{color:#64748b;font-size:0.95rem;margin-bottom:1.5rem;}
.user-hero{background:linear-gradient(135deg,#1A1A2E,#16213E);
  border:1px solid rgba(139,92,246,0.3);border-radius:20px;padding:1.8rem 2rem;
  position:relative;overflow:hidden;margin-bottom:1.5rem;}
.user-hero::before{content:'';position:absolute;top:0;left:0;right:0;height:4px;
  background:linear-gradient(90deg,#8B5CF6,#EC4899,#F59E0B);}
.user-name{font-size:1.8rem;font-weight:800;color:#e2e8f0;}
.user-email{font-size:0.9rem;color:#64748b;margin-top:0.2rem;}
.avatar{width:64px;height:64px;border-radius:50%;background:linear-gradient(135deg,#8B5CF6,#EC4899);
  display:flex;align-items:center;justify-content:center;font-size:1.8rem;font-weight:700;
  color:white;flex-shrink:0;}
.badge-seg{display:inline-block;padding:0.3rem 0.8rem;border-radius:20px;font-size:0.82rem;
  font-weight:600;background:rgba(139,92,246,0.15);color:#a78bfa;
  border:1px solid rgba(139,92,246,0.35);margin-top:0.6rem;}
.stat-mini{background:rgba(139,92,246,0.08);border:1px solid rgba(139,92,246,0.2);
  border-radius:12px;padding:0.8rem 1rem;text-align:center;}
.stat-mini-val{font-size:1.4rem;font-weight:800;color:#a78bfa;}
.stat-mini-lbl{font-size:0.72rem;text-transform:uppercase;letter-spacing:1px;color:#64748b;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0F0F1A,#1A1A2E);
  border-right:1px solid rgba(124,58,237,0.2);}
</style>
""", unsafe_allow_html=True)

dfs  = load_all()
bill = dfs.get("bill", pd.DataFrame())
be   = dfs.get("bill_extraction", pd.DataFrame())
user = dfs.get("user", pd.DataFrame())
rc   = dfs.get("reward_credit", pd.DataFrame())

st.markdown('<div class="page-title">👤 User Profile Deep Dive</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Search any user to see their full spending analytics, segment, and history</div>', unsafe_allow_html=True)

if user.empty:
    st.warning("No user data.")
    st.stop()

# ── Search ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 Search User")

    # Create labels for all users
    user_options = user[["id","name","email"]].copy()
    user_options["label"] = user_options["name"].fillna("Unknown") + " — " + user_options["email"].fillna("Unknown")

    # Sort users so those with the most bills appear first by default
    if not bill.empty and "userId" in bill.columns:
        _bill_counts = bill.groupby("userId").size().reset_index(name="_cnt")
        _user_with_bills = user_options.merge(_bill_counts, left_on="id", right_on="userId", how="left")
        _user_with_bills["_cnt"] = _user_with_bills["_cnt"].fillna(0)
        user_options = _user_with_bills.sort_values("_cnt", ascending=False).copy()

    # Streamlit's selectbox is natively searchable! Type to search.
    sel_label = st.selectbox("Type to search User:", user_options["label"].tolist())
    
    if not sel_label:
        st.stop()

    sel_row = user_options[user_options["label"] == sel_label].iloc[0]
    sel_id  = sel_row["id"]

# ── Load selected user data ────────────────────────────────────────────────────
u_data = user[user["id"] == sel_id].iloc[0]

# Bills for this user
u_bills = bill[bill["userId"] == sel_id].copy() if "userId" in bill.columns else pd.DataFrame()

# Bill extractions for this user
if not u_bills.empty and not be.empty:
    u_ext = u_bills.merge(be, left_on="id", right_on="billId", how="left")
else:
    u_ext = pd.DataFrame()

# Reward credits for this user
u_rewards = rc[rc["userId"] == sel_id].copy() if not rc.empty and "userId" in rc.columns else pd.DataFrame()

# ── Basic stats ────────────────────────────────────────────────────────────────
now = pd.Timestamp.now()
if not u_bills.empty and "createdAt" in u_bills.columns:
    last_bill    = u_bills["createdAt"].max()
    recency_days = int((now - last_bill).days) if pd.notna(last_bill) else 999
    freq         = len(u_bills)
else:
    recency_days = 999
    freq         = 0

total_spend = u_ext["totalAmount"].sum() if not u_ext.empty and "totalAmount" in u_ext.columns else 0
avg_spend   = u_ext["totalAmount"].mean() if not u_ext.empty and "totalAmount" in u_ext.columns else 0

# Segment (simple)
def get_segment(r_days, freq, spend):
    r = 5 if r_days < 7 else 4 if r_days < 30 else 3 if r_days < 90 else 2 if r_days < 180 else 1
    f = min(5, max(1, freq))
    m = 5 if spend > 5000 else 4 if spend > 1000 else 3 if spend > 300 else 2 if spend > 50 else 1
    if r >= 4 and f >= 4 and m >= 4: return "🏆 Champion"
    if r >= 3 and f >= 3:            return "⭐ Loyal"
    if r >= 4 and f <= 2:            return "🌱 New / Promising"
    if r <= 2 and f >= 3:            return "⚠️ At-Risk"
    if r <= 2 and f <= 2:            return "😴 Dormant"
    return "🔄 Average"

rfm_seg = get_segment(recency_days, freq, total_spend)

# ── User Hero Card ─────────────────────────────────────────────────────────────
avatar_letter = str(u_data.get("name","?"))[0].upper()
member_since  = u_data["createdAt"].strftime("%b %Y") if pd.notna(u_data.get("createdAt")) else "Unknown"

# Format total spend without $
spend_display = f"{total_spend:,.0f}"

st.markdown(f"""
<div class="user-hero">
  <div style="display:flex;align-items:center;gap:1.5rem;">
    <div class="avatar">{avatar_letter}</div>
    <div style="flex:1;">
      <div class="user-name">{u_data.get('name','Unknown')}</div>
      <div class="user-email">📧 {u_data.get('email','N/A')}</div>
      <div class="badge-seg">{rfm_seg}</div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:2.5rem;font-weight:900;color:#a78bfa;">{spend_display}</div>
      <div style="font-size:0.75rem;text-transform:uppercase;letter-spacing:1px;color:#64748b;">Total Spend</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Stat Pills ─────────────────────────────────────────────────────────────────
s1, s2, s3, s4, s5, s6 = st.columns(6)
has_wallet = "Yes" if pd.notna(u_data.get("mainWalletAddress")) else "No"
stats = [
    (f"{freq}", "Bills Uploaded"),
    (f"{avg_spend:,.1f}", "Avg Bill"),
    (f"{recency_days}d", "Last Active"),
    (f"{int(u_data.get('rewardBalance',0)):,}", "Reward Balance"),
    (f"{u_ext['category'].nunique() if not u_ext.empty and 'category' in u_ext.columns else 0}", "Categories Used"),
    (f"{has_wallet}", "Wallet Connected"),
]
for col,(val,lbl) in zip([s1,s2,s3,s4,s5,s6], stats):
    col.markdown(f"""<div class="stat-mini">
        <div class="stat-mini-val">{val}</div>
        <div class="stat-mini-lbl">{lbl}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── RFM Analysis ───────────────────────────────────────────────────────────────
st.markdown("### 🎯 RFM Analysis")
r_col, f_col, m_col = st.columns(3)
with r_col:
    st.markdown(f"""
    <div style="background:rgba(6,182,212,0.1);border:1px solid rgba(6,182,212,0.3);border-radius:12px;padding:1rem;">
      <div style="color:#06B6D4;font-size:0.8rem;text-transform:uppercase;font-weight:700;">Recency (R)</div>
      <div style="font-size:1.5rem;font-weight:800;color:#e2e8f0;margin-top:0.3rem;">{recency_days} days</div>
      <div style="color:#64748b;font-size:0.85rem;margin-top:0.2rem;">Since last bill uploaded</div>
    </div>""", unsafe_allow_html=True)
with f_col:
    st.markdown(f"""
    <div style="background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.3);border-radius:12px;padding:1rem;">
      <div style="color:#10B981;font-size:0.8rem;text-transform:uppercase;font-weight:700;">Frequency (F)</div>
      <div style="font-size:1.5rem;font-weight:800;color:#e2e8f0;margin-top:0.3rem;">{freq} bills</div>
      <div style="color:#64748b;font-size:0.85rem;margin-top:0.2rem;">Total lifetime bills</div>
    </div>""", unsafe_allow_html=True)
with m_col:
    st.markdown(f"""
    <div style="background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.3);border-radius:12px;padding:1rem;">
      <div style="color:#F59E0B;font-size:0.8rem;text-transform:uppercase;font-weight:700;">Monetary (M)</div>
      <div style="font-size:1.5rem;font-weight:800;color:#e2e8f0;margin-top:0.3rem;">{total_spend:,.2f}</div>
      <div style="color:#64748b;font-size:0.85rem;margin-top:0.2rem;">Total lifetime spend</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

if u_ext.empty and u_bills.empty:
    st.info("This user hasn't uploaded any bills yet.")
    st.stop()

# ── Row 1: Bill Status Pipeline + Category Pie ────────────────────────────────
r1, r2 = st.columns([3, 2])

with r1:
    # Bill status breakdown — how many completed, minted, duplicated, etc.
    if not u_bills.empty and "status" in u_bills.columns:
        status_counts = u_bills["status"].value_counts().reset_index()
        status_counts.columns = ["status", "count"]
        status_counts = status_counts.sort_values("count", ascending=True)

        # Color each status
        def _status_color(s):
            s = str(s).lower()
            if s in ["completed", "minted", "hash_complete", "extracted"]:
                return "#10B981"
            elif any(k in s for k in ["duplicate", "fail", "reject", "flag"]):
                return "#EF4444"
            elif s in ["uploaded", "hashing"]:
                return "#7C3AED"
            return "#F59E0B"

        bar_colors = [_status_color(s) for s in status_counts["status"]]

        fig = go.Figure(go.Bar(
            x=status_counts["count"],
            y=status_counts["status"],
            orientation="h",
            marker=dict(color=bar_colors, line=dict(width=0)),
            text=status_counts["count"],
            textposition="outside",
            textfont=dict(size=12, color="#e2e8f0"),
        ))
        fig.update_layout(
            title=f"📋 Bill Status Pipeline  ·  {freq} total bills",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e2e8f0", family="Inter"),
            title_font=dict(color="#a78bfa", size=15),
            height=320,
            margin=dict(l=10, r=80, t=55, b=10),
            xaxis=dict(title="Number of Bills", gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.0)", tickfont=dict(size=12)),
            showlegend=False,
        )
        st.plotly_chart(fig, width='stretch')

        # Summary badges
        completed  = int(u_bills["status"].isin(["completed","minted","hash_complete"]).sum())
        minted     = int((u_bills["status"] == "minted").sum())
        duplicated = int(u_bills["status"].str.contains("duplicate", na=False).sum())
        failed     = int(u_bills["status"].str.contains("fail|reject|flag", na=False).sum())

        st.markdown(f"""
        <div style="display:flex;gap:0.8rem;flex-wrap:wrap;margin-top:0.3rem;">
          <span style="background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.3);
            border-radius:20px;padding:0.3rem 0.9rem;font-size:0.82rem;color:#10B981;font-weight:600;">
            ✅ Completed: {completed}</span>
          <span style="background:rgba(139,92,246,0.1);border:1px solid rgba(139,92,246,0.3);
            border-radius:20px;padding:0.3rem 0.9rem;font-size:0.82rem;color:#a78bfa;font-weight:600;">
            🖼️ Minted NFT: {minted}</span>
          <span style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);
            border-radius:20px;padding:0.3rem 0.9rem;font-size:0.82rem;color:#EF4444;font-weight:600;">
            🔁 Duplicated: {duplicated}</span>
          <span style="background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.3);
            border-radius:20px;padding:0.3rem 0.9rem;font-size:0.82rem;color:#F59E0B;font-weight:600;">
            ❌ Failed: {failed}</span>
        </div>""", unsafe_allow_html=True)
    else:
        st.info("No bill status data available.")

with r2:
    # Try to get categories and total amount from the bill_extraction table
    cat_df = pd.DataFrame()
    if not u_ext.empty and "category" in u_ext.columns and "totalAmount" in u_ext.columns:
        cat_df = u_ext[["category", "totalAmount"]].dropna(subset=["category"])
    elif not u_bills.empty and not be.empty and "billId" in be.columns and "category" in be.columns and "totalAmount" in be.columns:
        user_bill_ids = u_bills["id"].tolist()
        _be_direct = be[be["billId"].isin(user_bill_ids)]
        cat_df = _be_direct[["category", "totalAmount"]].dropna(subset=["category"])
        
    if not cat_df.empty:
        # Calculate spend by category
        cat_spend = cat_df.groupby("category")["totalAmount"].sum().reset_index()
        cat_spend.columns = ["category", "spend"]
        
        fig = px.pie(
            cat_spend, values="spend", names="category",
            title="🏷️ Spend by Category",
            hole=0.55,
            color_discrete_sequence=px.colors.qualitative.Vivid,
        )
        fig.update_traces(textinfo="label+percent", textfont=dict(size=10))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e2e8f0"), title_font=dict(color="#a78bfa", size=15),
            height=320, margin=dict(l=10, r=10, t=50, b=10),
            legend=dict(font=dict(size=9)),
        )
        st.plotly_chart(fig, width='stretch')
    else:
        st.markdown("""
        <div style="background:rgba(139,92,246,0.08);border:1px solid rgba(139,92,246,0.2);
          border-radius:12px;padding:1.5rem;text-align:center;margin-top:1rem;">
          <div style="font-size:2rem;">🏷️</div>
          <div style="color:#a78bfa;font-size:0.9rem;margin-top:0.5rem;font-weight:600;">
            Category data not yet available</div>
          <div style="color:#64748b;font-size:0.8rem;margin-top:0.3rem;">
            Bills may still be processing through extraction</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Recent Bills Table ─────────────────────────────────────────────────────────
st.markdown("### 🧾 Recent Bills")

if not u_ext.empty:
    cols_show = [c for c in ["merchantName", "category", "totalAmount", "taxAmount",
                              "currency", "invoiceDate", "status"] if c in u_ext.columns]
    if not cols_show:
        cols_show = [c for c in u_ext.columns if c in ["merchantName", "category", "totalAmount", "invoiceDate"]]

    if cols_show:
        disp = u_ext[cols_show].copy()

        # Drop rows where ALL key fields are empty (no meaningful data)
        key_fields = [c for c in ["merchantName", "totalAmount", "invoiceDate"] if c in disp.columns]
        disp = disp.dropna(how="all", subset=key_fields)
        # Also drop rows where merchantName and totalAmount are both null
        if "merchantName" in disp.columns and "totalAmount" in disp.columns:
            disp = disp[disp["merchantName"].notna() | disp["totalAmount"].notna()]

        if "totalAmount" in disp.columns:
            disp["totalAmount"] = disp["totalAmount"].apply(lambda x: f"{x:,.2f}" if pd.notna(x) else "—")
        if "taxAmount" in disp.columns:
            disp["taxAmount"] = disp["taxAmount"].apply(lambda x: f"{x:,.2f}" if pd.notna(x) else "—")

        # Rename columns
        col_map = {
            "merchantName": "Merchant", "category": "Category",
            "totalAmount": "Amount", "taxAmount": "Tax",
            "currency": "Currency", "invoiceDate": "Invoice Date",
            "status": "Status",
        }
        disp = disp.rename(columns={c: col_map.get(c, c) for c in disp.columns})

        sort_col = "Invoice Date" if "Invoice Date" in disp.columns else disp.columns[0]
        disp_sorted = disp.sort_values(sort_col, ascending=False).head(50)

        st.dataframe(
            disp_sorted,
            width='stretch',
            hide_index=True,
            height=min(400, max(100, len(disp_sorted) * 40 + 40)),
        )
        st.caption(f"Showing {len(disp_sorted)} bills with data")
elif not u_bills.empty:
    st.info("Bills uploaded but no extraction data available yet.")
else:
    st.info("No bills found for this user.")

# ── Reward History ─────────────────────────────────────────────────────────────
if not u_rewards.empty:
    with st.expander("🏆 Reward Credit History"):
        rdisp = u_rewards[["amount","createdAt"]].copy() if "amount" in u_rewards.columns else u_rewards
        rdisp.columns = ["Amount (pts)", "Date"]
        st.dataframe(rdisp.sort_values("Date", ascending=False), width='stretch', hide_index=True)
        st.markdown(f"**Total credits earned:** {u_rewards['amount'].sum():,} points")
