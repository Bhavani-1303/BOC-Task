"""
pages/2_👥_Users.py — User analytics
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from data_loader import load_all

st.set_page_config(page_title="BOC · Users", page_icon="👥", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.page-title{font-size:2rem;font-weight:800;background:linear-gradient(135deg,#34d399,#60a5fa);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:0.2rem;}
.page-sub{color:#64748b;font-size:0.95rem;margin-bottom:1.5rem;}
.stat-pill{display:inline-block;background:rgba(52,211,153,0.1);border:1px solid rgba(52,211,153,0.3);
  border-radius:20px;padding:0.3rem 0.8rem;font-size:0.8rem;color:#34d399;font-weight:600;margin:0.2rem;}
.user-table th{background:#1A1A2E!important;color:#a78bfa!important;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0F0F1A,#1A1A2E);
  border-right:1px solid rgba(124,58,237,0.2);}
</style>
""", unsafe_allow_html=True)

dfs  = load_all()
user = dfs.get("user", pd.DataFrame())
bill = dfs.get("bill", pd.DataFrame())
be   = dfs.get("bill_extraction", pd.DataFrame())
rc   = dfs.get("reward_credit", pd.DataFrame())

st.markdown('<div class="page-title">👥 User Analytics</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">User growth, engagement, loyalty tiers, and referral network</div>', unsafe_allow_html=True)

if user.empty:
    st.warning("No user data found.")
    st.stop()

# ── Compute enriched user stats ───────────────────────────────────────────────
# bills per user
if not bill.empty and "userId" in bill.columns:
    bill_counts = bill.groupby("userId").size().reset_index(name="bill_count")
    user = user.merge(bill_counts, left_on="id", right_on="userId", how="left")
    user["bill_count"] = user["bill_count"].fillna(0).astype(int)
else:
    user["bill_count"] = 0

# spend per user
if not be.empty and "userId" in bill.columns and "totalAmount" in be.columns:
    bill_spend = bill[["id","userId"]].merge(
        be[["billId","totalAmount"]], left_on="id", right_on="billId", how="left"
    ).groupby("userId")["totalAmount"].sum().reset_index(name="total_spend")
    user = user.merge(bill_spend, left_on="id", right_on="userId", how="left", suffixes=("","_sp"))
    user["total_spend"] = user["total_spend"].fillna(0)
else:
    user["total_spend"] = 0

# tenure in days
user["tenure_days"] = (pd.Timestamp.now() - user["createdAt"]).dt.days

# Activity segments
user["activity_segment"] = pd.cut(
    user["bill_count"],
    bins=[-1, 0, 1, 3, 10, 10000],
    labels=["No Bills", "1 Bill", "2-3 Bills", "4-10 Bills", "Power Users (10+)"]
)

