import streamlit as st
import pandas as pd
import os

# Safely import the AI library
try:
    import google.generativeai as genai
    AI_MODULE_READY = True
except ModuleNotFoundError:
    AI_MODULE_READY = False

# Import the core financial engines
from calculations.allocation_engine import calculate_dynamic_waterfall
from calculations.financial_health import calculate_health_score
from calculations.retirement_engine import calculate_retirement_needs
from calculations.risk_engine import assess_risk_capacity, determine_asset_allocation

# ==========================================
# 1. PAGE CONFIGURATION & THEME
# ==========================================
st.set_page_config(
    page_title="FINPILOT | Wealth Engine",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Futuristic UI CSS Injection
st.markdown("""
    <style>
    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
    }
    .metric-card {
        background: linear-gradient(145deg, #111827, #1f2937);
        border-radius: 12px;
        padding: 20px;
        box-shadow:  5px 5px 10px #07090f, -5px -5px 10px #151d2d;
        border: 1px solid #374151;
        margin-bottom: 20px;
    }
    h1, h2, h3 {
        color: #60a5fa !important;
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    .neon-text {
        color: #34d399;
        text-shadow: 0 0 10px rgba(52, 211, 153, 0.5);
        font-size: 1.5rem;
        font-weight: bold;
    }
    .alert-text {
        color: #f87171;
        font-size: 0.9rem;
    }
    .success-text {
        color: #34d399;
        font-size: 0.9rem;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. STATE MANAGEMENT (CENTRAL DATA MODEL)
# ==========================================
if 'profile' not in st.session_state:
    st.session_state.profile = {
        'income': 50000,
        'essential_expenses': 20000,
        'debt_emi': 0,
        'dependents': 0,
        'emergency_fund_current': 10000,
        'has_health_insurance': False,
        'current_age': 25,
        'retirement_age': 60,
        'life_expectancy': 85,
        'current_retirement_corpus': 0,
        'risk_tolerance': 'Moderate'
    }

# ==========================================
# 3. SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown("### 💠 FINPILOT ENGINE")
    page = st.radio("System Modules", ["Dashboard", "Financial Profile", "AI Advisor"])
    
    st.markdown("---")
    st.markdown("### API Status")
    
    if not AI_MODULE_READY:
        st.error("Gemini Engine: WAITING FOR INSTALL")
    elif "API_KEY" in st.secrets:
        st.success("Gemini Engine: ONLINE")
        genai.configure(api_key=st.secrets["API_KEY"])
    else:
        st.error("Gemini Engine: OFFLINE")

# ==========================================
# 4. PAGE ROUTING & LOGIC
# ==========================================
if page == "Financial Profile":
    st.title("User Financial Profile")
    st.markdown("Update your baseline metrics. The engines will dynamically recalculate your roadmap.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Cash Flow & Debt")
        st.session_state.profile['income'] = st.number_input("Monthly Income (₹)", value=st.session_state.profile['income'], step=5000)
        st.session_state.profile['essential_expenses'] = st.number_input("Essential Expenses (₹)", value=st.session_state.profile['essential_expenses'], step=1000)
        st.session_state.profile['debt_emi'] = st.number_input("Monthly Debt/EMI (₹)", value=st.session_state.profile['debt_emi'], step=1000)
        
    with col2:
        st.subheader("Safety & Protection")
        st.session_state.profile['dependents'] = st.number_input("Number of Dependents", value=st.session_state.profile['dependents'], step=1, min_value=0)
        st.session_state.profile['emergency_fund_current'] = st.number_input("Current Emergency Savings (₹)", value=st.session_state.profile['emergency_fund_current'], step=10000)
        st.session_state.profile['has_health_insurance'] = st.checkbox("I have adequate Health Insurance", value=st.session_state.profile['has_health_insurance'])

    with col3:
        st.subheader("Retirement & Risk")
        st.session_state.profile['current_age'] = st.number_input("Current Age", value=st.session_state.profile['current_age'], step=1)
        st.session_state.profile['current_retirement_corpus'] = st.number_input("Current Retirement Savings (₹)", value=st.session_state.profile['current_retirement_corpus'], step=10000)
        st.session_state.profile['risk_tolerance'] = st.selectbox("Psychological Risk Tolerance", ["Conservative", "Moderate", "Aggressive"], index=1)

elif page == "Dashboard":
    st.title("Command Center")
    
    # Run core calculations
    health = calculate_health_score(st.session_state.profile)
    allocations = calculate_dynamic_waterfall(st.session_state.profile)
    risk_capacity = assess_risk_capacity(st.session_state.profile)
    
    # KPIs
    c1, c2, c3 = st.columns(3)
    with c1:
        surplus = st.session_state.profile['income'] - st.session_state.profile['essential_expenses'] - st.session_state.profile['debt_emi']
        st.markdown(f"""
        <div class="metric-card">
            <p>Available Monthly Surplus</p>
            <p class="neon-text">₹{surplus:,}</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <p>Financial Foundation Score</p>
            <p class="neon-text">{health['score']} / {health['max_score']}</p>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <p>Objective Risk Capacity</p>
            <p class="neon-text">{risk_capacity.upper()}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    # Tabbed Interface for deep dives
    tab1, tab2, tab3 = st.tabs(["Money Waterfall", "Foundation Status", "Retirement Engine"])
    
    with tab1:
        st.subheader("Where Every ₹100 Should Go")
        st.markdown("Calculated dynamically based on your liabilities and protection gaps, not fixed percentages.")
        if "error" not in allocations and "Warning" not in allocations:
            chart_data = pd.DataFrame([{"Category": k, "Percentage": v} for k, v in allocations.items() if v > 0])
            st.bar_chart(chart_data.set_index("Category"), height=350, color="#3b82f6")
        else:
            st.warning(allocations.get("Warning", "Invalid Income to calculate waterfall."))

    with tab2:
        st.subheader("Foundation Diagnostics")
        colA, colB = st.columns(2)
        with colA:
            st.markdown("#### ✅ Strengths")
            for strength in health['strong_points']:
                st.markdown(f"<span class='success-text'>• {strength}</span>", unsafe_allow_html=True)
        with colB:
            st.markdown("#### ⚠️ Immediate Priorities")
            for gap in health['attention_needed']:
                st.markdown(f"<span class='alert-text'>• {gap}</span>", unsafe_allow_html=True)

    with tab3:
        st.subheader("Retirement Trajectory")
        ret = calculate_retirement_needs(
            current_age=st.session_state.profile['current_age'],
            retirement_age=st.session_state.profile['retirement_age'],
            life_expectancy=st.session_state.profile['life_expectancy'],
            current_monthly_expenses=st.session_state.profile['essential_expenses'],
            current_retirement_corpus=st.session_state.profile['current_retirement_corpus']
        )
        if "error" not in ret:
            r1, r2, r3 = st.columns(3)
            r1.metric("Required Corpus (Inflation Adj)", f"₹{ret['required_corpus']:,.0f}")
            r2.metric("Projected Corpus Shortfall", f"₹{ret['corpus_shortfall']:,.0f}")
            r3.metric("Required Monthly SIP", f"₹{ret['required_monthly_investment']:,.0f}")
            st.caption("Assumes 6% inflation, 12% pre-retirement return, and 8% post-retirement return.")

elif page == "AI Advisor":
    st.title("Gemini Strategic Advisor")
    st.markdown("AI insights based strictly on your deterministic engine outputs.")
    
    if st.button("Generate Strategy Brief"):
        if AI_MODULE_READY and "API_KEY" in st.secrets:
            try:
                health = calculate_health_score(st.session_state.profile)
                capacity = assess_risk_capacity(st.session_state.profile)
                
                model = genai.GenerativeModel('gemini-1.5-pro')
                prompt = f"""
                Act as a strict, professional financial advisor.
                User's Financial Health Score: {health['score']}/100.
                Gaps identified: {health['attention_needed']}.
                Objective Risk Capacity: {capacity}.
                Psychological Risk Tolerance: {st.session_state.profile['risk_tolerance']}.
                
                Write a 3-paragraph executive summary to the user explaining:
                1. Their most critical vulnerability based on the gaps.
                2. Why their objective risk capacity dictates their investment strategy regardless of their psychological tolerance.
                3. The immediate next action they must take.
                Do not invent numbers. Be direct and professional.
                """
                response = model.generate_content(prompt)
                st.success(response.text)
            except Exception as e:
                st.error(f"Error connecting to Gemini: {e}")
        else:
            st.error("Cannot generate strategy. Check API Key and Module Status.")
