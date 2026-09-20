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
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="FINPILOT | Wealth Engine",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Custom CSS dynamically
try:
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("assets/style.css not found. The app will use default Streamlit styling.")

# ==========================================
# 2. STATE MANAGEMENT 
# ==========================================
# Tracks whether the user is on the landing page or the main dashboard
if 'app_state' not in st.session_state:
    st.session_state.app_state = 'landing'

# Initializes the central data model with zeros to prevent hard-coding
if 'profile' not in st.session_state:
    st.session_state.profile = {
        'income': 0,
        'essential_expenses': 0,
        'debt_emi': 0,
        'dependents': 0,
        'emergency_fund_current': 0,
        'has_health_insurance': False,
        'current_age': 25,
        'retirement_age': 60,
        'life_expectancy': 85,
        'current_retirement_corpus': 0,
        'risk_tolerance': 'Moderate'
    }

# ==========================================
# 3. ROUTING: LANDING PAGE
# ==========================================
if st.session_state.app_state == 'landing':
    # CSS injection to force hide the sidebar and top header specifically for the landing page
    st.markdown("""
        <style>
            [data-testid="collapsedControl"] { display: none; }
            section[data-testid="stSidebar"] { display: none; }
            header { visibility: hidden; }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center; font-size: 4rem; color: #60a5fa;'>💠 FINPILOT</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #94a3b8;'>Your Dynamic Financial Planning Engine</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b;'>Stop relying on generic rules. Build a personalized financial waterfall based on objective risk capacity, dependency gaps, and real cash flow.</p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Centered Call-to-Action button
        c1, c2, c3 = st.columns([1, 1, 1])
        with c2:
            if st.button("Configure My Financial Engine", use_container_width=True):
                st.session_state.app_state = 'dashboard'
                st.rerun()

# ==========================================
# 4. ROUTING: MAIN DASHBOARD & SIDEBAR
# ==========================================
elif st.session_state.app_state == 'dashboard':
    
    # --- SIDEBAR (DATA INPUTS) ---
    with st.sidebar:
        st.markdown("### 💠 FINPILOT")
        st.markdown("---")
        
        st.markdown("**1. Cash Flow & Debt**")
        st.session_state.profile['income'] = st.number_input("Monthly Income (₹)", value=st.session_state.profile['income'], step=5000)
        st.session_state.profile['essential_expenses'] = st.number_input("Essential Expenses (₹)", value=st.session_state.profile['essential_expenses'], step=1000)
        st.session_state.profile['debt_emi'] = st.number_input("Monthly Debt/EMI (₹)", value=st.session_state.profile['debt_emi'], step=1000)
        
        st.markdown("**2. Safety & Protection**")
        st.session_state.profile['dependents'] = st.number_input("Dependents", value=st.session_state.profile['dependents'], step=1, min_value=0)
        st.session_state.profile['emergency_fund_current'] = st.number_input("Current Emergency Savings (₹)", value=st.session_state.profile['emergency_fund_current'], step=10000)
        st.session_state.profile['has_health_insurance'] = st.checkbox("I have Health Insurance", value=st.session_state.profile['has_health_insurance'])

        st.markdown("**3. Investment Profile**")
        st.session_state.profile['current_age'] = st.number_input("Current Age", value=st.session_state.profile['current_age'], step=1)
        st.session_state.profile['risk_tolerance'] = st.selectbox("Risk Tolerance", ["Conservative", "Moderate", "Aggressive"], index=1)
        
        st.markdown("---")
        # System checks
        if not AI_MODULE_READY:
            st.error("AI: OFFLINE")
        elif "API_KEY" in st.secrets:
            st.success("AI: ONLINE")
            genai.configure(api_key=st.secrets["API_KEY"])
        else:
            st.error("AI: KEY MISSING")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Return to Home", use_container_width=True):
            st.session_state.app_state = 'landing'
            st.rerun()

    # --- MAIN DASHBOARD (OUTPUTS) ---
    st.title("Command Center")
    
    # If income is 0, the user hasn't started entering data yet. Prevent division by zero.
    if st.session_state.profile['income'] == 0:
        st.info("👈 Please enter your Monthly Income in the sidebar to initialize the calculation engines.")
    
    else:
        # Run core calculations
        health = calculate_health_score(st.session_state.profile)
        allocations = calculate_dynamic_waterfall(st.session_state.profile)
        risk_capacity = assess_risk_capacity(st.session_state.profile)
        
        # Calculate Asset Strategy assuming a default long-term horizon (10 years) for general wealth
        asset_allocation = determine_asset_allocation(risk_capacity, st.session_state.profile['risk_tolerance'], 10)
        
        # Top KPI Cards
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
                <p>Foundation Score</p>
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
        
        # Deep Dive Modules
        tab1, tab2, tab3, tab4 = st.tabs(["Money Waterfall", "Foundation Status", "Asset Strategy", "AI Strategic Brief"])
        
        with tab1:
            st.subheader("Where Every ₹100 Should Go")
            st.markdown("Calculated dynamically based on your liabilities and protection gaps.")
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
            st.subheader("Recommended Asset Allocation")
            st.markdown(f"**Strategy:** {asset_allocation['Strategy']}")
            st.markdown("This allocation bounds your psychological risk tolerance to your objective financial capacity.")
            
            # Clean dictionary for the chart
            asset_data = {k: v for k, v in asset_allocation.items() if k != 'Strategy'}
            pie_data = pd.DataFrame([{"Asset": k, "Allocation (%)": v} for k, v in asset_data.items() if v > 0])
            st.bar_chart(pie_data.set_index("Asset"), height=300, color="#34d399")
            
        with tab4:
            st.subheader("Gemini Intelligence")
            st.markdown("AI insights based strictly on your deterministic engine outputs.")
            
            if st.button("Generate Strategy Brief", type="primary"):
                if AI_MODULE_READY and "API_KEY" in st.secrets:
                    try:
                        with st.spinner("Analyzing financial engines..."):
                            model = genai.GenerativeModel('gemini-1.5-pro')
                            prompt = f'''
                            Act as a strict, professional financial advisor.
                            User's Financial Health Score: {health['score']}/100.
                            Gaps identified: {health['attention_needed']}.
                            Objective Risk Capacity: {risk_capacity}.
                            Psychological Risk Tolerance: {st.session_state.profile['risk_tolerance']}.
                            
                            Write a 3-paragraph executive summary explaining:
                            1. Their most critical vulnerability based on the gaps.
                            2. Why their objective risk capacity dictates their investment strategy regardless of their psychological tolerance.
                            3. The immediate next action they must take.
                            Do not invent numbers. Be direct and professional.
                            '''
                            response = model.generate_content(prompt)
                            st.info(response.text)
                    except Exception as e:
                        st.error(f"Error connecting to Gemini: {e}")
                else:
                    st.error("Cannot generate strategy. Check API Key and Module Status in the sidebar.")