# ── KPI Strip ─────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
metrics = [
    ("👥", f"{len(user):,}", "Total Users"),
    ("✅", f"{(user['bill_count'] > 0).sum():,}", "Active Users"),
    ("😴", f"{(user['bill_count'] == 0).sum():,}", "No Bills Yet"),
    ("🏆", f"{(user['bill_count'] >= 10).sum():,}", "Power Users"),
    ("🎯", f"{user['lifetimeRewardPoints'].mean():.0f}", "Avg Reward Pts"),
]
for col, (icon, val, lbl) in zip([k1,k2,k3,k4,k5], metrics):
    col.markdown(f"""
    <div style="background:linear-gradient(135deg,#1A1A2E,#16213E);border:1px solid rgba(52,211,153,0.2);
    border-radius:14px;padding:1rem;text-align:center;position:relative;overflow:hidden;">
    <div style="position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,#10B981,#3B82F6);"></div>
    <div style="font-size:1.5rem">{icon}</div>
    <div style="font-size:1.6rem;font-weight:800;color:#34d399">{val}</div>
    <div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:1px;color:#64748b;margin-top:2px">{lbl}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Row 1: User Growth + Bill Distribution ────────────────────────────────────
r1, r2 = st.columns(2)

with r1:
    user_time = user.dropna(subset=["createdAt"]).copy()

    u_min = user_time["createdAt"].min().date()
    u_max = user_time["createdAt"].max().date()
    ud1, ud2 = st.columns(2)
    with ud1:
        u_from = st.date_input("📅 From", value=u_min, key="u_from")
    with ud2:
        u_to   = st.date_input("📅 To",   value=u_max, key="u_to")
    st.caption(f"ℹ️ Data available: {u_min.strftime('%b %d, %Y')} — {u_max.strftime('%b %d, %Y')}")

    ts_from = pd.Timestamp(u_from).normalize()
    ts_to   = pd.Timestamp(u_to).normalize() + pd.Timedelta(days=1)
    user_time["_date"] = user_time["createdAt"].dt.normalize()
    mask = (user_time["_date"] >= ts_from) & (user_time["_date"] < ts_to)
    u_filtered = user_time[mask]

    if len(u_filtered) == 0:
        st.warning("No users registered in the selected date range.")
    else:
        u_monthly = u_filtered.set_index("createdAt").resample("ME").size().reset_index(name="new_users")
        u_monthly["month_label"] = u_monthly["createdAt"].dt.strftime("%b %Y")
        total_in_range = u_monthly["new_users"].sum()

        fig = go.Figure(go.Bar(
            x=u_monthly["month_label"],
            y=u_monthly["new_users"],
            name="New Users",
            marker=dict(
                color=u_monthly["new_users"],
                colorscale=[[0, "#064e3b"], [0.5, "#10B981"], [1, "#34d399"]],
                showscale=False,
                line=dict(width=0),
            ),
            text=u_monthly["new_users"],
            textposition="outside",
            textfont=dict(size=11, color="#e2e8f0"),
        ))
        fig.update_layout(
            title=f"📅 Monthly User Registrations  ·  {total_in_range:,} users in range",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e2e8f0", family="Inter"),
            title_font=dict(color="#34d399", size=15),
            height=340,
            margin=dict(l=10, r=20, t=55, b=10),
            xaxis=dict(
                gridcolor="rgba(255,255,255,0.05)",
                tickangle=-30,
                tickfont=dict(size=10),
            ),
            yaxis=dict(
                title="New Users",
                gridcolor="rgba(255,255,255,0.05)",
                title_font=dict(color="#34d399"),
                tickfont=dict(color="#34d399"),
            ),
            showlegend=False,
        )
        st.plotly_chart(fig, width='stretch')

with r2:
    # Active / Inactive / Power users donut
    active_count   = int((user["bill_count"] > 0).sum())
    inactive_count = int((user["bill_count"] == 0).sum())
    power_users    = int((user["bill_count"] >= 10).sum())
    light_users    = int(((user["bill_count"] >= 1) & (user["bill_count"] < 10)).sum())

    status_df = pd.DataFrame({
        "Category": ["Power Users\n(10+ bills)", "Light Users\n(1–9 bills)", "Inactive\n(0 bills)"],
        "Count":    [power_users, light_users, inactive_count],
    })
    status_colors = {
        "Power Users\n(10+ bills)": "#34d399",
        "Light Users\n(1–9 bills)": "#7C3AED",
        "Inactive\n(0 bills)":      "#EF4444",
    }
    active_pct = active_count / max(len(user), 1) * 100

    fig = px.pie(
        status_df, values="Count", names="Category",
        title="👥 User Activity Categories",
        hole=0.58,
        color="Category",
        color_discrete_map=status_colors,
    )
    fig.update_traces(
        textinfo="label+percent+value",
        textfont=dict(size=11),
        pull=[0.05, 0.02, 0.02],
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0", family="Inter"),
        title_font=dict(color="#34d399", size=15),
        height=340,
        margin=dict(l=10, r=10, t=55, b=10),
        legend=dict(
            font=dict(size=10),
            bgcolor="rgba(0,0,0,0.3)",
            bordercolor="rgba(52,211,153,0.3)",
            borderwidth=1,
            orientation="h",
            x=0.0, y=-0.15,
        ),
        annotations=[
            dict(
                text=f"<b>{active_pct:.0f}%</b><br>Active",
                x=0.5, y=0.5,
                font=dict(size=17, color="#34d399"),
                showarrow=False,
            )
        ],
    )
    st.plotly_chart(fig, width='stretch')



# ── Top Users Leaderboard ─────────────────────────────────────────────────────
st.markdown("### 🏅 Top 20 Users Leaderboard")

top_users = user.sort_values("lifetimeRewardPoints", ascending=False).head(20).copy()
top_users["rank"] = range(1, len(top_users)+1)
medals = {1:"🥇", 2:"🥈", 3:"🥉"}

display_cols = ["rank","name","email","lifetimeRewardPoints","bill_count","total_spend","tenure_days"]
available = [c for c in display_cols if c in top_users.columns]
top_display = top_users[available].copy()
top_display["rank"] = top_display["rank"].apply(lambda r: medals.get(r, str(r)))
top_display.columns = [c.replace("lifetimeRewardPoints","Reward Pts")
                         .replace("bill_count","Bills")
                         .replace("total_spend","Total Spend")
                         .replace("tenure_days","Tenure (days)")
                         .replace("name","Name").replace("email","Email").replace("rank","#")
                       for c in top_display.columns]

st.dataframe(
    top_display,
    width='stretch',
    hide_index=True,
    height=500,
)

# ── Referral Stats ─────────────────────────────────────────────────────────────
with st.expander("🔗 Referral Network Stats"):
    has_referral = user["referralCode"].notna().sum()
    referred     = user["referredBy"].notna().sum()
    st.markdown(f"""
    <div style="display:flex;gap:2rem;padding:1rem;">
    <div><div style="font-size:2rem;font-weight:800;color:#34d399">{has_referral:,}</div>
    <div style="color:#64748b;font-size:0.8rem">Users with a referral code</div></div>
    <div><div style="font-size:2rem;font-weight:800;color:#60a5fa">{referred:,}</div>
    <div style="color:#64748b;font-size:0.8rem">Users who were referred</div></div>
    <div><div style="font-size:2rem;font-weight:800;color:#F59E0B">{referred/len(user)*100:.1f}%</div>
    <div style="color:#64748b;font-size:0.8rem">Referral conversion rate</div></div>
    </div>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 👥 Users")
    st.markdown(f"Total: **{len(user):,}**")
    st.markdown(f"Active (has bills): **{(user['bill_count']>0).sum():,}**")
    st.markdown(f"Avg bills/user: **{user['bill_count'].mean():.1f}**")
