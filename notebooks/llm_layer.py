from groq import Groq


def explain_results(
    pattern_results: dict,
    outputs: dict,
    years: list,
    language: str = 'en',
    model: str = 'llama-3.3-70b-versatile',
) -> str:

    lines = []
    for sheet, labels in pattern_results.items():
        out    = outputs.get(sheet, {})
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
            f"peak_debt={peak_debt} M$, "
            f"min_cash={min_cash} M$, "
            f"avg_ACoSt={avg_acost} M$/yr"
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
for Rwanda's CleanStep scenario (2023-2034, values in M$):

{financial_summary}

Pattern label definitions:
- subsidy_dependent: technology requires significant long-term subsidies to be viable
- fragile_structure: capital structure has high leverage or peak debt
- high_circularity: financial model required many solver iterations to converge

{instruction}
Give a concise 3-4 sentence interpretation of what these results mean for the
financing plan, highlighting the main risks and practical implications.
"""

    client = Groq()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512,
    )

    return response.choices[0].message.content