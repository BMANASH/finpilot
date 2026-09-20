# calculations/allocation_engine.py

def calculate_dynamic_waterfall(profile: dict) -> dict:
    """
    Calculates a personalized cash-flow waterfall based on the user's financial profile.
    This replaces rigid rules like 50/30/20 with dynamic, needs-based allocation.

    Returns a dict shaped as:
    {
        "warning": str | None,
        "amounts": {category: rupee_amount, ...},
        "percentages": {category: percent_of_income, ...},
    }
    """
    income = profile.get('income', 0)
    essential = profile.get('essential_expenses', 0)
    debt_emi = profile.get('debt_emi', 0)

    empty = {"warning": None, "amounts": {}, "percentages": {}}

    # Forced Input Validation: If income is 0 or less than essential + debt, flag an error
    if income <= 0:
        empty["warning"] = "Income must be greater than zero to calculate allocation."
        return empty
    if (essential + debt_emi) >= income:
        empty["warning"] = "Your committed expenses and debt exceed or equal your income. Immediate cash-flow restructuring required."
        return empty

    surplus = income - essential - debt_emi
    
    # Initialize allocation buckets (in currency amounts, not percentages yet)
    allocation_amounts = {
        'Essential Living': essential,
        'Debt Repayment': debt_emi,
        'Protection (Insurance)': 0,
        'Emergency Fund': 0,
        'Retirement': 0,
        'Goal Funding & Wealth': 0,
        'Flexible/Lifestyle': 0
    }

    # Step 1: Protection (Term & Health)
    # If they have dependents or no health insurance, allocate a portion of surplus to protection
    protection_needs = 0
    if not profile.get('has_health_insurance', False):
        protection_needs += (income * 0.05) # Estimate 5% for baseline health cover
    if profile.get('dependents', 0) > 0:
        protection_needs += (income * 0.03) # Estimate 3% for term life cover
    
    # Cap protection at 15% of surplus to avoid draining all cash flow
    actual_protection = min(protection_needs, surplus * 0.15)
    allocation_amounts['Protection (Insurance)'] = actual_protection
    surplus -= actual_protection

    # Step 2: Emergency Fund
    # Target: 6 months of essential expenses
    target_ef = essential * 6
    current_ef = profile.get('emergency_fund_current', 0)
    
    if current_ef < target_ef:
        # If underfunded, aggressively allocate up to 30% of remaining surplus
        ef_allocation = min(target_ef - current_ef, surplus * 0.30)
        allocation_amounts['Emergency Fund'] = ef_allocation
        surplus -= ef_allocation

    # Step 3: Retirement
    # Baseline 10% of income if surplus allows, otherwise a smaller percentage
    retirement_target = income * 0.10
    actual_retirement = min(retirement_target, surplus * 0.40)
    allocation_amounts['Retirement'] = actual_retirement
    surplus -= actual_retirement

    # Step 4: Wealth & Goals vs. Lifestyle
    # Split the remaining surplus between long-term goals and flexible lifestyle spending
    if surplus > 0:
        allocation_amounts['Goal Funding & Wealth'] = surplus * 0.70
        allocation_amounts['Flexible/Lifestyle'] = surplus * 0.30

    # Convert amounts to percentages for the dashboard UI
    allocation_percentages = {}
    for category, amount in allocation_amounts.items():
        if amount > 0:
            percentage = round((amount / income) * 100, 1)
            allocation_percentages[category] = percentage

    return {
        "warning": None,
        "amounts": {k: round(v, 2) for k, v in allocation_amounts.items() if v > 0},
        "percentages": allocation_percentages,
        "goal_and_wealth_amount": round(allocation_amounts['Goal Funding & Wealth'], 2),
    }
