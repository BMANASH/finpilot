import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time

from calculations.allocation_engine import calculate_dynamic_waterfall
from calculations.financial_health import calculate_health_score
from calculations.risk_engine import assess_risk_capacity, determine_asset_allocation
from calculations.retirement_engine import calculate_retirement_needs
from calculations.goals_engine import categorize_goal, calculate_required_pmt, evaluate_goal_conflict

st.set_page_config(page_title="FINPILOT | Wealth Engine", page_icon="💠", layout="centered")

# ==========================================
# THEME
# ==========================================
COLOR_MAP = {
    "Essential Living": "#64748B",
    "Debt Repayment": "#EF4444",
    "Protection (Insurance)": "#F59E0B",
    "Emergency Fund": "#38BDF8",
    "Retirement": "#8B5CF6",
    "Goal Funding & Wealth": "#10B981",
    "Flexible/Lifestyle": "#3B82F6",
    "Equity": "#10B981",
    "Debt": "#38BDF8",
    "Liquid/Cash": "#64748B",
    "Gold": "#F59E0B",
}

# Load CSS
try:
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass


def money(x) -> str:
    try:
        return f"₹{x:,.0f}"
    except (TypeError, ValueError):
        return "₹0"


def donut_chart(data: dict, center_text: str = "") -> go.Figure:
    labels = list(data.keys())
    values = list(data.values())
    colors = [COLOR_MAP.get(l, "#3B82F6") for l in labels]
    fig = go.Figure(data=[go.Pie(
        labels=labels, values=values, hole=0.62,
        marker=dict(colors=colors, line=dict(color="#0A1128", width=3)),
        textinfo="percent", textfont=dict(color="white", size=13),
        hovertemplate="%{label}<br>%{value}%<extra></extra>",
        sort=False,
    )])
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="v", font=dict(color="#CBD5E1", size=12), x=1, y=0.5),
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=320,
        annotations=[dict(text=center_text, x=0.5, y=0.5, font=dict(size=16, color="white"), showarrow=False)],
    )
    return fig


def gauge_chart(score: int, max_score: int = 100) -> go.Figure:
    if score >= 80:
        bar_color = "#10B981"
    elif score >= 60:
        bar_color = "#38BDF8"
    elif score >= 40:
        bar_color = "#F59E0B"
    else:
        bar_color = "#EF4444"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number=dict(font=dict(color="white", size=36), suffix=f"/{max_score}"),
        gauge=dict(
            axis=dict(range=[0, max_score], tickcolor="#334155", tickfont=dict(color="#94A3B8")),
            bar=dict(color=bar_color, thickness=0.35),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            steps=[
                dict(range=[0, 40], color="rgba(239,68,68,0.12)"),
                dict(range=[40, 60], color="rgba(245,158,11,0.12)"),
                dict(range=[60, 80], color="rgba(56,189,248,0.12)"),
                dict(range=[80, max_score], color="rgba(16,185,129,0.12)"),
            ],
        ),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=30, b=10),
        height=260,
    )
    return fig


def status_badge(ok: bool, review: bool = False) -> str:
    if ok:
        return "<span class='pill pill-ok'>✓ Covered</span>"
    if review:
        return "<span class='pill pill-review'>⚠ Review</span>"
    return "<span class='pill pill-missing'>✕ Missing</span>"


# ==========================================
# STATE MANAGEMENT (The Wizard Memory)
# ==========================================
DEFAULT_PROFILE = {
    'intent': [],
    'income': 0, 'essential_expenses': 0, 'debt_emi': 0,
    'dependents': 0, 'emergency_fund_current': 0, 'has_health_insurance': False,
    'has_term_insurance': False, 'has_accident_insurance': False,
    'current_age': 25, 'retirement_age': 60, 'life_expectancy': 85,
    'existing_retirement_corpus': 0, 'risk_tolerance': 'Moderate',
    'goals': [
        {"Goal": "Emergency Trip Fund", "Target (₹)": 200000, "Saved So Far (₹)": 20000, "Years Away": 2.0},
        {"Goal": "New Car", "Target (₹)": 900000, "Saved So Far (₹)": 100000, "Years Away": 4.0},
    ],
}

