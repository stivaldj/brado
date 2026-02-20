from __future__ import annotations

from app.political_interview.budget import simulate_budget


def test_budget_simulator_rejects_sum_different_from_100():
    result = simulate_budget(
        [
            {"category": "saude", "percent": 40},
            {"category": "educacao", "percent": 30},
            {"category": "seguranca", "percent": 20},
        ]
    )

    assert result["valid"] is False
    assert result["total_percent"] == 90
    assert result["tradeoffs"]


def test_budget_simulator_accepts_100_percent():
    result = simulate_budget(
        [
            {"category": "saude", "percent": 35},
            {"category": "educacao", "percent": 35},
            {"category": "seguranca", "percent": 30},
        ]
    )

    assert result["valid"] is True
    assert result["total_percent"] == 100
