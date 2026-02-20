from __future__ import annotations

import math
from dataclasses import dataclass

from .constants import DIMENSIONS, LIKERT_MAX, LIKERT_MIN


@dataclass(frozen=True)
class ScoringOutput:
    vector: dict[str, float]
    left_right_score: float
    confidence: float
    consistency: float


def _normalize_likert(answer: int) -> float:
    middle = (LIKERT_MAX + LIKERT_MIN) / 2
    radius = (LIKERT_MAX - LIKERT_MIN) / 2
    return max(-1.0, min(1.0, (answer - middle) / radius))


def score_interview(answer_records: list[dict]) -> ScoringOutput:
    totals = {dim: 0.0 for dim in DIMENSIONS}
    weights = {dim: 0.0 for dim in DIMENSIONS}

    if not answer_records:
        return ScoringOutput(totals, 0.0, 0.0, 0.0)

    weighted_signals: list[float] = []
    for record in answer_records:
        normalized = _normalize_likert(int(record["answer_value"]))
        dimensions = record["dimensions"]

        for dim in DIMENSIONS:
            weight = float(dimensions.get(dim, 0.0))
            totals[dim] += normalized * weight
            weights[dim] += abs(weight)
            if weight != 0:
                weighted_signals.append(normalized * weight)

    vector = {
        dim: round((totals[dim] / weights[dim]) if weights[dim] > 0 else 0.0, 4)
        for dim in DIMENSIONS
    }

    left_right_score = round((vector["ECO"] + vector["LIB"] + vector["GOV"]) / 3, 4)
    consistency = _estimate_consistency(weighted_signals)
    confidence = _estimate_confidence(answer_count=len(answer_records), consistency=consistency)

    return ScoringOutput(vector=vector, left_right_score=left_right_score, confidence=confidence, consistency=consistency)


def _estimate_consistency(weighted_signals: list[float]) -> float:
    if len(weighted_signals) < 2:
        return 0.4
    mean = sum(weighted_signals) / len(weighted_signals)
    variance = sum((value - mean) ** 2 for value in weighted_signals) / len(weighted_signals)
    stddev = math.sqrt(variance)
    consistency = max(0.0, min(1.0, 1.0 - stddev))
    return round(consistency, 4)


def _estimate_confidence(answer_count: int, consistency: float) -> float:
    quantity_factor = max(0.0, min(1.0, answer_count / 40))
    confidence = 0.55 * quantity_factor + 0.45 * consistency
    return round(max(0.0, min(1.0, confidence)), 4)
