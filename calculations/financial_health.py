# calculations/financial_health.py

def calculate_health_score(profile: dict) -> dict:
    """
    Calculates a transparent Financial Foundation Score (0-100).
    Evaluates cash flow, emergency reserves, protection, and debt.
    """
    score = 0
    max_score = 100
    
    strong = []
    needs_attention = []
    not_applicable = []

    # 1. Cash Flow (Max 25 points)
    income = profile.get('income', 0)
    expenses = profile.get('essential_expenses', 0)
    debt = profile.get('debt_emi', 0)
    
    if income > 0:
        surplus_ratio = (income - expenses - debt) / income
        if surplus_ratio >= 0.20:
            score += 25
            strong.append("Healthy monthly cash flow surplus (>= 20%)")
        elif surplus_ratio > 0:
            score += 15
            needs_attention.append("Positive cash flow, but surplus is tight (< 20%)")
        else:
            needs_attention.append("Negative or zero cash flow. High risk.")
    
    # 2. Emergency Fund (Max 25 points)
    current_emergency = profile.get('emergency_fund_current', 0)
    target_emergency = (expenses + debt) * 6
    
    if target_emergency > 0:
        emergency_ratio = current_emergency / target_emergency
        if emergency_ratio >= 1.0:
            score += 25
            strong.append("Emergency fund fully funded (6+ months)")
        elif emergency_ratio >= 0.5:
            score += 15
            needs_attention.append("Emergency fund partially funded (needs completion)")
        else:
            needs_attention.append("Critically low emergency reserves")

    # 3. Health Insurance (Max 25 points)
    if profile.get('has_health_insurance', False):
        score += 25
        strong.append("Health insurance coverage active")
    else:
        needs_attention.append("Missing health insurance coverage")

    # 4. Debt Burden (Max 25 points)
    if income > 0:
        debt_to_income = debt / income
        if debt_to_income == 0:
            score += 25
            strong.append("No monthly debt obligations")
        elif debt_to_income <= 0.30:
            score += 15
            strong.append("Manageable debt-to-income ratio (<= 30%)")
        else:
            needs_attention.append("High debt-to-income ratio (> 30%)")

    return {
        "score": score,
        "max_score": max_score,
        "strong_points": strong,
        "attention_needed": needs_attention,
        "not_applicable": not_applicable
    }
