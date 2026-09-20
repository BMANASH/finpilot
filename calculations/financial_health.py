# calculations/financial_health.py

def calculate_health_score(profile: dict) -> dict:
    """
    Evaluates the user's financial foundation across four core pillars:
    1. Cash Flow & Savings Capacity (30 points)
    2. Emergency Liquidity (25 points)
    3. Debt Burden (25 points)
    4. Insurance & Protection (20 points)
    
    Returns a deterministic score out of 100 with itemized diagnostic feedback.
    """
    income = profile.get('income', 0)
    essential = profile.get('essential_expenses', 0)
    debt_emi = profile.get('debt_emi', 0)
    current_ef = profile.get('emergency_fund_current', 0)
    has_health_insurance = profile.get('has_health_insurance', False)
    dependents = profile.get('dependents', 0)
    
    if income <= 0:
        return {
            "score": 0,
            "max_score": 100,
            "rating": "Unrated",
            "strong_points": [],
            "attention_needed": ["Monthly income must be entered to generate a foundation score."]
        }

    score = 0
    strong_points = []
    attention_needed = []

    # -------------------------------------------------------------
    # 1. Cash Flow & Savings Capacity (Max 30 Points)
    # -------------------------------------------------------------
    surplus = income - essential - debt_emi
    surplus_ratio = surplus / income

    if surplus_ratio >= 0.30:
        score += 30
        strong_points.append(f"Strong surplus buffer: saving {round(surplus_ratio * 100)}% of monthly income.")
    elif surplus_ratio >= 0.15:
        score += 20
        strong_points.append(f"Healthy positive cash flow: saving {round(surplus_ratio * 100)}% of income.")
    elif surplus_ratio > 0:
        score += 10
        attention_needed.append("Thin cash-flow margin (under 15% surplus). Minor shocks could strain finances.")
    else:
        score += 0
        attention_needed.append("Negative cash flow: committed expenses exceed income.")

    # -------------------------------------------------------------
    # 2. Emergency Liquidity Reserve (Max 25 Points)
    # Target: 6 months of essential living expenses
    # -------------------------------------------------------------
    target_ef = essential * 6 if essential > 0 else income * 3
    months_covered = current_ef / essential if essential > 0 else 0

    if months_covered >= 6:
        score += 25
        strong_points.append(f"Emergency liquidity fully funded ({round(months_covered, 1)} months of essentials).")
    elif months_covered >= 3:
        score += 15
        attention_needed.append(f"Emergency reserve partially funded ({round(months_covered, 1)} months). Target is 6 months.")
    elif months_covered > 0:
        score += 8
        attention_needed.append(f"Vulnerable liquidity: only {round(months_covered, 1)} months of runway saved.")
    else:
        score += 0
        attention_needed.append("No emergency fund reported. High vulnerability to unexpected expenses.")

    # -------------------------------------------------------------
    # 3. Debt Burden / DTI (Max 25 Points)
    # Debt-to-Income ratio: EMI / Gross Monthly Income
    # -------------------------------------------------------------
    dti = debt_emi / income

    if dti == 0:
        score += 25
        strong_points.append("Zero debt burden: 100% of non-essential surplus is available for goals.")
    elif dti <= 0.20:
        score += 20
        strong_points.append(f"Conservative debt level: EMIs consume {round(dti * 100)}% of income (well under 30%).")
    elif dti <= 0.40:
        score += 10
        attention_needed.append(f"Moderate debt load: EMIs consume {round(dti * 100)}% of income. Limit new borrowing.")
    else:
        score += 0
        attention_needed.append(f"Heavy debt stress: EMIs take {round(dti * 100)}% of income. Prioritize debt restructuring.")

    # -------------------------------------------------------------
    # 4. Protection & Insurance (Max 20 Points)
    # -------------------------------------------------------------
    # Health Insurance (10 pts)
    if has_health_insurance:
        score += 10
        strong_points.append("Active health insurance safeguards savings from medical emergencies.")
    else:
        attention_needed.append("Missing health insurance: a medical emergency could wipe out current investments.")

    # Term / Dependency Protection (10 pts)
    if dependents == 0:
        score += 10
        strong_points.append("No income dependents; term life protection is currently not required.")
    else:
        # User has dependents: needs life protection coverage
        # (Assuming baseline review needed if not explicitly validated)
        score += 5
        attention_needed.append(f"{dependents} income dependent(s) recorded: review term life coverage.")

    # Final qualitative rating
    if score >= 80:
        rating = "Institutional Grade"
    elif score >= 60:
        rating = "Stable Foundation"
    elif score >= 40:
        rating = "Moderate Vulnerability"
    else:
        rating = "High Financial Fragility"

    return {
        "score": score,
        "max_score": 100,
        "rating": rating,
        "strong_points": strong_points,
        "attention_needed": attention_needed
    }
