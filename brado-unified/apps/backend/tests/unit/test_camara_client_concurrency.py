from __future__ import annotations

import time

import httpx

from app.ingest.camara.client import CamaraClient


def test_fetch_many_preserves_request_order(monkeypatch):
    client = CamaraClient()
    client.max_concurrency = 8

    def fake_get(endpoint, params=None, *, raise_for_status=True):
        idx = int(endpoint.rsplit("/", 1)[-1])
        time.sleep((20 - idx) * 0.0001)
        return 200, {"id": idx}

    monkeypatch.setattr(client, "get", fake_get)

    requests = [(f"/resource/{i}", None) for i in range(20)]
    result = client.fetch_many(requests, max_workers=8)

    assert [item[1]["id"] for item in result] == list(range(20))
    client.close()


def test_get_retries_on_throttling_429(monkeypatch):
    client = CamaraClient()
    calls = {"n": 0}

    monkeypatch.setattr(client, "_throttle", lambda: None)
    monkeypatch.setattr("app.ingest.camara.client.time.sleep", lambda _s: None)

    def fake_http_get(url, params=None):
        calls["n"] += 1
        request = httpx.Request("GET", url, params=params)
        if calls["n"] < 3:
            return httpx.Response(429, request=request, json={"detail": "throttled"})
        return httpx.Response(200, request=request, json={"dados": [{"id": 1}]})

    monkeypatch.setattr(client.client, "get", fake_http_get)

    status, body = client.get("/deputados", {"itens": 1})

    assert status == 200
    assert body["dados"][0]["id"] == 1
    assert calls["n"] == 3
    client.close()
