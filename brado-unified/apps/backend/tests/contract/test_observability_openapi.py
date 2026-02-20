from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

pytest.importorskip("sqlalchemy")

from app.main import create_app


def test_observability_paths_exist_in_openapi():
    client = TestClient(create_app())
    spec = client.get('/openapi.json').json()

    paths = spec['paths']
    assert '/metrics' in paths
    assert '/ready' in paths
