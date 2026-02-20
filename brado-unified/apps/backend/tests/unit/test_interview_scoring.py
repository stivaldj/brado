from __future__ import annotations

from app.political_interview.scoring import score_interview


def test_score_interview_returns_8d_vector_and_confidence_bounds():
    answers = [
        {"question_id": "ECO_001", "answer_value": 7, "dimensions": {"ECO": 1.0, "LIB": 0.2}},
        {"question_id": "SOC_001", "answer_value": 2, "dimensions": {"SOC": 0.9, "INS": 0.3}},
        {"question_id": "GOV_001", "answer_value": 6, "dimensions": {"GOV": 0.8, "ECO": 0.4}},
    ]

    result = score_interview(answers)
    assert set(result.vector.keys()) == {"ECO", "SOC", "EST", "AMB", "LIB", "GOV", "GLB", "INS"}
    assert -1 <= result.left_right_score <= 1
    assert 0 <= result.confidence <= 1
    assert 0 <= result.consistency <= 1
