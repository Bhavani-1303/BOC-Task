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
from shared_styles import inject_shared_styles, inject_sidebar_brand

st.set_page_config(page_title="BOC · Users", page_icon="👥", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;background:#FFFFFF;color:#1E293B;}
.page-title{font-size:2rem;font-weight:800;color:#1E293B;margin-bottom:0.2rem;}
.page-sub{color:#64748B;font-size:0.95rem;margin-bottom:1.5rem;}
.stat-pill{display:inline-block;background:rgba(5,150,105,0.08);border:1px solid rgba(5,150,105,0.25);
  border-radius:20px;padding:0.3rem 0.8rem;font-size:0.8rem;color:#059669;font-weight:600;margin:0.2rem;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0F172A,#1E293B) !important;
  border-right:1px solid #334155;}
.kpi-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 1rem;
    margin-bottom: 1rem;
}
.kpi-box {
    background:#FFFFFF;
    border:1px solid #E2E8F0;
    border-radius:14px;
    padding:1rem;
    text-align:center;
    position:relative;
    overflow:hidden;
    box-shadow:0 1px 3px rgba(0,0,0,0.06);
}
.kpi-top-bar {
    position:absolute;top:0;left:0;right:0;height:3px;
    background:linear-gradient(90deg,#CBD5E1,#94A3B8);
}
.kpi-val {
    font-size:1.6rem;font-weight:800;color:#1E293B;
}
.kpi-lbl {
    font-size:0.72rem;text-transform:uppercase;letter-spacing:1px;color:#94A3B8;margin-top:2px;
}
.ml-insight-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}
</style>
""", unsafe_allow_html=True)

inject_shared_styles()
inject_sidebar_brand()

dfs  = load_all()
user = dfs.get("user", pd.DataFrame())
bill = dfs.get("bill", pd.DataFrame())
be   = dfs.get("bill_extraction", pd.DataFrame())
rc   = dfs.get("reward_credit", pd.DataFrame())
nft  = dfs.get("nft", pd.DataFrame())

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
wallet_connected = int(user["mainWalletAddress"].notna().sum()) if "mainWalletAddress" in user.columns else 0
nft_minted = int(len(nft)) if not nft.empty else 0
did_completed = int(user["didStatus"].eq("ready").sum()) if "didStatus" in user.columns else 0

metrics = [
    ("📊", f"{len(user):,}", "Total Users"),
    ("🟢", f"{(user['bill_count'] > 0).sum():,}", "Active Users"),
    ("🔴", f"{(user['bill_count'] == 0).sum():,}", "Inactive Users"),
    ("🎨", f"{nft_minted:,}", "NFTs Minted"),
    ("🛡️", f"{did_completed:,}", "DID Completed"),
    ("🔗", f"{wallet_connected:,}", "Wallets Connected"),
]

kpi_html = '<div class="kpi-container">'
for icon, val, lbl in metrics:
    kpi_html += f"""
    <div class="kpi-box">
        <div class="kpi-top-bar"></div>
        <div style="font-size:1.5rem">{icon}</div>
        <div class="kpi-val">{val}</div>
        <div class="kpi-lbl">{lbl}</div>
    </div>"""
kpi_html += '</div>'
st.markdown(kpi_html, unsafe_allow_html=True)

st.info('📈 **User Growth & Engagement** — The registration chart tracks new user signups over time. The activity donut shows the ratio of power users (10+ bills), light users, and inactive accounts — key indicators of platform health.')

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
                colorscale=[[0, "#A7F3D0"], [0.5, "#34D399"], [1, "#059669"]],
                showscale=False,
                line=dict(width=0),
            ),
            text=u_monthly["new_users"],
            textposition="outside",
            textfont=dict(size=11, color="#334155"),
        ))
        fig.update_layout(
            title=f"📅 Monthly User Registrations  ·  {total_in_range:,} users in range",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#334155", family="Inter"),
            title_font=dict(color="#1E293B", size=15),
            height=340,
            margin=dict(l=10, r=20, t=55, b=10),
            xaxis=dict(
                gridcolor="rgba(0,0,0,0.06)",
                tickangle=-30,
                tickfont=dict(size=10, color="#64748B"),
            ),
            yaxis=dict(
                title="New Users",
                gridcolor="rgba(0,0,0,0.06)",
                title_font=dict(color="#475569"),
                tickfont=dict(color="#64748B"),
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
        "Power Users\n(10+ bills)": "#10B981",
        "Light Users\n(1–9 bills)": "#6366F1",
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
        textfont=dict(size=11, color="#334155"),
        pull=[0.05, 0.02, 0.02],
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#334155", family="Inter"),
        title_font=dict(color="#1E293B", size=15),
        height=340,
        margin=dict(l=10, r=10, t=55, b=10),
        legend=dict(
            font=dict(size=10, color="#475569"),
            bgcolor="rgba(248,250,252,0.8)",
            bordercolor="#E2E8F0",
            borderwidth=1,
            orientation="h",
            x=0.0, y=-0.15,
        ),
        annotations=[
            dict(
                text=f"<b>{active_pct:.0f}%</b><br>Active",
                x=0.5, y=0.5,
                font=dict(size=17, color="#10B981"),
                showarrow=False,
            )
        ],
    )
    st.plotly_chart(fig, width='stretch')


# ── DID Analysis + NFT Minting ────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.info('🛡️ **DID (Decentralized Identity) Analysis** — Track how many users have completed their decentralized identity verification. DID enables secure, self-sovereign identity on the blockchain.')

st.markdown("### 🛡️ DID Status Distribution")

if "didStatus" in user.columns:
    did_counts = user["didStatus"].fillna("not_started").value_counts().reset_index()
    did_counts.columns = ["Status", "Count"]
    did_colors = {"completed": "#10B981", "ready": "#10B981", "pending": "#F59E0B", "not_started": "#94A3B8", "none": "#94A3B8", "failed": "#EF4444"}

    d1, d2 = st.columns(2)
    with d1:
        fig_did = px.pie(
            did_counts, values="Count", names="Status",
            hole=0.55,
            color="Status",
            color_discrete_map=did_colors,
        )
        fig_did.update_traces(
            textinfo="label+percent+value",
            textfont=dict(size=11, color="#334155"),
        )
        fig_did.update_layout(
            title="🛡️ DID Verification Status",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#334155", family="Inter"),
            title_font=dict(color="#1E293B", size=15),
            height=380,
            margin=dict(l=10, r=10, t=55, b=10),
            legend=dict(
                font=dict(size=10, color="#475569"),
                bgcolor="rgba(248,250,252,0.8)",
                bordercolor="#E2E8F0",
                borderwidth=1,
            ),
        )
        st.plotly_chart(fig_did, width='stretch')

    with d2:
        # NFT minted over time with date picker
        if not nft.empty and "createdAt" in nft.columns:
            nft_ts = nft.copy()
            nft_ts["createdAt"] = pd.to_datetime(nft_ts["createdAt"], errors="coerce", utc=True).dt.tz_convert(None)
            nft_ts = nft_ts.dropna(subset=["createdAt"])

            nft_min = nft_ts["createdAt"].min().date()
            nft_max = nft_ts["createdAt"].max().date()

            nd1, nd2 = st.columns(2)
            with nd1:
                nft_from = st.date_input("📅 From", value=nft_min, key="nft_from")
            with nd2:
                nft_to = st.date_input("📅 To", value=nft_max, key="nft_to")

            nft_ts_from = pd.Timestamp(nft_from).normalize()
            nft_ts_to = pd.Timestamp(nft_to).normalize() + pd.Timedelta(days=1)
            nft_filtered = nft_ts[(nft_ts["createdAt"] >= nft_ts_from) & (nft_ts["createdAt"] < nft_ts_to)]

            nft_count_in_range = len(nft_filtered)
            nft_monthly = nft_filtered.set_index("createdAt").resample("ME").size().reset_index(name="minted")
            nft_monthly["month_label"] = nft_monthly["createdAt"].dt.strftime("%b %Y")

            fig_nft = go.Figure(go.Bar(
                x=nft_monthly["month_label"],
                y=nft_monthly["minted"],
                marker=dict(
                    color=nft_monthly["minted"],
                    colorscale=[[0, "#DDD6FE"], [0.5, "#8B5CF6"], [1, "#6D28D9"]],
                    showscale=False,
                ),
                text=nft_monthly["minted"],
                textposition="outside",
                textfont=dict(size=11, color="#334155"),
            ))
            fig_nft.update_layout(
                title=f"🎨 NFTs Minted Over Time  ·  {nft_count_in_range:,} in range",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#334155", family="Inter"),
                title_font=dict(color="#1E293B", size=15),
                height=350,
                margin=dict(l=10, r=20, t=55, b=10),
                xaxis=dict(gridcolor="rgba(0,0,0,0.06)", tickangle=-30),
                yaxis=dict(gridcolor="rgba(0,0,0,0.06)"),
                showlegend=False,
            )
            st.plotly_chart(fig_nft, width='stretch')
        else:
            st.info("No NFT minting data available.")
else:
    st.info("No DID status data available in user table.")

# ── Referral Analysis ─────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.info('🔗 **Referral Analysis** — Explore which referral codes drive the most signups. A strong referral network indicates healthy organic growth and community engagement.')

st.markdown("### 🔗 Referral Analysis")

has_referral = user["referralCode"].notna().sum() if "referralCode" in user.columns else 0
referred     = user["referredBy"].notna().sum() if "referredBy" in user.columns else 0
ref_rate     = referred / len(user) * 100 if len(user) > 0 else 0

# KPI row
rk1, rk2, rk3 = st.columns(3)
for col, (val, lbl) in zip([rk1, rk2, rk3], [
    (f"{has_referral:,}", "Users with Referral Code"),
    (f"{referred:,}", "Users who were Referred"),
    (f"{ref_rate:.1f}%", "Referral Conversion Rate"),
]):
    col.markdown(f"""<div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;
    padding:1rem;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
    <div style="font-size:1.8rem;font-weight:800;color:#1E293B">{val}</div>
    <div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:1px;color:#94A3B8;margin-top:4px">{lbl}</div>
    </div>""", unsafe_allow_html=True)

# Top 15 Referral Codes Chart
if "referredBy" in user.columns:
    ref_counts = user["referredBy"].dropna().value_counts().head(15).reset_index()
    ref_counts.columns = ["Referral Code", "Times Used"]
    ref_counts = ref_counts.sort_values("Times Used", ascending=True)

    fig_ref = go.Figure(go.Bar(
        y=ref_counts["Referral Code"],
        x=ref_counts["Times Used"],
        orientation="h",
        marker=dict(
            color="#F59E0B",
            line=dict(width=0),
        ),
        text=ref_counts["Times Used"],
        textposition="outside",
        textfont=dict(size=11, color="#334155"),
    ))
    fig_ref.update_layout(
        title="🏅 Top 15 Referral Codes Used",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#334155", family="Inter"),
        title_font=dict(color="#1E293B", size=15),
        height=450,
        margin=dict(l=10, r=60, t=55, b=30),
        xaxis=dict(title="Times Used", gridcolor="rgba(0,0,0,0.06)"),
        yaxis=dict(title="", gridcolor="rgba(0,0,0,0)"),
        showlegend=False,
    )
    st.plotly_chart(fig_ref, width='stretch')
else:
    st.info("No referral data available.")


# ── Signup Patterns — Day & Hour ──────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.info('📅 **Signup Patterns** — Understand when users register. Use the date range to analyze a specific week. Select a day to see its hourly breakdown.')

st.markdown("### 📅 Signup Patterns — Day & Hour")

if "createdAt" in user.columns:
    user_ts = user.copy()
    user_ts["createdAt"] = pd.to_datetime(user_ts["createdAt"], errors="coerce", utc=True).dt.tz_convert(None)
    user_ts = user_ts.dropna(subset=["createdAt"])

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # Date range for Day-of-Week chart
    _min_date = user_ts["createdAt"].min().date()
    _max_date = user_ts["createdAt"].max().date()
    _default_from = _max_date - pd.Timedelta(days=6)  # last 7 days by default
    if _default_from < _min_date:
        _default_from = _min_date

    dc1, dc2, dc3 = st.columns([2, 2, 2])
    with dc1:
        dow_from = st.date_input("From", value=_default_from, min_value=_min_date, max_value=_max_date, key="dow_from")
    with dc2:
        dow_to = st.date_input("To", value=_max_date, min_value=_min_date, max_value=_max_date, key="dow_to")
    with dc3:
        hour_day_filter = st.selectbox("Filter Hour Chart by Day:", ["All Days"] + day_order, index=0, key="hour_day_filter")

    # Filter data for date range
    _dow_from_ts = pd.Timestamp(dow_from)
    _dow_to_ts = pd.Timestamp(dow_to) + pd.Timedelta(days=1)
    user_ts_filtered = user_ts[(user_ts["createdAt"] >= _dow_from_ts) & (user_ts["createdAt"] < _dow_to_ts)]

    user_ts_filtered["day_of_week"] = user_ts_filtered["createdAt"].dt.day_name()
    user_ts_filtered["hour"] = user_ts_filtered["createdAt"].dt.hour

    sp1, sp2 = st.columns(2)

    with sp1:
        # By Day of Week (filtered by date range)
        day_counts = user_ts_filtered["day_of_week"].value_counts().reindex(day_order, fill_value=0).reset_index()
        day_counts.columns = ["Day", "Users"]

        # Highlight the peak day
        peak_day = day_counts.loc[day_counts["Users"].idxmax(), "Day"] if len(user_ts_filtered) > 0 else day_order[0]
        day_colors = ["#F59E0B" if d == peak_day else "#6B7DB3" for d in day_counts["Day"]]

        fig_dow = go.Figure(go.Bar(
            x=day_counts["Day"],
            y=day_counts["Users"],
            marker=dict(color=day_colors, line=dict(width=0)),
            text=day_counts["Users"],
            textposition="outside",
            textfont=dict(size=11, color="#334155"),
        ))
        fig_dow.update_layout(
            title=f"📆 By Day of Week  ({peak_day} = peak)",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#334155", family="Inter"),
            title_font=dict(color="#1E293B", size=14),
            height=380,
            margin=dict(l=10, r=10, t=55, b=10),
            xaxis=dict(gridcolor="rgba(0,0,0,0)", tickangle=-30),
            yaxis=dict(title="Users", gridcolor="rgba(0,0,0,0.06)"),
            showlegend=False,
        )
        st.plotly_chart(fig_dow, width='stretch')

    with sp2:
        # By Hour of Day — optionally filtered by selected day
        if hour_day_filter != "All Days":
            hour_data = user_ts_filtered[user_ts_filtered["day_of_week"] == hour_day_filter]
            hour_title = f"🕐 Hourly Signups on {hour_day_filter}s"
        else:
            hour_data = user_ts_filtered
            hour_title = "🕐 By Hour of Day (UTC)"

        hour_counts = hour_data["hour"].value_counts().reindex(range(24), fill_value=0).reset_index()
        hour_counts.columns = ["Hour", "Users"]
        hour_counts = hour_counts.sort_values("Hour")

        fig_hour = go.Figure(go.Bar(
            x=hour_counts["Hour"],
            y=hour_counts["Users"],
            marker=dict(
                color=hour_counts["Users"],
                colorscale=[[0, "#B2EBF2"], [0.5, "#4DD0E1"], [1, "#0097A7"]],
                showscale=False,
                line=dict(width=0),
            ),
            text=hour_counts["Users"],
            textposition="outside",
            textfont=dict(size=9, color="#334155"),
        ))
        fig_hour.update_layout(
            title=hour_title,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#334155", family="Inter"),
            title_font=dict(color="#1E293B", size=14),
            height=380,
            margin=dict(l=10, r=10, t=55, b=10),
            xaxis=dict(title="Hour", gridcolor="rgba(0,0,0,0)", dtick=2),
            yaxis=dict(title="Users", gridcolor="rgba(0,0,0,0.06)"),
            showlegend=False,
        )
        st.plotly_chart(fig_hour, width='stretch')

    # Summary insight
    if len(user_ts_filtered) > 0:
        peak_hour = int(hour_counts.loc[hour_counts["Users"].idxmax(), "Hour"])
        st.markdown(f"""
        <div style="background:rgba(5,150,105,0.06);border-left:3px solid #059669;
        border-radius:0 8px 8px 0;padding:0.7rem 1rem;margin:0.5rem 0 1rem 0;font-size:0.85rem;color:#475569">
        <b style="color:#1E293B">📊 Insight:</b> In the selected range ({dow_from} to {dow_to}), peak signup day is <b>{peak_day}</b> with {day_counts[day_counts['Day']==peak_day]['Users'].values[0]:,} registrations.
        Most signups occur around <b>{peak_hour}:00 UTC</b>.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("No signups in the selected date range.")
else:
    st.info("No timestamp data available for signup pattern analysis.")


# ── Top 20 Users Leaderboard ─────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.info('🏆 **Leaderboard** — The top 20 users ranked by lifetime reward points. High-ranking users are the most engaged customers on the platform and represent your core community.')

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


# ── RFM Segmentation Table ────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.info('📊 **RFM Analysis (Recency, Frequency, Monetary)** — Each user is scored on three dimensions: how recently they uploaded a bill (R), how frequently they upload (F), and how much they spend (M). Higher scores (5 = best) indicate stronger engagement. The RFM Total guides segmentation into Champions, Loyal, At Risk, etc.')

st.markdown("### 📋 RFM Segmentation Table")

# Build RFM data
_now = pd.Timestamp.now()
rfm = user[["id", "name", "email", "bill_count", "total_spend", "createdAt"]].copy()

# Recency: days since account creation (proxy — last bill would be better but this is simpler)
if not bill.empty and "userId" in bill.columns and "createdAt" in bill.columns:
    _last_bill = bill.dropna(subset=["createdAt"]).groupby("userId")["createdAt"].max().reset_index()
    _last_bill.columns = ["userId", "lastBillDate"]
    rfm = rfm.merge(_last_bill, left_on="id", right_on="userId", how="left", suffixes=("", "_lb"))
    rfm["Recency"] = (_now - rfm["lastBillDate"]).dt.days
    rfm["Recency"] = rfm["Recency"].fillna(9999).astype(int)
else:
    rfm["Recency"] = (_now - rfm["createdAt"]).dt.days.fillna(9999).astype(int)

rfm["Frequency"] = rfm["bill_count"].fillna(0).astype(int)
rfm["Monetary"] = rfm["total_spend"].fillna(0)

# Score R, F, M on a 1-5 scale using quantiles
# Safe scoring function that handles cases where qcut produces fewer bins than labels
def safe_qcut(series, q=5, ascending=True):
    """Score a series into 1-5 bins. ascending=True means higher values get higher scores."""
    try:
        if series.nunique() <= 1:
            return pd.Series([3] * len(series), index=series.index)
        labels = list(range(1, q + 1)) if ascending else list(range(q, 0, -1))
        result = pd.qcut(series.rank(method="first"), q, labels=labels, duplicates="drop")
        # If qcut dropped bins and labels don't match, fall back to rank-based
        return result.astype(int)
    except (ValueError, TypeError):
        # Fallback: simple rank-based scoring
        ranks = series.rank(pct=True)
        scores = pd.cut(ranks, bins=q, labels=list(range(1, q + 1)) if ascending else list(range(q, 0, -1)))
        return scores.fillna(3).astype(int)

# For Recency, lower is better so ascending=False (low recency → high score)
rfm["R"] = safe_qcut(rfm["Recency"], ascending=False)
rfm["F"] = safe_qcut(rfm["Frequency"], ascending=True)
rfm["M"] = safe_qcut(rfm["Monetary"], ascending=True)
rfm["RFM Total"] = rfm["R"] + rfm["F"] + rfm["M"]

# Segment based on RFM Total
def rfm_segment(score):
    if score >= 13: return "Champions"
    elif score >= 10: return "Loyal"
    elif score >= 7: return "Promising"
    elif score >= 5: return "At Risk"
    else: return "Hibernating"

rfm["Segment"] = rfm["RFM Total"].apply(rfm_segment)

# Format display table
rfm_display = rfm[["name", "email", "Recency", "Frequency", "Monetary", "R", "F", "M", "RFM Total", "Segment"]].copy()
rfm_display["Customer"] = rfm_display["name"].fillna("Unknown") + " (" + rfm_display["email"].fillna("") + ")"
rfm_display["Recency"] = rfm_display["Recency"].apply(lambda x: f"{x} days" if x < 9999 else "N/A")
rfm_display["Monetary"] = rfm_display["Monetary"].apply(lambda x: f"{x:,.0f}" if x > 0 else "0")
rfm_display = rfm_display.sort_values("RFM Total", ascending=False)

# ── Search & Filter for RFM Table ──────────────────────────────────────────
sf1, sf2 = st.columns([3, 1])
with sf1:
    rfm_search = st.text_input("🔍 Search by name or email", value="", key="rfm_search", placeholder="Type to search all users...")
with sf2:
    seg_options = ["All Segments"] + sorted(rfm_display["Segment"].unique().tolist())
    rfm_seg_filter = st.selectbox("Segment", seg_options, key="rfm_seg_filter")

# Apply search filter
rfm_filtered = rfm_display.copy()
if rfm_search.strip():
    _q = rfm_search.strip().lower()
    rfm_filtered = rfm_filtered[rfm_filtered["Customer"].str.lower().str.contains(_q, na=False)]
if rfm_seg_filter != "All Segments":
    rfm_filtered = rfm_filtered[rfm_filtered["Segment"] == rfm_seg_filter]

# Pagination
ROWS_PER_PAGE = 15
total_rows = len(rfm_filtered)
total_pages = max(1, (total_rows + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE)

# Use session state for page tracking so input can be below the table
if "rfm_pg" not in st.session_state:
    st.session_state["rfm_pg"] = 1
# Reset page if search changed
_pg = min(st.session_state["rfm_pg"], total_pages)
start_idx = (_pg - 1) * ROWS_PER_PAGE
end_idx = min(start_idx + ROWS_PER_PAGE, total_rows)
page_data = rfm_filtered.iloc[start_idx:end_idx]

st.dataframe(
    page_data[["Customer", "Recency", "Frequency", "Monetary", "R", "F", "M", "RFM Total", "Segment"]],
    width='stretch',
    hide_index=True,
    height=min(35 * len(page_data) + 40, 600),
)

# Pagination controls BELOW the table
st.number_input(
    f"Page (1–{total_pages})", min_value=1, max_value=total_pages,
    value=_pg, step=1, key="rfm_page",
    on_change=lambda: st.session_state.update({"rfm_pg": st.session_state["rfm_page"]})
)
st.caption(f"Showing {start_idx+1}–{end_idx} of {total_rows:,} users  ·  Page {_pg} of {total_pages}")



with st.sidebar:
    st.markdown("### 👥 Users")
    st.markdown(f"Total: **{len(user):,}**")
    st.markdown(f"Active (has bills): **{(user['bill_count']>0).sum():,}**")
    st.markdown(f"Avg bills/user: **{user['bill_count'].mean():.1f}**")

