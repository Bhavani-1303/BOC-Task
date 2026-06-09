"""
pages/1_📊_Overview.py — KPIs, trends, and bill pipeline
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from data_loader import load_all
from shared_styles import inject_shared_styles, inject_sidebar_brand

st.set_page_config(page_title="BOC · Overview", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;background:#FFFFFF;color:#1E293B;}
.page-title{font-size:2rem;font-weight:800;color:#1E293B;margin-bottom:0.2rem;}
.page-sub{color:#64748B;font-size:0.95rem;margin-bottom:1.5rem;}
.metric-box{background:#FFFFFF;border:1px solid #E2E8F0;
  border-radius:14px;padding:1.2rem 1.5rem;position:relative;overflow:hidden;
  box-shadow:0 1px 3px rgba(0,0,0,0.06);}
.metric-box::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;
  background:linear-gradient(90deg,#CBD5E1,#94A3B8);}
.m-val{font-size:1.9rem;font-weight:800;color:#1E293B;}
.m-lbl{font-size:0.75rem;text-transform:uppercase;letter-spacing:1px;color:#94A3B8;margin-top:2px;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0F172A,#1E293B) !important;
  border-right:1px solid #334155;}
.kpi-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 1rem;
    margin-bottom: 1rem;
}
.kpi-container-large {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

inject_shared_styles()
inject_sidebar_brand()

# ── Load real data from bocdata 1 ─────────────────────────────────────────────
dfs  = load_all()
bill = dfs.get("bill",            pd.DataFrame())
be   = dfs.get("bill_extraction", pd.DataFrame())
user = dfs.get("user",            pd.DataFrame())
fc   = dfs.get("fraud_check",     pd.DataFrame())
nft  = dfs.get("nft",             pd.DataFrame())
rc   = dfs.get("reward_credit",   pd.DataFrame())

# ── Derived KPI values (all from real data) ────────────────────────────────────
total_users     = len(user)
total_bills     = len(bill)
total_extracted = len(be)
bills_completed = int((bill["status"] == "completed").sum()) if "status" in bill.columns else 0
total_nfts      = len(nft)
total_merchants = int(be["merchantName"].nunique()) if "merchantName" in be.columns else 0
total_currencies= int(be["currency"].nunique())     if "currency"     in be.columns else 0

# Spend: Convert from INR to USD by dividing by 83
total_spend_num = (float(be["totalAmount"].sum()) / 83.0) if "totalAmount" in be.columns else 0
avg_spend_num   = (float(be["totalAmount"].mean()) / 83.0) if "totalAmount" in be.columns else 0
top_category    = be["category"].value_counts().idxmax() if "category" in be.columns and len(be) else "N/A"

# Fraud stats
fraud_passed    = int(fc["decision"].isin(["pass", "fraud_passed"]).sum()) if "decision" in fc.columns and len(fc) else 0
fraud_total     = len(fc)
fraud_pass_rate = (fraud_passed / fraud_total * 100) if fraud_total > 0 else 0

# ── Page Header ────────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">📊 Platform Overview</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Key performance indicators and platform-wide trends — sourced from BOC database</div>', unsafe_allow_html=True)

# ── KPI Cards (7 metrics from real data) ──────────────────────────────────────
kpis = [
    ("👥", f"{total_users:,}",       "Users"),
    ("🧾", f"{total_bills:,}",       "Bills Uploaded"),
    ("✅", f"{bills_completed:,}",   "Completed"),
    ("🔎", f"{total_extracted:,}",   "Extracted"),
    ("🖼️", f"{total_nfts:,}",        "NFTs Minted"),
    ("🏪", f"{total_merchants:,}",   "Merchants"),
    ("🌍", f"{total_currencies:,}",  "Currencies"),
]

kpi_html = '<div class="kpi-container">'
for icon, val, lbl in kpis:
    kpi_html += f"""
    <div class="metric-box">
        <div style="font-size:1.4rem">{icon}</div>
        <div class="m-val">{val}</div>
        <div class="m-lbl">{lbl}</div>
    </div>"""
kpi_html += '</div>'
st.markdown(kpi_html, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Second row of KPIs — spend metrics
k2_data = [
    ("💰", f"${total_spend_num:,.0f}", "Total Spend (USD)"),
    ("📊", f"${avg_spend_num:,.1f}",  "Avg Bill Amount (USD)"),
    ("🏷️", top_category.title(),     "Top Spend Category"),
    ("🛡️", f"{fraud_pass_rate:.1f}%","Fraud Pass Rate"),
]

k2_html = '<div class="kpi-container-large">'
for icon, val, lbl in k2_data:
    k2_html += f"""
    <div class="metric-box">
        <div style="font-size:1.4rem">{icon}</div>
        <div class="m-val">{val}</div>
        <div class="m-lbl">{lbl}</div>
    </div>"""
k2_html += '</div>'
st.markdown(k2_html, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

st.info('📈 **Monthly Trends & Activity** — The bar chart below tracks bill uploads over time, helping identify growth trends and seasonal spikes. The donut chart highlights user engagement, showing how many users actively upload bills vs. those who have gone inactive.')

# ── Row 1: Monthly Bills Uploaded (date-picker) + Category Treemap ────────────
r1c1, r1c2 = st.columns([3, 2])

with r1c1:
    if "createdAt" in bill.columns and len(bill):
        bill_ts = bill.dropna(subset=["createdAt"]).copy()

        min_date = bill_ts["createdAt"].min().date()
        max_date = bill_ts["createdAt"].max().date()

        dp_col1, dp_col2 = st.columns(2)
        with dp_col1:
            date_from = st.date_input(
                "📅 From", value=min_date,
                key="bills_from"
            )
        with dp_col2:
            date_to = st.date_input(
                "📅 To", value=max_date,
                key="bills_to"
            )
        st.caption(f"ℹ️ Data available: {min_date.strftime('%b %d, %Y')} — {max_date.strftime('%b %d, %Y')}")

        ts_from = pd.Timestamp(date_from).normalize()
        ts_to   = pd.Timestamp(date_to).normalize() + pd.Timedelta(days=1)
        bill_ts["_date"] = bill_ts["createdAt"].dt.normalize()
        mask = (bill_ts["_date"] >= ts_from) & (bill_ts["_date"] < ts_to)
        filtered_bills = bill_ts[mask]

        if len(filtered_bills) == 0:
            st.warning("No bills in the selected date range.")
        else:
            # Monthly aggregation — bars only
            filtered_bills = filtered_bills.set_index("createdAt")
            monthly = filtered_bills.resample("ME").agg(
                uploaded=("id", "count") if "id" in filtered_bills.columns
                         else ("status", "count"),
            ).reset_index()
            monthly.columns = ["month", "uploaded"]
            monthly["month_label"] = monthly["month"].dt.strftime("%b %Y")

            total_in_range = monthly["uploaded"].sum()
            fig = go.Figure(go.Bar(
                x=monthly["month_label"],
                y=monthly["uploaded"],
                name="Bills Uploaded",
                marker=dict(
                    color=monthly["uploaded"],
                    colorscale=[[0, "#C7D2FE"], [0.4, "#818CF8"], [1, "#4F46E5"]],
                    showscale=False,
                    line=dict(width=0),
                ),
                text=monthly["uploaded"],
                textposition="outside",
                textfont=dict(size=11, color="#334155"),
            ))
            fig.update_layout(
                title=f"📅 Monthly Bills Uploaded  ·  {total_in_range:,} bills in range",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#334155", family="Inter"),
                title_font=dict(color="#1E293B", size=15),
                height=380,
                margin=dict(l=10, r=20, t=55, b=10),
                xaxis=dict(
                    gridcolor="rgba(0,0,0,0.06)",
                    tickangle=-30,
                    tickfont=dict(size=10, color="#64748B"),
                ),
                yaxis=dict(
                    title="Bills Uploaded",
                    gridcolor="rgba(0,0,0,0.06)",
                    title_font=dict(color="#475569"),
                    tickfont=dict(color="#64748B"),
                ),
                showlegend=False,
            )
            st.plotly_chart(fig, width='stretch')


with r1c2:
    # ── Active vs Inactive Users donut ─────────────────────────────────────────
    # Compute bill_count for each user from the bill table
    if not user.empty and not bill.empty and "userId" in bill.columns:
        _bc = bill.groupby("userId").size().reset_index(name="bill_count")
        _user = user.merge(_bc, left_on="id", right_on="userId", how="left")
        _user["bill_count"] = _user["bill_count"].fillna(0).astype(int)
    elif not user.empty:
        _user = user.copy()
        _user["bill_count"] = 0
    else:
        _user = pd.DataFrame()

    if not _user.empty:
        active_count   = int((_user["bill_count"] > 0).sum())
        inactive_count = int((_user["bill_count"] == 0).sum())
        power_users    = int((_user["bill_count"] >= 10).sum())
        light_users    = int(((_user["bill_count"] >= 1) & (_user["bill_count"] < 10)).sum())

        status_df = pd.DataFrame({
            "Status": ["Power Users (10+ bills)", "Light Users (1–9 bills)", "Inactive (0 bills)"],
            "Count":  [power_users, light_users, inactive_count],
        })
        status_colors = {"Power Users (10+ bills)": "#10B981",
                         "Light Users (1–9 bills)": "#6366F1",
                         "Inactive (0 bills)":       "#EF4444"}

        fig = px.pie(
            status_df, values="Count", names="Status",
            title="👥 User Activity Status",
            hole=0.58,
            color="Status",
            color_discrete_map=status_colors,
        )
        fig.update_traces(
            textinfo="label+percent+value",
            textfont=dict(size=11, color="#334155"),
            pull=[0.04, 0.02, 0.02],
        )
        active_pct = active_count / max(len(_user), 1) * 100
        fig.update_layout(
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
                orientation="h",
                x=0.0, y=-0.12,
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

# ── Row 2: Bill Status Pipeline  +  Fraud Decision Donut ─────────────────────
st.info('⚙️ **Pipeline Health & Fraud Detection** — The status breakdown shows how bills move through the processing pipeline (upload → extraction → completion). The fraud detection chart reveals the pass/reject ratio from automated integrity checks.')
r2c1, r2c2 = st.columns(2)

with r2c1:
    if "status" in bill.columns and len(bill):
        s_counts = bill["status"].value_counts().reset_index()
        s_counts.columns = ["status", "count"]
        def status_color(s):
            if s in ["completed","minted","fraud_passed","extracted","hash_complete","uploaded","hashing"]:
                return "#10B981"
            elif any(k in s for k in ["fail","reject","flag","duplicate"]):
                return "#EF4444"
            return "#6366F1"
        s_counts["color"] = s_counts["status"].apply(status_color)
        s_counts = s_counts.sort_values("count", ascending=True)
        fig = go.Figure(go.Bar(
            x=s_counts["count"], y=s_counts["status"], orientation="h",
            marker_color=s_counts["color"],
            text=s_counts["count"],
            textposition="outside",
            textfont=dict(color="#334155", size=11),
        ))
        fig.update_layout(
            title="⚙️ Bill Status Breakdown",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#334155"), title_font=dict(color="#1E293B", size=15),
            height=400, margin=dict(l=10,r=80,t=50,b=10),
            xaxis=dict(gridcolor="rgba(0,0,0,0.06)"),
            yaxis=dict(gridcolor="rgba(0,0,0,0.06)", tickfont=dict(color="#475569")),
        )
        st.plotly_chart(fig, width='stretch')

with r2c2:
    if fraud_total > 0 and "decision" in fc.columns:
        d_counts = fc["decision"].value_counts().reset_index()
        d_counts.columns = ["decision", "count"]
        colors_map = {"fraud_passed": "#10B981", "fraud_rejected": "#EF4444", "pass": "#10B981", "fail": "#EF4444", "review": "#F59E0B"}
        fig = px.pie(
            d_counts, values="count", names="decision",
            title=f"🔍 Fraud Decision Split  ·  {fraud_total:,} checks",
            hole=0.60,
            color="decision",
            color_discrete_map=colors_map,
        )
        fig.update_traces(
            textinfo="label+percent+value",
            textfont=dict(size=12, color="#334155"),
            pull=[0.04] * len(d_counts),
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#334155", family="Inter"),
            title_font=dict(color="#1E293B", size=14),
            height=450,
            margin=dict(l=10, r=10, t=80, b=20),
            legend=dict(
                font=dict(size=11, color="#475569"),
                bgcolor="rgba(248,250,252,0.8)",
                bordercolor="#E2E8F0",
                borderwidth=1,
            ),
            annotations=[
                dict(
                    text=f"<b>{fraud_pass_rate:.0f}%</b><br>Pass",
                    x=0.5, y=0.5,
                    font=dict(size=18, color="#10B981"),
                    showarrow=False,
                )
            ],
        )
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No fraud check data available.")


# ── Row 3: Fraud Score Distribution  +  Fraud Checks by Vendor ────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.info('📊 **Fraud Analysis Deep Dive** — The histogram shows the distribution of fraud confidence scores (0 = definitely legitimate, 1 = definitely fraudulent). The vendor chart reveals which fraud-checking providers are most utilized. Flags highlight the most common reasons bills get flagged for review.')
if fraud_total > 0:

    import json
    from collections import Counter

    fa1, fa2 = st.columns(2)

    with fa1:
        if "score" in fc.columns and fc["score"].notna().sum() > 0:
            fig = px.histogram(
                fc.dropna(subset=["score"]), x="score", nbins=30,
                title="📊 Fraud Score Distribution",
                color_discrete_sequence=["#6366F1"],
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#334155"), title_font=dict(color="#1E293B", size=14),
                height=320, margin=dict(l=10, r=10, t=55, b=10),
                xaxis=dict(title="Fraud Score (0–1)", gridcolor="rgba(0,0,0,0.06)"),
                yaxis=dict(gridcolor="rgba(0,0,0,0.06)"),
                showlegend=False,
            )
            st.plotly_chart(fig, width='stretch')

    with fa2:
        if "vendor" in fc.columns:
            v_counts = fc["vendor"].value_counts().head(8).reset_index()
            v_counts.columns = ["vendor", "count"]
            fig = go.Figure(go.Bar(
                x=v_counts["count"][::-1],
                y=v_counts["vendor"][::-1],
                orientation="h",
                marker=dict(
                    color=v_counts["count"][::-1],
                    colorscale=[[0, "#C7D2FE"], [0.5, "#818CF8"], [1, "#4F46E5"]],
                    showscale=False,
                ),
                text=v_counts["count"][::-1],
                textposition="outside",
                textfont=dict(color="#334155", size=10),
            ))
            fig.update_layout(
                title="🏢 Fraud Checks by Vendor",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#334155"), title_font=dict(color="#1E293B", size=14),
                height=320, margin=dict(l=10, r=80, t=55, b=10),
                xaxis=dict(gridcolor="rgba(0,0,0,0.06)"),
                yaxis=dict(gridcolor="rgba(0,0,0,0.0)", tickfont=dict(size=10, color="#475569")),
            )
            st.plotly_chart(fig, width='stretch')

    # Fraud flags full-width below
    if "flags" in fc.columns and fc["flags"].notna().sum() > 0:
        all_flags = []
        for f_val in fc["flags"].dropna():
            try:
                parsed = json.loads(f_val) if isinstance(f_val, str) else f_val
                if isinstance(parsed, list):
                    all_flags.extend([str(x) for x in parsed])
                elif isinstance(parsed, dict):
                    all_flags.extend(parsed.keys())
            except Exception:
                pass
        if all_flags:
            flag_counts = Counter(all_flags)
            flag_df = pd.DataFrame(flag_counts.most_common(15), columns=["flag", "count"])
            fig = px.bar(
                flag_df, x="count", y="flag", orientation="h",
                title="🚩 Most Common Fraud Flags",
                color="count",
                color_continuous_scale=["#FEE2E2", "#F87171", "#DC2626"],
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#334155"), title_font=dict(color="#1E293B", size=13),
                height=350, margin=dict(l=10, r=10, t=50, b=10),
                xaxis=dict(gridcolor="rgba(0,0,0,0.06)"),
                yaxis=dict(gridcolor="rgba(0,0,0,0.0)", tickfont=dict(color="#475569")),
                coloraxis_showscale=False, showlegend=False,
            )
            st.plotly_chart(fig, width='stretch')

# ── Sidebar summary ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📊 Overview")
    st.markdown("---")
    st.markdown(f"**Users:** {total_users:,}")
    st.markdown(f"**Bills uploaded:** {total_bills:,}")
    st.markdown(f"**Bills completed:** {bills_completed:,}")
    st.markdown(f"**NFTs minted:** {total_nfts:,}")
    st.markdown(f"**Merchants seen:** {total_merchants:,}")
    st.markdown(f"**Currencies:** {total_currencies}")
    st.markdown("---")
    if fraud_total > 0:
        st.markdown(f"**Fraud checks:** {fraud_total:,}")
        st.markdown(f"**Fraud pass rate:** {fraud_pass_rate:.1f}%")
    if avg_spend_num > 0:
        st.markdown(f"**Avg bill amount:** ${avg_spend_num:,.1f} (USD)")
