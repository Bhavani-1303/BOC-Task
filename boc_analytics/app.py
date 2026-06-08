"""
app.py — Landing Page.
"""
import streamlit as st

st.set_page_config(
    page_title="BOC Analytics Platform",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for the glowing gradient landing page
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
    background-color: #0B0E14;
    color: #F8FAFC;
}

/* Hide sidebar and top header */
[data-testid="stSidebar"] { display: none; }
[data-testid="collapsedControl"] { display: none; }
header[data-testid="stHeader"] { display: none; }

/* Vertically center the content cleanly without huge gaps */
.block-container {
    padding-top: 25vh;
}

/* Typography styles */
.hero-icon {
    font-size: 5rem;
    margin-bottom: 1rem;
    filter: drop-shadow(0 0 20px rgba(251, 146, 60, 0.5));
}

.hero-title {
    font-size: 4rem;
    font-weight: 900;
    line-height: 1.1;
    margin-bottom: 1rem;
    background: linear-gradient(135deg, #06B6D4, #3B82F6, #8B5CF6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    font-size: 1.1rem;
    color: #94a3b8;
    max-width: 650px;
    margin: 0 auto 3rem auto;
    line-height: 1.6;
}

/* Glowing Pill Button Override */
div.stButton {
    display: flex;
    justify-content: center;
}
div.stButton > button {
    background: linear-gradient(135deg, #6366f1, #a855f7) !important;
    color: white !important;
    border: none !important;
    padding: 1.2rem 4rem !important;
    font-size: 1.2rem !important;
    font-weight: 700 !important;
    border-radius: 50px !important;
    box-shadow: 0 4px 15px -3px rgba(168, 85, 247, 0.4) !important;
    transition: all 0.3s ease !important;
}
div.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 20px -4px rgba(168, 85, 247, 0.5) !important;
}
</style>
""", unsafe_allow_html=True)

# Layout
st.markdown(
    """
    <div style='text-align: center;'>
        <div class="hero-icon">⚡</div>
        <h1 class="hero-title">BOC Analytics Platform</h1>
        <p class="hero-subtitle">
            Deep insights into user engagement, merchant trends, global expansion, and OCR bill extraction pipelines.
        </p>
    </div>
    """, 
    unsafe_allow_html=True
)

# Button nested inside a perfectly sized column so it centers natively
col1, col2, col3 = st.columns([1, 1.5, 1])
with col2:
    if st.button("Enter Dashboard ➔", type="primary", width='stretch'):
        st.switch_page("pages/1_📊_Overview.py")
