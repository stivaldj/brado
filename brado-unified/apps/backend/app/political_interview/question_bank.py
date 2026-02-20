from __future__ import annotations

import random

from .constants import DIMENSIONS


_THEME_BY_DIM = {
    "ECO": "politica fiscal",
    "SOC": "direitos sociais",
    "EST": "seguranca publica",
    "AMB": "sustentabilidade",
    "LIB": "liberdades civis",
    "GOV": "governanca do Estado",
    "GLB": "integracao internacional",
    "INS": "instituicoes democraticas",
}


def build_seed_questions(total: int = 600) -> list[dict]:
    rng = random.Random(42)
    questions: list[dict] = []

    for idx in range(total):
        main_dim = DIMENSIONS[idx % len(DIMENSIONS)]
        secondary_dim = DIMENSIONS[(idx + 3) % len(DIMENSIONS)]

        main_weight = round(rng.uniform(0.6, 1.0), 2)
        secondary_weight = round(rng.uniform(-0.8, 0.8), 2)

        dimensions = {dim: 0.0 for dim in DIMENSIONS}
        dimensions[main_dim] = main_weight
        dimensions[secondary_dim] = secondary_weight

        q_id = f"{main_dim}_{idx + 1:03d}"
        prompt = (
            f"No tema de {_THEME_BY_DIM[main_dim]}, qual deve ser a prioridade do governo "
            f"considerando impactos em {_THEME_BY_DIM[secondary_dim]}?"
        )
        tags = [main_dim.lower(), secondary_dim.lower(), "politica-publica", "entrevista-adaptativa"]
        questions.append(
            {
                "id": q_id,
                "prompt": prompt,
                "response_type": "LIKERT_7",
                "dimensions_json": dimensions,
                "tags_json": tags,
                "active": 1,
            }
        )

    return questions


def pick_next_question(
    *,
    unanswered_questions: list[dict],
    partial_vector: dict[str, float],
) -> dict | None:
    if not unanswered_questions:
        return None

    weakest_dim = min(DIMENSIONS, key=lambda dim: abs(float(partial_vector.get(dim, 0.0))))
    dimension_filtered = [q for q in unanswered_questions if float(q["dimensions_json"].get(weakest_dim, 0.0)) != 0.0]
    candidates = dimension_filtered if dimension_filtered else unanswered_questions

    candidates.sort(key=lambda q: abs(float(q["dimensions_json"].get(weakest_dim, 0.0))), reverse=True)
    return candidates[0]
