from __future__ import annotations

from app.political_interview.question_bank import build_seed_questions


def test_seed_question_bank_builds_600_items_with_dimensions():
    questions = build_seed_questions(600)

    assert len(questions) == 600
    assert questions[0]["id"]
    assert set(questions[0]["dimensions_json"].keys()) == {"ECO", "SOC", "EST", "AMB", "LIB", "GOV", "GLB", "INS"}
