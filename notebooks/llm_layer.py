from groq import Groq


def explain_results(
    pattern_results: dict,
    outputs: dict,
    rl_results: dict,
    years: list,
    country: str = 'Mozambique',
    language: str = 'en',
    model: str = 'openai/gpt-oss-120b',
) -> str:

    lines = []
    for sheet, labels in pattern_results.items():
        out    = outputs.get(sheet, {})
        cs     = rl_results.get(sheet) or {}
        lts    = out.get('Long term subsidies', [])
        debt   = out.get('DEBT:EoP',            [])
        cash   = out.get('Cash EoP',            [])
        acost  = out.get('Annual Cost of Service', [])

        total_lts  = round(sum(lts), 1)
        peak_debt  = round(max(debt) if debt else 0, 1)
        min_cash   = round(min(cash) if cash else 0, 1)
        avg_acost  = round(sum(acost) / len(acost) if acost else 0, 1)
        flags      = [k for k, v in labels.items() if v > 0.5]

        lines.append(
            f"- {sheet}: flags={flags}, "
            f"total_LTS={total_lts} M$, "
            f"peak_debt_actually_raised_M$={peak_debt}, "
            f"min_cash={min_cash} M$, "
            f"avg_ACoSt={avg_acost} M$/yr, "
            f"financing_mix_target=(equity_share={cs.get('PCT_EQUITY','?')}%, "
            f"grants_share={cs.get('PCT_GRANTS','?')}%, "
            f"debt_share_of_financing_mix={cs.get('PCT_DEBT','?')}%, "
            f"cost_of_debt={cs.get('COST_OF_DEBT','?')}%, "
            f"cost_of_equity={cs.get('COST_OF_EQUITY','?')}%, "
            f"grace_period={cs.get('GRACE_PERIOD','?')}y, "
            f"amortization={cs.get('AMORTIZATION','?')}y)"
        )

    financial_summary = "\n".join(lines)

    if language == 'es':
        instruction = "Responde en español."
        persona = (
            "Eres un asesor financiero experto en proyectos de acceso a energía "
            "limpia en países en desarrollo."
        )
    else:
        instruction = "Respond in English."
        persona = (
            "You are a financial advisor specialising in clean energy access "
            "projects in developing countries."
        )

    prompt = f"""{persona}

The capital structure optimisation pipeline has produced the following results
for {country}'s CleanStep scenario ({years[0]}-{years[-1]}, values in M$):

{financial_summary}

Field definitions (read carefully, these two are easy to confuse):
- "debt_share_of_financing_mix" is a TARGET percentage the optimiser searched
  over (part of the financing plan going in), NOT the amount of debt the
  project actually ended up needing.
- "peak_debt_actually_raised_M$" is the OUTPUT: the largest amount of debt
  the model actually had to draw in any single year. If this is 0, the
  project raised no debt at all in practice, regardless of what
  debt_share_of_financing_mix says -- do not describe a project as
  "relying on debt" or "debt-heavy" if peak_debt_actually_raised_M$ is 0.

Pattern label definitions:
- subsidy_dependent: technology requires significant long-term subsidies to be viable
- fragile_structure: capital structure has high leverage or peak debt
- high_circularity: financial model required many solver iterations to converge

{instruction}
Give a concise 3-4 sentence interpretation of what these results mean for the
financing plan. Explicitly connect the main risks to the capital structure
that produced them (e.g. is the grants share doing most of the work, is debt
concentrated in a way that creates a liquidity risk in specific years, is the
cost of equity or debt driving the outcome), and note any practical
implication for negotiating the financing terms.

IMPORTANT: only use the exact figures given above. Do not introduce, round
to a different unit, combine, or estimate any numeric value that is not
explicitly present in the data above -- if a figure isn't given, describe
the situation qualitatively instead of inventing a number.
"""

    client = Groq()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
    )

    choice = response.choices[0]
    text = choice.message.content
    if choice.finish_reason == "length":
        text += "\n\n[⚠ response truncated due to token limit]"

    return text