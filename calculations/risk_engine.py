# calculations/risk_engine.py

def assess_risk_capacity(profile: dict) -> str:
    """
    Determines objective risk capacity (financial ability to take risk),
    evaluating time horizon, liquidity, cash flow, and fixed obligations.
    """
    income = profile.get('income', 0)
    essential = profile.get('essential_expenses', 0)
    debt_emi = profile.get('debt_emi', 0)
    current_ef = profile.get('emergency_fund_current', 0)
    dependents = profile.get('dependents', 0)
    age = profile.get('current_age', 25)

    if income <= 0:
        return "Low"

    surplus = income - essential - debt_emi
    surplus_ratio = surplus / income
    months_ef = current_ef / essential if essential > 0 else 0
    dti = debt_emi / income

    score = 0
    
    # 1. Time Horizon (Age proxy for general wealth capacity)
    if age < 35: score += 3
    elif age < 50: score += 2
    else: score += 1

    # 2. Liquidity Buffer (Emergency Fund)
    if months_ef >= 6: score += 3
    elif months_ef >= 3: score += 2
    else: score += 0

    # 3. Cash Flow (Surplus generation)
    if surplus_ratio >= 0.30: score += 3
    elif surplus_ratio >= 0.15: score += 2
    else: score += 1

    # 4. Fixed Obligations (Dependents & Debt)
    if dependents == 0 and dti < 0.20: score += 3
    elif dependents <= 2 and dti < 0.40: score += 2
    else: score += 1

    # Classify Capacity
    if score >= 10:
        return "High"
    elif score >= 7:
        return "Moderate"
    else:
        return "Low"


def determine_asset_allocation(risk_capacity: str, risk_tolerance: str, time_horizon: int = 10) -> dict:
    """
    Determines asset allocation by bounding psychological tolerance 
    with objective risk capacity and time horizon.
    """
    # Absolute Rule: Short horizons demand liquidity regardless of capacity/tolerance
    if time_horizon <= 3:
        return {
            "Strategy": "Capital Preservation (Short Term Goal)",
            "Equity": 0,
            "Debt": 60,
            "Liquid/Cash": 40,
            "Gold": 0
        }
    
    # Capacity vs Tolerance Matrix
    # The math bounds the psychology. You cannot be aggressive if you have low financial capacity.
    final_profile = "Moderate"
    
    if risk_capacity == "Low":
        final_profile = "Conservative" # Overrides aggressive tolerance
    elif risk_capacity == "Moderate":
        if risk_tolerance == "Conservative":
            final_profile = "Conservative"
        else:
            final_profile = "Moderate" # Overrides aggressive tolerance
    elif risk_capacity == "High":
        final_profile = risk_tolerance # Capacity is high enough to allow any psychological preference

    # Generate Allocation Percentages
    if final_profile == "Conservative":
        return {
            "Strategy": "Income & Capital Protection",
            "Equity": 20,
            "Debt": 60,
            "Liquid/Cash": 10,
            "Gold": 10
        }
    elif final_profile == "Moderate":
        return {
            "Strategy": "Balanced Growth",
            "Equity": 50,
            "Debt": 35,
            "Liquid/Cash": 5,
            "Gold": 10
        }
    else: # Aggressive
        return {
            "Strategy": "Aggressive Wealth Creation",
            "Equity": 75,
            "Debt": 15,
            "Liquid/Cash": 5,
            "Gold": 5
        }