if 'step' not in st.session_state:
    st.session_state.step = 0

if 'profile' not in st.session_state:
    st.session_state.profile = {k: (v.copy() if isinstance(v, (list, dict)) else v) for k, v in DEFAULT_PROFILE.items()}


def next_step(): st.session_state.step += 1
def prev_step(): st.session_state.step -= 1
def reset():
    st.session_state.step = 0
    st.session_state.profile = {k: (v.copy() if isinstance(v, (list, dict)) else v) for k, v in DEFAULT_PROFILE.items()}


TOTAL_WIZARD_STEPS = 5  # steps 0-4 before the dashboard (step 5)

if 0 <= st.session_state.step < TOTAL_WIZARD_STEPS:
    st.progress(st.session_state.step / (TOTAL_WIZARD_STEPS - 1) if TOTAL_WIZARD_STEPS > 1 else 0)

st.markdown("<br>", unsafe_allow_html=True)

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

    selected_intents = st.multiselect(
        "Select your priorities:", intents,
        default=st.session_state.profile.get('intent', []),
        placeholder="Choose your financial goals..."
    )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Initialize Engine →", width='stretch'):
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
    st.markdown("<h2 style='text-align: center;'>Step 1 of 5 · Cash Flow & Liabilities</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8;'>Let's establish your baseline liquidity.</p><br>", unsafe_allow_html=True)

    p = st.session_state.profile
    p['income'] = st.number_input("Monthly Income (₹)", min_value=0, value=p['income'], step=5000)
    p['essential_expenses'] = st.number_input("Essential Monthly Expenses (₹)", min_value=0, value=p['essential_expenses'], step=1000)
    p['debt_emi'] = st.number_input("Total Monthly Debt/EMI (₹)", min_value=0, value=p['debt_emi'], step=1000)

    if p['income'] > 0:
        live_surplus = p['income'] - p['essential_expenses'] - p['debt_emi']
        color = "success-text" if live_surplus >= 0 else "alert-text"
        st.markdown(f"<p class='{color}'>Live surplus: {money(live_surplus)} / month</p>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.button("← Back", on_click=prev_step, width='stretch')
    with col2:
        st.button("Next: Safety & Protection →", on_click=next_step, width='stretch')

# ==========================================
# STEP 2: PROTECTION WIZARD
# ==========================================
elif st.session_state.step == 2:
    st.markdown("<h2 style='text-align: center;'>Step 2 of 5 · Safety & Protection</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8;'>Securing your financial foundation before investing.</p><br>", unsafe_allow_html=True)

    p = st.session_state.profile
    p['dependents'] = st.number_input("Number of Dependents", min_value=0, value=p['dependents'], step=1)
    p['emergency_fund_current'] = st.number_input("Current Emergency Savings (₹)", min_value=0, value=p['emergency_fund_current'], step=10000)

    c1, c2, c3 = st.columns(3)
    with c1:
        p['has_health_insurance'] = st.checkbox("Health Insurance", value=p['has_health_insurance'])
    with c2:
        p['has_term_insurance'] = st.checkbox("Term Life Insurance", value=p['has_term_insurance'])
    with c3:
        p['has_accident_insurance'] = st.checkbox("Personal Accident Cover", value=p['has_accident_insurance'])

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.button("← Back", on_click=prev_step, width='stretch')
    with col2:
        st.button("Next: Risk Profile →", on_click=next_step, width='stretch')

# ==========================================
# STEP 3: RISK & INVESTMENT WIZARD
# ==========================================
elif st.session_state.step == 3:
    st.markdown("<h2 style='text-align: center;'>Step 3 of 5 · Investment & Retirement Profile</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8;'>Aligning your psychology with your objective capacity.</p><br>", unsafe_allow_html=True)

    p = st.session_state.profile
    c1, c2 = st.columns(2)
    with c1:
        p['current_age'] = st.number_input("Current Age", min_value=18, max_value=80, value=p['current_age'], step=1)
    with c2:
        p['retirement_age'] = st.number_input("Target Retirement Age", min_value=p['current_age'] + 1, max_value=90, value=max(p['retirement_age'], p['current_age'] + 1), step=1)

    c3, c4 = st.columns(2)
    with c3:
        p['life_expectancy'] = st.number_input("Life Expectancy Assumption", min_value=p['retirement_age'] + 1, max_value=110, value=max(p['life_expectancy'], p['retirement_age'] + 1), step=1)
    with c4:
        p['existing_retirement_corpus'] = st.number_input("Existing Retirement Savings (₹)", min_value=0, value=p['existing_retirement_corpus'], step=10000)

    p['risk_tolerance'] = st.select_slider("Psychological Risk Tolerance", options=["Conservative", "Moderate", "Aggressive"], value=p['risk_tolerance'])
    st.caption("This reflects comfort with market volatility. FINPILOT will separately check whether your finances can actually support it before recommending an allocation.")

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.button("← Back", on_click=prev_step, width='stretch')
    with col2:
        st.button("Next: Goals →", on_click=next_step, width='stretch')

# ==========================================
# STEP 4: GOALS WIZARD
# ==========================================
elif st.session_state.step == 4:
    st.markdown("<h2 style='text-align: center;'>Step 4 of 5 · Your Goals</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8;'>Add, edit, or remove rows. Each goal will be classified and costed automatically.</p><br>", unsafe_allow_html=True)

    goals_df = pd.DataFrame(st.session_state.profile['goals'])
    edited = st.data_editor(
        goals_df,
        num_rows="dynamic",
        width='stretch',
        column_config={
            "Goal": st.column_config.TextColumn(required=True),
            "Target (₹)": st.column_config.NumberColumn(min_value=0, step=10000, format="₹%d"),
            "Saved So Far (₹)": st.column_config.NumberColumn(min_value=0, step=5000, format="₹%d"),
            "Years Away": st.column_config.NumberColumn(min_value=0.5, max_value=50.0, step=0.5),
        },
        key="goals_editor",
    )
    st.session_state.profile['goals'] = edited.fillna(0).to_dict("records")

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.button("← Back", on_click=prev_step, width='stretch')
    with col2:
        st.button("Generate Dashboard ⚡", on_click=next_step, width='stretch')

# ==========================================
# STEP 5: FINAL DASHBOARD (Command Center)
# ==========================================
elif st.session_state.step == 5:
    p = st.session_state.profile

    with st.spinner("Processing multi-tier risk capacity and allocation models..."):
        time.sleep(0.6)
        health = calculate_health_score(p)
        risk_capacity = assess_risk_capacity(p)
        years_to_retirement = max(p['retirement_age'] - p['current_age'], 1)
        allocation_mix = determine_asset_allocation(risk_capacity, p['risk_tolerance'], time_horizon=years_to_retirement)
        waterfall = calculate_dynamic_waterfall(p)
        retirement = calculate_retirement_needs(
            current_age=p['current_age'], retirement_age=p['retirement_age'],
            life_expectancy=p['life_expectancy'], current_monthly_expenses=p['essential_expenses'],
            current_retirement_corpus=p['existing_retirement_corpus'],
        )

        surplus = p['income'] - p['essential_expenses'] - p['debt_emi']
        goal_funding_pool = waterfall.get('goal_and_wealth_amount', max(surplus, 0) * 0.5) if not waterfall.get('warning') else 0

        priced_goals = []
        for g in p['goals']:
            name = g.get('Goal') or "Untitled Goal"
            target = float(g.get('Target (₹)', 0) or 0)
            current = float(g.get('Saved So Far (₹)', 0) or 0)
            years = float(g.get('Years Away', 0) or 0)
            expected_return = 0.07 if years <= 3 else (0.09 if years <= 7 else 0.12)
            required_monthly = calculate_required_pmt(target, current, years, expected_return)
            priced_goals.append({
                "Goal": name, "Category": categorize_goal(years), "Target (₹)": target,
                "Saved (₹)": current, "Years": years, "Assumed Return": f"{expected_return*100:.0f}%",
                "Required Monthly (₹)": required_monthly,
                "Progress": min(current / target, 1.0) if target > 0 else 0.0,
            })
        conflict = evaluate_goal_conflict(
            [{"required_monthly": g["Required Monthly (₹)"]} for g in priced_goals],
            goal_funding_pool,
        )

    st.success("Financial Engine Synchronized.")
    st.markdown("<h1>Command Center</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: #94A3B8;'>Optimized for: {', '.join(p['intent']) if p['intent'] else 'General Planning'}</p>", unsafe_allow_html=True)

    tabs = st.tabs(["📊 Overview", "🛡️ Protection", "💧 Money Plan", "🎯 Goals", "🏖️ Retirement", "📈 Investments"])

    # ---------- OVERVIEW ----------
    with tabs[0]:
        c1, c2, c3 = st.columns(3)
        with c1:
            color = "neon-text" if surplus >= 0 else "alert-text"
            st.markdown(f"""<div class='metric-card'>
            <p style='color:#94A3B8; margin:0;'>Monthly Surplus</p>
            <p class='{color}' style='margin:0;'>{money(surplus)}</p>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class='metric-card'>
            <p style='color:#94A3B8; margin:0;'>Foundation Score</p>
            <p class='neon-text' style='margin:0;'>{health['score']} / {health['max_score']}</p>
            <p style='color:#94A3B8; margin:0; font-size:0.85rem;'>{health['rating']}</p>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class='metric-card'>
            <p style='color:#94A3B8; margin:0;'>Risk Capacity</p>
            <p class='neon-text' style='margin:0;'>{risk_capacity}</p>
            <p style='color:#94A3B8; margin:0; font-size:0.85rem;'>Tolerance: {p['risk_tolerance']}</p>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        gc1, gc2 = st.columns([1, 1.4])
        with gc1:
            st.plotly_chart(gauge_chart(health['score']), width='stretch', config={"displayModeBar": False})
        with gc2:
            st.markdown("#### Your Next Actions")
            actions = (health['attention_needed'][:2] if health['attention_needed'] else []) 
            if conflict.get('has_conflict'):
                actions.append(f"Your goals need {money(conflict['monthly_shortfall'])} more per month than is available — revisit priorities in the Goals tab.")
            if not actions:
                actions = ["No urgent gaps detected — consider increasing long-term wealth contributions."]
            for i, a in enumerate(actions[:3], start=1):
                st.markdown(f"<div class='action-item'><span class='action-num'>{i}</span>{a}</div>", unsafe_allow_html=True)

    # ---------- PROTECTION ----------
    with tabs[1]:
        months_ef = (p['emergency_fund_current'] / p['essential_expenses']) if p['essential_expenses'] > 0 else 0
        st.markdown("#### Protection Status")
        pc1, pc2, pc3, pc4 = st.columns(4)
        with pc1:
            st.markdown(f"<div class='metric-card' style='text-align:center;'><p style='color:#94A3B8;margin:0;'>Health</p>{status_badge(p['has_health_insurance'])}</div>", unsafe_allow_html=True)
        with pc2:
            if p['dependents'] == 0:
                st.markdown(f"<div class='metric-card' style='text-align:center;'><p style='color:#94A3B8;margin:0;'>Term Life</p><span class='pill pill-na'>— Not required</span></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='metric-card' style='text-align:center;'><p style='color:#94A3B8;margin:0;'>Term Life</p>{status_badge(p['has_term_insurance'], review=True)}</div>", unsafe_allow_html=True)
        with pc3:
            st.markdown(f"<div class='metric-card' style='text-align:center;'><p style='color:#94A3B8;margin:0;'>Accident</p>{status_badge(p['has_accident_insurance'], review=True)}</div>", unsafe_allow_html=True)
        with pc4:
            ef_ok = months_ef >= 6
            st.markdown(f"<div class='metric-card' style='text-align:center;'><p style='color:#94A3B8;margin:0;'>Emergency Fund</p>{status_badge(ef_ok, review=(0 < months_ef < 6))}</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.progress(min(months_ef / 6, 1.0), text=f"Emergency fund: {months_ef:.1f} of 6 target months covered")

        st.markdown("<br>", unsafe_allow_html=True)
        sp_col, an_col = st.columns(2)
        with sp_col:
            st.markdown("**Strong points**")
            for s in health['strong_points']:
                st.markdown(f"<p class='success-text'>✓ {s}</p>", unsafe_allow_html=True)
        with an_col:
            st.markdown("**Needs attention**")
            for a in health['attention_needed']:
                st.markdown(f"<p class='alert-text'>⚠ {a}</p>", unsafe_allow_html=True)

        with st.expander("Why this score?"):
            st.caption("Financial Foundation Score = Cash Flow (30) + Emergency Liquidity (25) + Debt Burden (25) + Protection (20).")
            st.json({
                "income": p['income'], "essential_expenses": p['essential_expenses'], "debt_emi": p['debt_emi'],
                "emergency_fund_current": p['emergency_fund_current'], "has_health_insurance": p['has_health_insurance'],
                "dependents": p['dependents'],
            })

    # ---------- MONEY PLAN ----------
    with tabs[2]:
        if waterfall.get('warning'):
            st.error(waterfall['warning'])
        else:
            mc1, mc2 = st.columns([1.3, 1])
            with mc1:
                st.plotly_chart(donut_chart(waterfall['percentages'], center_text="Your ₹100"), width='stretch', config={"displayModeBar": False})
            with mc2:
                st.markdown("#### Where each ₹ goes")
                for cat, amt in waterfall['amounts'].items():
                    pct = waterfall['percentages'].get(cat, 0)
                    st.markdown(
                        f"<div class='alloc-row'><span class='alloc-dot' style='background:{COLOR_MAP.get(cat,'#3B82F6')}'></span>"
                        f"<span class='alloc-label'>{cat}</span><span class='alloc-value'>{money(amt)} · {pct}%</span></div>",
                        unsafe_allow_html=True,
                    )
            with st.expander("Why is my allocation different from a generic 50/30/20?"):
                st.caption(
                    "FINPILOT first covers essentials and debt, then reserves a protection budget if health "
                    "insurance is missing or dependents exist, then funds the emergency reserve toward a 6-month "
                    "target, then a baseline retirement contribution, and only then splits the remainder between "
                    "long-term goals/wealth and flexible spending."
                )

    # ---------- GOALS ----------
    with tabs[3]:
        st.markdown(f"#### Monthly surplus available for goals & wealth: {money(goal_funding_pool)}")
        if conflict.get('has_conflict'):
            st.markdown(
                f"<div class='alert-banner'>⚠ Your goals require {money(conflict['total_required'])}/month but only "
                f"{money(conflict['available_surplus'])} is available — a shortfall of {money(conflict['monthly_shortfall'])}. "
                f"Consider adjusting target dates, amounts, or priority in the table above.</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(f"<p class='success-text'>✓ Your goal contributions fit within your available surplus.</p>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        for g in priced_goals:
            st.markdown(f"**{g['Goal']}** · {g['Category']} · assumed return {g['Assumed Return']}")
            st.progress(g['Progress'], text=f"{money(g['Saved (₹)'])} of {money(g['Target (₹)'])} saved")
            st.markdown(f"<p style='color:#94A3B8; margin-top:-6px;'>Requires ~{money(g['Required Monthly (₹)'])}/month for {g['Years']} years</p>", unsafe_allow_html=True)
            st.markdown("<hr style='border-color:#1E293B;'>", unsafe_allow_html=True)

    # ---------- RETIREMENT ----------
    with tabs[4]:
        if 'error' in retirement:
            st.error(retirement['error'])
        else:
            rc1, rc2, rc3 = st.columns(3)
            with rc1:
                st.markdown(f"<div class='metric-card'><p style='color:#94A3B8;margin:0;'>Required Corpus</p><p class='neon-text' style='margin:0;'>{money(retirement['required_corpus'])}</p></div>", unsafe_allow_html=True)
            with rc2:
                st.markdown(f"<div class='metric-card'><p style='color:#94A3B8;margin:0;'>Projected Corpus</p><p class='neon-text' style='margin:0;'>{money(retirement['projected_existing_corpus'])}</p></div>", unsafe_allow_html=True)
            with rc3:
                gap = retirement['corpus_shortfall']
                gap_color = "alert-text" if gap > 0 else "success-text"
                st.markdown(f"<div class='metric-card'><p style='color:#94A3B8;margin:0;'>Shortfall</p><p class='{gap_color}' style='margin:0; font-size:1.75rem; font-weight:700;'>{money(gap)}</p></div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"To close this gap, FINPILOT estimates a required monthly SIP of **{money(retirement['required_monthly_investment'])}** over {retirement['years_to_retirement']} years.")

            st.markdown("#### Scenario Testing")
            st.caption("Adjust assumptions to see how sensitive your retirement plan is. These are scenarios, not predictions.")
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                infl = st.slider("Inflation %", 3.0, 10.0, 6.0, 0.5) / 100
            with sc2:
                pre_ret = st.slider("Pre-retirement return %", 4.0, 16.0, 12.0, 0.5) / 100
            with sc3:
                post_ret = st.slider("Post-retirement return %", 3.0, 12.0, 8.0, 0.5) / 100

            scenario = calculate_retirement_needs(
                current_age=p['current_age'], retirement_age=p['retirement_age'],
                life_expectancy=p['life_expectancy'], current_monthly_expenses=p['essential_expenses'],
                inflation_rate=infl, pre_retirement_return=pre_ret, post_retirement_return=post_ret,
                current_retirement_corpus=p['existing_retirement_corpus'],
            )
            st.markdown(
                f"<p style='color:#94A3B8;'>Under these assumptions: required monthly SIP = "
                f"<span class='neon-text' style='font-size:1.1rem;'>{money(scenario['required_monthly_investment'])}</span>, "
                f"required corpus = {money(scenario['required_corpus'])}</p>",
                unsafe_allow_html=True,
            )

    # ---------- INVESTMENTS ----------
    with tabs[5]:
        if p['risk_tolerance'] == 'Aggressive' and risk_capacity in ('Low', 'Moderate'):
            st.markdown(
                "<div class='alert-banner'>⚠ Your psychological risk tolerance is Aggressive, but your objective "
                "risk capacity is currently " + risk_capacity + ". The recommended allocation below is bounded by "
                "what your finances can actually support.</div>", unsafe_allow_html=True,
            )
        ic1, ic2 = st.columns([1.3, 1])
        with ic1:
            alloc_for_chart = {k: v for k, v in allocation_mix.items() if k != "Strategy" and v > 0}
            st.plotly_chart(donut_chart(alloc_for_chart, center_text=allocation_mix['Strategy'].split(" ")[0]), width='stretch', config={"displayModeBar": False})
        with ic2:
            st.markdown(f"#### {allocation_mix['Strategy']}")
            for asset, pct in allocation_mix.items():
                if asset == "Strategy" or pct == 0:
                    continue
                st.markdown(
                    f"<div class='alloc-row'><span class='alloc-dot' style='background:{COLOR_MAP.get(asset,'#3B82F6')}'></span>"
                    f"<span class='alloc-label'>{asset}</span><span class='alloc-value'>{pct}%</span></div>",
                    unsafe_allow_html=True,
                )
        with st.expander("Why this allocation?"):
            st.caption(
                f"Time horizon to retirement: {years_to_retirement} years. Objective risk capacity ({risk_capacity}) "
                f"is evaluated from age, emergency-fund coverage, cash-flow surplus, dependents, and debt-to-income "
                f"ratio, and it caps how much psychological tolerance ({p['risk_tolerance']}) is allowed to drive the mix."
            )

    st.markdown("<br>", unsafe_allow_html=True)
    st.button("↺ Recalibrate Profile", on_click=reset)
