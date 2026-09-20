import streamlit as st
import pandas as pd
import time

# (Placeholder imports for your calculation engines)
# from calculations.allocation_engine import calculate_dynamic_waterfall
# from calculations.financial_health import calculate_health_score

st.set_page_config(page_title="FINPILOT | Wealth Engine", page_icon="💠", layout="centered")

# Load CSS
try:
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

# ==========================================
# STATE MANAGEMENT (The Wizard Memory)
# ==========================================
if 'step' not in st.session_state:
    st.session_state.step = 0

if 'profile' not in st.session_state:
    st.session_state.profile = {
        'intent': [],
        'income': 0, 'essential_expenses': 0, 'debt_emi': 0,
        'dependents': 0, 'emergency_fund_current': 0, 'has_health_insurance': False,
        'current_age': 25, 'risk_tolerance': 'Moderate'
    }

def next_step(): st.session_state.step += 1
def prev_step(): st.session_state.step -= 1
def reset(): st.session_state.step = 0

st.markdown("<br><br>", unsafe_allow_html=True)

# ==========================================
# STEP 0: INTENT SELECTION
# ==========================================
if st.session_state.step == 0:
    st.markdown("<h1 style='text-align: center;'>What brings you to <span class='primary-blue'>FINPILOT</span> today?</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8;'>Select the areas you want to focus on to customize your engine.</p><br>", unsafe_allow_html=True)
    
    intents = [
        "Goal-Based Planning", "Retirement Strategy", 
        "Education Planning", "Home Loan Analysis", 
        "Wealth Investment", "Building Emergency Fund", 
        "Debt Management", "Comprehensive Savings"
    ]
    
    selected_intents = st.multiselect("Select your priorities:", intents, placeholder="Choose your financial goals...")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Initialize Engine →"):
        if selected_intents:
            st.session_state.profile['intent'] = selected_intents
            next_step()
            st.rerun()
        else:
            st.warning("Please select at least one priority to continue.")

# ==========================================
# STEP 1: CASH FLOW WIZARD
# ==========================================
elif st.session_state.step == 1:
    st.markdown("<h2 style='text-align: center;'>Step 1: Cash Flow & Liabilities</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8;'>Let's establish your baseline liquidity.</p><br>", unsafe_allow_html=True)
    
    st.session_state.profile['income'] = st.number_input("Monthly Income (₹)", value=st.session_state.profile['income'], step=5000)
    st.session_state.profile['essential_expenses'] = st.number_input("Essential Monthly Expenses (₹)", value=st.session_state.profile['essential_expenses'], step=1000)
    st.session_state.profile['debt_emi'] = st.number_input("Total Monthly Debt/EMI (₹)", value=st.session_state.profile['debt_emi'], step=1000)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.button("← Back", on_click=prev_step)
    with col2:
        st.button("Next: Safety & Protection →", on_click=next_step)

# ==========================================
# STEP 2: PROTECTION WIZARD
# ==========================================
elif st.session_state.step == 2:
    st.markdown("<h2 style='text-align: center;'>Step 2: Safety & Protection</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8;'>Securing your financial foundation before investing.</p><br>", unsafe_allow_html=True)
    
    st.session_state.profile['dependents'] = st.number_input("Number of Dependents", value=st.session_state.profile['dependents'], step=1)
    st.session_state.profile['emergency_fund_current'] = st.number_input("Current Emergency Savings (₹)", value=st.session_state.profile['emergency_fund_current'], step=10000)
    st.session_state.profile['has_health_insurance'] = st.checkbox("I have an active Health Insurance policy")
    
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.button("← Back", on_click=prev_step)
    with col2:
        st.button("Next: Risk Profile →", on_click=next_step)

# ==========================================
# STEP 3: RISK & INVESTMENT WIZARD
# ==========================================
elif st.session_state.step == 3:
    st.markdown("<h2 style='text-align: center;'>Step 3: Investment Profile</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8;'>Aligning your psychology with your objective capacity.</p><br>", unsafe_allow_html=True)
    
    st.session_state.profile['current_age'] = st.number_input("Current Age", value=st.session_state.profile['current_age'], step=1)
    st.session_state.profile['risk_tolerance'] = st.select_slider("Psychological Risk Tolerance", options=["Conservative", "Moderate", "Aggressive"], value=st.session_state.profile['risk_tolerance'])
    
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.button("← Back", on_click=prev_step)
    with col2:
        st.button("Generate Dashboard ⚡", on_click=next_step)

# ==========================================
# STEP 4: FINAL DASHBOARD (Command Center)
# ==========================================
elif st.session_state.step == 4:
    with st.spinner("Processing multi-tier risk capacity and allocation models..."):
        time.sleep(1) # Simulating engine calculation time for a premium feel
        
    st.success("Financial Engine Synchronized.")
    st.markdown("<h1>Command Center</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: #94A3B8;'>Optimized for: {', '.join(st.session_state.profile['intent'])}</p>", unsafe_allow_html=True)
    
    surplus = st.session_state.profile['income'] - st.session_state.profile['essential_expenses'] - st.session_state.profile['debt_emi']
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class='metric-card'>
        <p style='color:#94A3B8; margin:0;'>Monthly Surplus</p>
        <p class='neon-text' style='margin:0;'>₹{surplus:,}</p>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class='metric-card'>
        <p style='color:#94A3B8; margin:0;'>Foundation Score</p>
        <p class='neon-text' style='margin:0;'>Pending</p>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class='metric-card'>
        <p style='color:#94A3B8; margin:0;'>Risk Capacity</p>
        <p class='neon-text' style='margin:0;'>Analyzing</p>
        </div>""", unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.button("↺ Recalibrate Profile", on_click=reset)
