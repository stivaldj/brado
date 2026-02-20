from __future__ import annotations


def simulate_budget(allocations: list[dict]) -> dict:
    total = round(sum(float(item["percent"]) for item in allocations), 2)
    valid = total == 100.0

    tradeoffs = []
    sorted_allocations = sorted(allocations, key=lambda item: float(item["percent"]), reverse=True)

    if sorted_allocations:
        highest = sorted_allocations[0]
        lowest = sorted_allocations[-1]
        tradeoffs.append(
            f"Maior prioridade em {highest['category']} ({highest['percent']}%) reduz margem para {lowest['category']} ({lowest['percent']}%)."
        )

    if not valid:
        delta = round(100.0 - total, 2)
        if delta > 0:
            tradeoffs.append(f"Ainda faltam {delta}% para completar 100% do orçamento.")
        else:
            tradeoffs.append(f"Excesso de {-delta}% acima do limite de 100%.")

    return {"valid": valid, "total_percent": total, "tradeoffs": tradeoffs}
