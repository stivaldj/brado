from __future__ import annotations

from app.political_interview.similarity import cosine_similarity


def test_cosine_similarity_is_one_for_identical_vectors():
    vector = {"ECO": 0.4, "SOC": -0.2, "EST": 0.0, "AMB": 0.3, "LIB": -0.1, "GOV": 0.5, "GLB": 0.2, "INS": 0.7}
    assert cosine_similarity(vector, vector) == 1.0
