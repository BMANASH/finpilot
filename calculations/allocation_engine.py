# calculations/allocation_engine.py

def calculate_dynamic_waterfall(profile: dict) -> dict:
    """
    Core Financial Engine: Processes cash flow through a strict priority waterfall.
    It does not use fixed percentages. It calculates allocations based on actual 
    liabilities, dependents, and safety gaps.
    """
    income = profile.get('income', 0)
    if income <= 0:
        return {"error": "Income must be greater than 0"}

    # Base Metrics
    essential_expenses = profile.get('essential_expenses', 0)
    debt_emi = profile.get('debt_emi', 0)
    dependents = profile.get('dependents', 0)
    current_emergency = profile.get('emergency_fund_current', 0)
    has_health_insurance = profile.get('has_health_insurance', False)

    # Calculate Base Surplus
    surplus = income - essential_expenses - debt_emi
    if surplus <= 0:
        return _generate_survival_mode_allocation(income, essential_expenses, debt_emi)

    allocation_plan = {
        "Essential Expenses": essential_expenses,
        "Debt Obligations": debt_emi,
        "Protection & Insurance": 0,
        "Emergency Reserve": 0,
        "Goal Funding": 0,
        "Retirement": 0,
        "Long-Term Wealth": 0,
        "Flexible Lifestyle": 0
    }

    # PRIORITY 1: Protection (Health & Term Life)
    # If no health insurance, allocate up to 5% of income to fund a premium
    if not has_health_insurance:
        health_premium_est = min(surplus, income * 0.05)
        allocation_plan["Protection & Insurance"] += health_premium_est
        surplus -= health_premium_est
    
    # If dependents exist, allocate up to 3% for Term Life Insurance
    if dependents > 0:
        term_premium_est = min(surplus, income * 0.03)
        allocation_plan["Protection & Insurance"] += term_premium_est
        surplus -= term_premium_est

    # PRIORITY 2: Emergency Liquidity
    # Target: 6 months of absolute essentials + debt
    emergency_target = (essential_expenses + debt_emi) * 6
    if current_emergency < emergency_target:
        # Aggressively fund emergency if gap is large, max 20% of income
        emergency_funding_capacity = min(surplus, income * 0.20)
        allocation_plan["Emergency Reserve"] = emergency_funding_capacity
        surplus -= emergency_funding_capacity

    # PRIORITY 3: Retirement Basics
    # Ensure at least 10% goes to retirement if surplus allows
    retirement_minimum = min(surplus, income * 0.10)
    allocation_plan["Retirement"] = retirement_minimum
    surplus -= retirement_minimum

    # PRIORITY 4: Goal Funding & Long-Term Wealth
    # Split remaining surplus between specific goals and general wealth building
    if surplus > 0:
        goal_allocation = surplus * 0.60
        wealth_allocation = surplus * 0.30
        lifestyle_allocation = surplus * 0.10
        
        allocation_plan["Goal Funding"] = goal_allocation
        allocation_plan["Long-Term Wealth"] = wealth_allocation
        allocation_plan["Flexible Lifestyle"] = lifestyle_allocation

    # Convert absolute raw numbers to percentages for the UI
    percentage_allocation = {
        category: round((amount / income) * 100, 2) 
        for category, amount in allocation_plan.items() 
        if amount > 0
    }

    return percentage_allocation

def _generate_survival_mode_allocation(income, expenses, debt):
    """Fallback engine if expenses + debt exceed or equal income."""
    return {
        "Essential Expenses": round((expenses / income) * 100, 2),
        "Debt Obligations": round((debt / income) * 100, 2),
        "Warning": "Cash flow negative or zero. Debt restructuring or income generation required."
    }
