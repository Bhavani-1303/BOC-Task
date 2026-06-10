"""
shared_styles.py — Shared CSS and sidebar branding for all pages.
Centralised so that every page gets consistent dark sidebar, bright table headers,
and the "Bills on Chain" branding title.
"""

import streamlit as st

# ── Common CSS ─────────────────────────────────────────────────────────────────
SHARED_CSS = """
<style>
/* ── Dark Sidebar ──────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%) !important;
    border-right: 1px solid #334155;
}
[data-testid="stSidebar"] * {
    color: #E2E8F0 !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4 {
    color: #FFFFFF !important;
}
[data-testid="stSidebar"] a {
    color: #93C5FD !important;
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMultiSelect label,
[data-testid="stSidebar"] .stSlider label,
[data-testid="stSidebar"] .stDateInput label {
    color: #CBD5E1 !important;
}
/* ── Sidebar widget inputs — dark background ─────────────────── */
[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"],
[data-testid="stSidebar"] .stMultiSelect [data-baseweb="select"] {
    background-color: #1E293B !important;
    border-color: #475569 !important;
}
[data-testid="stSidebar"] .stDateInput input,
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stNumberInput input {
    background-color: #1E293B !important;
    border-color: #475569 !important;
    color: #FFFFFF !important;
    caret-color: #FFFFFF !important;
}
/* Select/Multiselect — internal search input must be transparent */
[data-testid="stSidebar"] [data-baseweb="select"] input {
    background: transparent !important;
    color: #FFFFFF !important;
    caret-color: #FFFFFF !important;
}
/* Selected value text in selectbox */
[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] > div > div {
    color: #E2E8F0 !important;
}
/* Placeholder text in multiselect */
[data-testid="stSidebar"] .stMultiSelect [data-baseweb="select"] > div > div > div {
    color: #94A3B8 !important;
}
/* Multiselect pills/tags — styled with contrast */
[data-testid="stSidebar"] [data-baseweb="tag"] {
    background-color: #3B82F6 !important;
    color: #FFFFFF !important;
    border: none !important;
}
[data-testid="stSidebar"] [data-baseweb="tag"] span {
    color: #FFFFFF !important;
}
/* Tag close/remove button */
[data-testid="stSidebar"] [data-baseweb="tag"] [role="presentation"],
[data-testid="stSidebar"] [data-baseweb="tag"] svg {
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
}
/* Sidebar horizontal rule */
[data-testid="stSidebar"] hr {
    border-color: #334155 !important;
}

/* ── Main Content Inputs — keep them light ────────────────────── */
[data-testid="stAppViewContainer"] .stDateInput input,
[data-testid="stAppViewContainer"] .stTextInput input,
[data-testid="stAppViewContainer"] .stNumberInput input {
    background-color: #FFFFFF !important;
    border-color: #CBD5E1 !important;
    color: #1E293B !important;
    caret-color: #1E293B !important;
}
[data-testid="stAppViewContainer"] .stSelectbox [data-baseweb="select"],
[data-testid="stAppViewContainer"] .stMultiSelect [data-baseweb="select"] {
    background-color: #FFFFFF !important;
    border-color: #CBD5E1 !important;
}
/* Main area select search input — transparent bg with dark text */
[data-testid="stAppViewContainer"] [data-baseweb="select"] input {
    background: transparent !important;
    color: #1E293B !important;
    caret-color: #1E293B !important;
}
/* Main area selected value + placeholder text */
[data-testid="stAppViewContainer"] .stSelectbox [data-baseweb="select"] > div > div,
[data-testid="stAppViewContainer"] .stMultiSelect [data-baseweb="select"] span {
    color: #1E293B !important;
}
/* ── Dropdown popup menus (opened option lists) ──────────────── */
/* Main area popover — light background */
[data-baseweb="popover"],
[data-baseweb="menu"],
[data-baseweb="popover"] ul,
[data-baseweb="menu"] ul {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
}
[data-baseweb="popover"] li,
[data-baseweb="popover"] [role="option"],
[data-baseweb="menu"] li,
[data-baseweb="menu"] [role="option"] {
    background-color: #FFFFFF !important;
    color: #1E293B !important;
}
[data-baseweb="popover"] li *,
[data-baseweb="menu"] li * {
    color: #1E293B !important;
}
[data-baseweb="popover"] li:hover,
[data-baseweb="popover"] [role="option"]:hover,
[data-baseweb="menu"] li:hover,
[data-baseweb="menu"] [role="option"]:hover {
    background-color: #F1F5F9 !important;
}
/* Sidebar dropdown popover — dark background */
[data-testid="stSidebar"] [data-baseweb="popover"],
[data-testid="stSidebar"] [data-baseweb="menu"],
[data-testid="stSidebar"] [data-baseweb="popover"] ul,
[data-testid="stSidebar"] [data-baseweb="menu"] ul {
    background-color: #1E293B !important;
    border-color: #475569 !important;
}
[data-testid="stSidebar"] [data-baseweb="popover"] li,
[data-testid="stSidebar"] [data-baseweb="popover"] [role="option"],
[data-testid="stSidebar"] [data-baseweb="menu"] li,
[data-testid="stSidebar"] [data-baseweb="menu"] [role="option"] {
    background-color: #1E293B !important;
    color: #E2E8F0 !important;
}
[data-testid="stSidebar"] [data-baseweb="popover"] li *,
[data-testid="stSidebar"] [data-baseweb="menu"] li * {
    color: #E2E8F0 !important;
}
[data-testid="stSidebar"] [data-baseweb="popover"] li:hover,
[data-testid="stSidebar"] [data-baseweb="popover"] [role="option"]:hover {
    background-color: #334155 !important;
}
/* Fix radio button text in main area */
[data-testid="stAppViewContainer"] .stRadio label span {
    color: #1E293B !important;
}
/* Fix number_input text */
[data-testid="stAppViewContainer"] .stNumberInput input {
    background-color: #FFFFFF !important;
    border-color: #CBD5E1 !important;
    color: #1E293B !important;
}
/* Slider labels in sidebar */
[data-testid="stSidebar"] .stSlider div,
[data-testid="stSidebar"] .stSlider span {
    color: #E2E8F0 !important;
}

/* ── Streamlit Dataframe Table Headers ─────────────────────────── */
/* Make table headers bold and dark black with stronger styling */
[data-testid="stDataFrame"] th,
[data-testid="stDataFrame"] [role="columnheader"],
.dvn-scroller th,
[data-testid="glideDataEditor"] [role="columnheader"],
[data-testid="stDataFrame"] thead th,
.glideDataEditor [role="columnheader"] {
    font-weight: 800 !important;
    color: #000000 !important;
    background-color: #F1F5F9 !important;
    font-size: 0.88rem !important;
    letter-spacing: 0.3px !important;
}
/* Target the glide-data-grid header cells specifically */
.dvn-scroller .gdg-header-cell,
[data-testid="stDataFrame"] .gdg-header-cell {
    font-weight: 800 !important;
    color: #000000 !important;
}
/* Make header text inside canvas-based grids visible */
[data-testid="stDataFrame"] canvas + div [role="columnheader"] {
    font-weight: 800 !important;
    color: #000000 !important;
}

/* ── Remove Table Row Hover Color ──────────────────────────────── */
[data-testid="stDataFrame"] [role="row"]:hover,
[data-testid="stDataFrame"] tr:hover,
.dvn-scroller [role="row"]:hover,
[data-testid="glideDataEditor"] [role="row"]:hover {
    background-color: transparent !important;
}
[data-testid="stDataFrame"] [role="gridcell"]:hover,
.dvn-scroller [role="gridcell"]:hover {
    background-color: transparent !important;
}

/* ── Sidebar Navigation Link Styling ──────────────────────────── */
[data-testid="stSidebar"] [data-testid="stSidebarNav"] li {
    background: transparent;
}
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a span {
    color: #CBD5E1 !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarNav"] li[class*="st-emotion-cache"] a[aria-selected="true"] span {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

/* ── BillsOnChain Branding at TOP of sidebar (compact) ────────── */
[data-testid="stSidebar"]::before {
    content: "⛓️ BillsOnChain";
    display: block;
    padding: 0.8rem 1rem 0.2rem 1rem;
    font-size: 1.4rem;
    font-weight: 800;
    color: #FFFFFF !important;
    letter-spacing: -0.2px;
    line-height: 1.2;
}
[data-testid="stSidebar"]::after {
    content: "ANALYTICS";
    display: block;
    padding: 0 1rem 0.5rem 2.6rem;
    font-size: 0.5rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #64748B !important;
    border-bottom: 1px solid #334155;
    margin-bottom: 0.3rem;
}
</style>
"""

# ── Sidebar Branding ───────────────────────────────────────────────────────────
# NOTE: The branding is now done purely via CSS ::before/::after pseudo-elements
# on the sidebar container so it appears ABOVE the auto-generated navigation.
# The inject_sidebar_brand function below is kept for backward compatibility
# but no longer inserts HTML (to avoid duplicate branding).


def inject_shared_styles():
    """Inject the shared CSS into the current page."""
    st.markdown(SHARED_CSS, unsafe_allow_html=True)


def inject_sidebar_brand():
    """No-op — branding is now handled via CSS pseudo-elements at the top of sidebar."""
    pass
