import streamlit as st
import pandas as pd
import os

# Safely import the AI library so the app doesn't crash if it's missing
try:
    import google.generativeai as genai
    AI_MODULE_READY = True
except ModuleNotFoundError:
    AI_MODULE_READY = False

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
        'goals': []
    }

# ==========================================
# 3. DYNAMIC ALLOCATION ENGINE (CORE LOGIC)
# ==========================================
def calculate_waterfall(profile):
    income = profile['income']
    if income <= 0:
        return {}

    expenses = profile['essential_expenses']
    debt = profile['debt_emi']
    surplus = income - expenses - debt
    
    protection_allocation = 0
    if not profile['has_health_insurance']:
        protection_allocation = min(surplus, int(income * 0.05)) 
        surplus -= protection_allocation

    emergency_target = expenses * 6
    emergency_allocation = 0
    if profile['emergency_fund_current'] < emergency_target:
        emergency_allocation = min(surplus, int(income * 0.15))
        surplus -= emergency_allocation

    investment_allocation = surplus * 0.70
    lifestyle_allocation = surplus * 0.30

    return {
        "Essential Expenses": (expenses / income) * 100,
        "Debt Obligations": (debt / income) * 100,
        "Protection & Insurance": (protection_allocation / income) * 100,
        "Emergency Reserve": (emergency_allocation / income) * 100,
        "Wealth & Goals": (investment_allocation / income) * 100,
        "Flexible Lifestyle": (lifestyle_allocation / income) * 100
    }

# ==========================================
# 4. SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown("### 💠 FINPILOT ENGINE")
    page = st.radio("System Modules", ["Dashboard", "Financial Profile", "AI Advisor"])
    
    st.markdown("---")
    st.markdown("### API Status")
    
    # Check both the module installation and the secret key
    if not AI_MODULE_READY:
        st.error("Gemini Engine: WAITING FOR INSTALL (Check requirements.txt)")
    elif "API_KEY" in st.secrets:
        st.success("Gemini Engine: ONLINE")
        genai.configure(api_key=st.secrets["API_KEY"])
    else:
        st.error("Gemini Engine: OFFLINE (Missing API Key)")

# ==========================================
# 5. PAGE ROUTING
# ==========================================
if page == "Financial Profile":
    st.title("User Financial Profile")
    st.markdown("Update your baseline metrics to recalculate the dynamic waterfall.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.profile['income'] = st.number_input("Monthly Income (₹)", value=st.session_state.profile['income'], step=5000)
        st.session_state.profile['essential_expenses'] = st.number_input("Essential Monthly Expenses (₹)", value=st.session_state.profile['essential_expenses'], step=1000)
        st.session_state.profile['debt_emi'] = st.number_input("Monthly Debt/EMI (₹)", value=st.session_state.profile['debt_emi'], step=1000)
    with col2:
        st.session_state.profile['dependents'] = st.number_input("Number of Dependents", value=st.session_state.profile['dependents'], step=1, min_value=0)
        st.session_state.profile['emergency_fund_current'] = st.number_input("Current Emergency Savings (₹)", value=st.session_state.profile['emergency_fund_current'], step=10000)
        st.session_state.profile['has_health_insurance'] = st.checkbox("I have adequate Health Insurance", value=st.session_state.profile['has_health_insurance'])

elif page == "Dashboard":
    st.title("Command Center")
    st.markdown("Your dynamically calculated financial waterfall.")
    
    allocations = calculate_waterfall(st.session_state.profile)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <p>Monthly Inflow</p>
            <p class="neon-text">₹{st.session_state.profile['income']:,}</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        surplus = st.session_state.profile['income'] - st.session_state.profile['essential_expenses'] - st.session_state.profile['debt_emi']
        st.markdown(f"""
        <div class="metric-card">
            <p>Available Surplus</p>
            <p class="neon-text">₹{surplus:,}</p>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        health_score = 85 if st.session_state.profile['has_health_insurance'] else 45
        st.markdown(f"""
        <div class="metric-card">
            <p>Foundation Score</p>
            <p class="neon-text">{health_score} / 100</p>
        </div>
        """, unsafe_allow_html=True)

    st.subheader("Where Every ₹100 Should Go (Dynamic Waterfall)")
    
    if allocations:
        chart_data = pd.DataFrame([
            {"Category": k, "Percentage": v} for k, v in allocations.items() if v > 0
        ])
        st.bar_chart(chart_data.set_index("Category"), height=400, color="#3b82f6")
    else:
        st.warning("Please update your profile to generate your allocation model.")

elif page == "AI Advisor":
    st.title("Gemini Strategic Advisor")
    st.markdown("AI insights based strictly on your deterministic profile outputs.")
    
    if st.button("Generate Strategy Brief"):
        if AI_MODULE_READY and "API_KEY" in st.secrets:
            try:
                model = genai.GenerativeModel('gemini-1.5-pro')
                prompt = f"Act as a strict, professional financial advisor. Analyze this user data: {st.session_state.profile}. Explain their most critical financial vulnerability right now in exactly 3 short sentences. Do not invent numbers."
                response = model.generate_content(prompt)
                st.success(response.text)
            except Exception as e:
                st.error(f"Error connecting to Gemini: {e}")
        else:
            st.error("Cannot generate strategy. Check API Key and Module Status in the sidebar.")
