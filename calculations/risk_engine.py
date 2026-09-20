# calculations/risk_engine.py

def assess_risk_capacity(profile: dict) -> str:
    """
    Evaluates objective financial capacity to absorb losses.
    Based on emergency reserves, debt load, dependents, and surplus stability.
    Returns: 'Low', 'Moderate', or 'High'
    """
    income = profile.get('income', 0)
    expenses = profile.get('essential_expenses', 0)
    debt = profile.get('debt_emi', 0)
    dependents = profile.get('dependents', 0)
    emergency = profile.get('emergency_fund_current', 0)
    
    capacity_score = 0
    
    # 1. Emergency reserve runway
    monthly_burn = expenses + debt
    if monthly_burn > 0:
        runway_months = emergency / monthly_burn
        if runway_months >= 6:
            capacity_score += 3
        elif runway_months >= 3:
            capacity_score += 2
        else:
            capacity_score += 1
            
    # 2. Dependency burden
    if dependents == 0:
        capacity_score += 3
    elif dependents <= 2:
        capacity_score += 2
    else:
        capacity_score += 1

    # 3. Debt-to-income ratio
    if income > 0:
        dti = debt / income
        if dti == 0:
            capacity_score += 3
        elif dti <= 0.30:
            capacity_score += 2
        else:
            capacity_score += 1

    if capacity_score >= 8:
        return "High"
    elif capacity_score >= 5:
        return "Moderate"
    else:
        return "Low"

def determine_asset_allocation(risk_capacity: str, risk_tolerance: str, goal_years: float) -> dict:
    """
    Determines asset allocation across Equity, Debt, and Gold.
    Enforces the rule: Practical allocation is bounded by Risk Capacity,
    not solely by psychological Risk Tolerance, and respects goal horizon.
    """
    # 1. Horizon overrides: Short-term money cannot take high volatility
    if goal_years <= 3:
        return {
            "Equity": 0.0,
            "Debt / Liquid": 90.0,
            "Gold": 10.0,
            "Strategy": "Capital Preservation (Near-term horizon)"
        }
    elif goal_years <= 7:
        return {
            "Equity": 40.0,
            "Debt / Fixed Income": 50.0,
            "Gold": 10.0,
            "Strategy": "Balanced Hybrid (Medium-term horizon)"
        }

    # 2. Long-term horizon (7+ years): Bound tolerance by capacity
    # If tolerance is high but capacity is low, cap equity exposure
    if risk_capacity == "Low":
        return {
            "Equity": 30.0,
            "Debt / Fixed Income": 60.0,
            "Gold": 10.0,
            "Strategy": "Conservative Growth (Constrained by low capacity)"
        }
    elif risk_capacity == "Moderate":
        if risk_tolerance.lower() == "aggressive":
            equity = 60.0
        elif risk_tolerance.lower() == "conservative":
            equity = 40.0
        else:
            equity = 50.0
            
        return {
            "Equity": equity,
            "Debt / Fixed Income": round(90.0 - equity, 2),
            "Gold": 10.0,
            "Strategy": "Balanced Growth"
        }
    else:  # High Capacity
        if risk_tolerance.lower() == "aggressive":
            equity = 75.0
            gold = 10.0
        elif risk_tolerance.lower() == "conservative":
            equity = 45.0
            gold = 10.0
        else:
            equity = 60.0
            gold = 15.0

        return {
            "Equity": equity,
            "Debt / Fixed Income": round(100.0 - equity - gold, 2),
            "Gold": gold,
            "Strategy": "Aggressive Long-Term Compounding"
        }
