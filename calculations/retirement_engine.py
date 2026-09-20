# calculations/retirement_engine.py

def calculate_retirement_needs(
    current_age: int,
    retirement_age: int,
    life_expectancy: int,
    current_monthly_expenses: float,
    inflation_rate: float = 0.06,
    pre_retirement_return: float = 0.12,
    post_retirement_return: float = 0.08,
    current_retirement_corpus: float = 0.0
) -> dict:
    """
    Calculates the required retirement corpus and the monthly investment needed
    to achieve it, factoring in inflation and expected returns.
    """
    years_to_retirement = retirement_age - current_age
    years_in_retirement = life_expectancy - retirement_age

    if years_to_retirement <= 0 or years_in_retirement <= 0:
        return {"error": "Invalid age parameters. Check current, retirement, and life expectancy ages."}

    # 1. Calculate future monthly expenses at retirement (adjusting for inflation)
    future_monthly_expenses = current_monthly_expenses * ((1 + inflation_rate) ** years_to_retirement)
    future_annual_expenses = future_monthly_expenses * 12

    # 2. Calculate required retirement corpus 
    # Using Present Value of an annuity formula for the retirement phase
    # Real rate of return during retirement (inflation adjusted)
    real_return_rate = ((1 + post_retirement_return) / (1 + inflation_rate)) - 1
    
    if real_return_rate <= 0:
        required_corpus = future_annual_expenses * years_in_retirement
    else:
        required_corpus = future_annual_expenses * (1 - (1 + real_return_rate) ** -years_in_retirement) / real_return_rate

    # 3. Future Value of current retirement savings
    fv_current_corpus = current_retirement_corpus * ((1 + pre_retirement_return) ** years_to_retirement)
    
    # 4. Shortfall to be funded via monthly investments (SIP)
    corpus_shortfall = max(required_corpus - fv_current_corpus, 0)
    
    # 5. Required Monthly Investment (PMT)
    months_to_retirement = years_to_retirement * 12
    monthly_return_rate = pre_retirement_return / 12
    
    if monthly_return_rate == 0:
        required_monthly_investment = corpus_shortfall / months_to_retirement
    else:
        required_monthly_investment = (corpus_shortfall * monthly_return_rate) / (((1 + monthly_return_rate) ** months_to_retirement) - 1)

    return {
        "years_to_retirement": years_to_retirement,
        "years_in_retirement": years_in_retirement,
        "future_monthly_expenses": round(future_monthly_expenses, 2),
        "required_corpus": round(required_corpus, 2),
        "projected_existing_corpus": round(fv_current_corpus, 2),
        "corpus_shortfall": round(corpus_shortfall, 2),
        "required_monthly_investment": round(required_monthly_investment, 2)
    }
