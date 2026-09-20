# calculations/goals_engine.py

def categorize_goal(target_years: float) -> str:
    """Classifies a goal based on its time horizon."""
    if target_years <= 3:
        return "Short Term"
    elif target_years <= 7:
        return "Medium Term"
    else:
        return "Long Term"

def calculate_required_pmt(target_amount: float, current_amount: float, years: float, expected_annual_return: float) -> float:
    """
    Calculates the required monthly contribution (PMT) to reach a target amount.
    Applies standard Time Value of Money (TVM) formulas.
    """
    if years <= 0:
        return max(target_amount - current_amount, 0)
    
    months = int(years * 12)
    monthly_rate = expected_annual_return / 12
    
    if monthly_rate == 0:
        return max((target_amount - current_amount) / months, 0)
        
    # Future Value of current savings
    fv_current = current_amount * ((1 + monthly_rate) ** months)
    shortfall = target_amount - fv_current
    
    if shortfall <= 0:
        return 0
        
    # PMT formula for future value
    pmt = (shortfall * monthly_rate) / (((1 + monthly_rate) ** months) - 1)
    return round(pmt, 2)

def evaluate_goal_conflict(goals: list, available_surplus: float) -> dict:
    """
    Evaluates if the user's total required goal contributions exceed their monthly surplus.
    Flags conflicts requiring prioritization.
    """
    total_required_monthly = sum(goal.get('required_monthly', 0) for goal in goals)
    
    has_conflict = total_required_monthly > available_surplus
    
    return {
        "total_required": total_required_monthly,
        "available_surplus": available_surplus,
        "has_conflict": has_conflict,
        "monthly_shortfall": total_required_monthly - available_surplus if has_conflict else 0
    }
