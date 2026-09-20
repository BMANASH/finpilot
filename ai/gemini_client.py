# ai/gemini_client.py
"""
Thin wrapper around Gemini for the "Ask AI" tab.

Per the FINPILOT architecture (see README):
    FINANCIAL ENGINE  -->  STRUCTURED RESULTS  -->  GEMINI  -->  EXPLANATION

Gemini never invents numbers. It only explains, summarizes, and answers
questions using the structured profile/results it's given, general personal
finance thumb-rules, and (optionally) live Google Search grounding for
things like "what's the current repo rate" or "what does a 7% FD return
look like right now".
"""

import os
import streamlit as st
from google import genai
from google.genai import types

MODEL_NAME = "gemini-2.5-flash"

_SECRET_KEY_NAMES = ("GEMINI_API_KEY", "GOOGLE_API_KEY", "gemini_api_key", "google_api_key")

SYSTEM_PREAMBLE = """You are the FINPILOT AI Explainer, embedded inside a personal-finance
planning app for an Indian user. You are NOT the financial engine — a deterministic
Python engine already calculated every number you'll see below (allocation, health
score, risk capacity, retirement corpus, required SIPs, etc). Your job is to:

1. Explain those numbers in simple, plain language — no jargon dumps.
2. Answer the user's follow-up questions using ONLY the structured data provided below,
   general well-known personal-finance thumb rules (e.g. "6 months of expenses as an
   emergency fund", "term cover ~10-15x annual income", "50/30/20 as a rough starting
   point, adjusted to the person's real situation"), and, when useful and available,
   live web search for current facts (interest rates, inflation prints, index levels).
3. NEVER invent numbers, returns, or coverage figures that aren't in the structured
   data or clearly labeled as a general rule of thumb / search result.
4. NEVER present anything as guaranteed investment advice. You are an educational
   explainer, not a licensed financial adviser. You can say what most planners suggest,
   but flag scenarios/assumptions clearly.
5. Keep answers concise, warm, and easy to follow — assume the user is smart but not
   a finance professional.

Here is the user's current structured financial profile and computed results:
"""


def _get_api_key():
    for name in _SECRET_KEY_NAMES:
        try:
            if name in st.secrets:
                return st.secrets[name]
        except Exception:
            pass
    try:
        gemini_section = st.secrets.get("gemini", {})
        if isinstance(gemini_section, dict) and gemini_section.get("api_key"):
            return gemini_section["api_key"]
    except Exception:
        pass
    for name in _SECRET_KEY_NAMES:
        if os.environ.get(name):
            return os.environ[name]
    return None


def is_configured() -> bool:
    return bool(_get_api_key())


def build_system_context(profile: dict, results: dict) -> str:
    """Serialize the profile + engine results into a compact block for the system prompt."""
    lines = [SYSTEM_PREAMBLE, "\n## PROFILE"]
    lines.append(f"- Intent: {', '.join(profile.get('intent', [])) or 'Not specified'}")
    lines.append(f"- Monthly income: Rs {profile.get('income', 0):,.0f}")
    lines.append(f"- Essential monthly expenses: Rs {profile.get('essential_expenses', 0):,.0f}")
    lines.append(f"- Monthly EMI/debt: Rs {profile.get('debt_emi', 0):,.0f}")
    lines.append(f"- Dependents: {profile.get('dependents', 0)}")
    lines.append(f"- Emergency fund saved: Rs {profile.get('emergency_fund_current', 0):,.0f}")
    lines.append(f"- Health insurance: {profile.get('has_health_insurance', False)}")
    lines.append(f"- Term life insurance: {profile.get('has_term_insurance', False)}")
    lines.append(f"- Personal accident cover: {profile.get('has_accident_insurance', False)}")
    lines.append(f"- Current age: {profile.get('current_age')}, Retirement age: {profile.get('retirement_age')}, Life expectancy: {profile.get('life_expectancy')}")
    lines.append(f"- Risk tolerance (psychological): {profile.get('risk_tolerance')}")

    lines.append("\n## ENGINE RESULTS")
    if results.get("health"):
        h = results["health"]
        lines.append(f"- Financial Foundation Score: {h['score']}/{h['max_score']} ({h['rating']})")
        lines.append(f"  Strong points: {'; '.join(h['strong_points']) or 'none'}")
        lines.append(f"  Needs attention: {'; '.join(h['attention_needed']) or 'none'}")
    if results.get("risk_capacity"):
        lines.append(f"- Objective risk capacity: {results['risk_capacity']}")
    if results.get("allocation_mix"):
        lines.append(f"- Recommended asset allocation: {results['allocation_mix']}")
    if results.get("waterfall") and not results["waterfall"].get("warning"):
        lines.append(f"- Monthly money-plan (Rs): {results['waterfall'].get('amounts')}")
    elif results.get("waterfall", {}).get("warning"):
        lines.append(f"- Money-plan warning: {results['waterfall']['warning']}")
    if results.get("retirement") and "error" not in results["retirement"]:
        r = results["retirement"]
        lines.append(
            f"- Retirement: required corpus Rs {r['required_corpus']:,.0f}, "
            f"projected corpus Rs {r['projected_existing_corpus']:,.0f}, "
            f"shortfall Rs {r['corpus_shortfall']:,.0f}, "
            f"required monthly SIP Rs {r['required_monthly_investment']:,.0f}"
        )
    if results.get("priced_goals"):
        for g in results["priced_goals"]:
            lines.append(
                f"- Goal '{g['Goal']}' ({g['Category']}): target Rs {g['Target (₹)']:,.0f}, "
                f"saved Rs {g['Saved (₹)']:,.0f}, requires ~Rs {g['Required Monthly (₹)']:,.0f}/month"
            )
    if results.get("conflict") and results["conflict"].get("has_conflict"):
        c = results["conflict"]
        lines.append(f"- Goal conflict: needs Rs {c['total_required']:,.0f}/month but only Rs {c['available_surplus']:,.0f} available (shortfall Rs {c['monthly_shortfall']:,.0f})")

    return "\n".join(lines)


def ask(user_message: str, history: list, system_context: str, use_search: bool = True):
    """
    Send a message to Gemini.

    history: list of {"role": "user"|"model", "content": str}
    Returns (answer_text, error_message) — exactly one will be None.
    """
    api_key = _get_api_key()
    if not api_key:
        return None, (
            "No Gemini API key found. Add `GEMINI_API_KEY` under your Streamlit app's "
            "Settings → Secrets, then reload."
        )

    try:
        client = genai.Client(api_key=api_key)
        tools = [types.Tool(google_search=types.GoogleSearch())] if use_search else None

        contents = []
        for turn in history:
            contents.append(types.Content(
                role=turn["role"],
                parts=[types.Part.from_text(text=turn["content"])],
            ))
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_message)]))

        config = types.GenerateContentConfig(
            system_instruction=system_context,
            tools=tools,
            temperature=0.4,
        )

        response = client.models.generate_content(model=MODEL_NAME, contents=contents, config=config)
        text = getattr(response, "text", None)
        if not text:
            return None, "Gemini returned an empty response. Try rephrasing your question."
        return text, None

    except Exception as e:
        return None, f"AI request failed: {e}"
