from __future__ import annotations

import pytest

pytest.importorskip("sqlalchemy")

from app.jobs.profile_jobs import _normalize_vote, _vector_from_signal


def test_normalize_vote_maps_expected_values():
    assert _normalize_vote("SIM") == 1.0
    assert _normalize_vote("NAO") == -1.0
    assert _normalize_vote("ABSTENCAO") == 0.0
    assert _normalize_vote("OBSTRUCAO") == -0.2


def test_vector_from_signal_returns_8d():
    vector = _vector_from_signal(0.5)
    assert set(vector.keys()) == {"ECO", "SOC", "EST", "AMB", "LIB", "GOV", "GLB", "INS"}
    assert vector["ECO"] == 0.5
