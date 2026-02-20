import json
from pathlib import Path

from app.core.config import get_settings
from app.ingest.camara.client import CamaraClient


class FakeCamaraClient(CamaraClient):
    def __init__(self):
        pass

    def get(self, endpoint, params=None):
        if endpoint == "/deputados":
            return 200, {"dados": [{"id": 1, "nome": "A"}], "links": []}
        if endpoint == "/proposicoes":
            return 200, {"dados": [{"id": 1, "ano": 2020}], "links": []}
        if endpoint == "/votacoes":
            return 200, {"dados": [{"id": 10}], "links": []}
        return 200, {"dados": [], "links": []}


def test_contract_minimum_shapes() -> None:
    client = FakeCamaraClient()
    for endpoint in ["/deputados", "/proposicoes", "/votacoes"]:
        status, body = client.get(endpoint)
        assert status == 200
        assert isinstance(body, dict)
        assert "dados" in body
        assert isinstance(body["dados"], list)


def test_vcr_replay_mode(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VCR_MODE", "replay")
    monkeypatch.setenv("VCR_DIR", str(tmp_path))
    get_settings.cache_clear()

    probe = CamaraClient()
    url = f"{probe.base_url}/deputados"
    key = probe._vcr._key("GET", url, {"itens": 1})  # noqa: SLF001 - internal key is deterministic contract
    probe.close()

    (tmp_path / f"{key}.json").write_text(
        json.dumps({"status": 200, "body": {"dados": [{"id": 10}], "links": []}}),
        encoding="utf-8",
    )

    client = CamaraClient()
    try:
        status, body = client.get("/deputados", {"itens": 1})
        assert status == 200
        assert body["dados"][0]["id"] == 10
    finally:
        client.close()
        get_settings.cache_clear()
