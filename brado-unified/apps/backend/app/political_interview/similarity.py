from __future__ import annotations

import math

from .constants import DIMENSIONS


def cosine_similarity(a: dict[str, float], b: dict[str, float]) -> float:
    vector_a = [float(a.get(dim, 0.0)) for dim in DIMENSIONS]
    vector_b = [float(b.get(dim, 0.0)) for dim in DIMENSIONS]

    dot = sum(x * y for x, y in zip(vector_a, vector_b))
    norm_a = math.sqrt(sum(x * x for x in vector_a))
    norm_b = math.sqrt(sum(y * y for y in vector_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return round(dot / (norm_a * norm_b), 4)


def explain_similarity(user_vector: dict[str, float], entity_vector: dict[str, float]) -> str:
    deltas = []
    for dim in DIMENSIONS:
        deltas.append((dim, abs(float(user_vector.get(dim, 0.0)) - float(entity_vector.get(dim, 0.0)))))
    deltas.sort(key=lambda item: item[1])
    closest = [dim for dim, _ in deltas[:2]]
    return f"Maior proximidade nas dimensoes {closest[0]} e {closest[1]}"
