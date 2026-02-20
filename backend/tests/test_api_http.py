import pytest
import httpx

from backend.main import app
from backend.database import db_instance


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_create_event_and_theme_over_http():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post("/login", json={"cpf": "12345678900"})
        assert login.status_code == 200
        token = login.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        event = await client.post(
            "/events",
            headers=headers,
            json={
                "name": "Evento API",
                "description": "teste",
                "latitude": -23.5505,
                "longitude": -46.6333,
                "radius": 500,
                "start_time": "2099-01-01T10:00:00",
                "end_time": "2099-01-01T12:00:00",
            },
        )
        assert event.status_code == 200
        assert "id" in event.json()

        theme = await client.post(
            "/voteThemes",
            headers=headers,
            json={
                "question": "Pergunta teste?",
                "options": ["Sim", "Nao"],
                "open_time": "2099-01-01T10:00:00",
                "close_time": "2099-01-01T12:00:00",
            },
        )
        assert theme.status_code == 200
        assert "id" in theme.json()


@pytest.mark.anyio
async def test_vote_requires_matching_theme_id():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post("/login", json={"cpf": "99999999999"})
        assert login.status_code == 200
        token = login.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        theme = await client.post(
            "/voteThemes",
            headers=headers,
            json={
                "question": "Tema atual",
                "options": ["A", "B"],
                "open_time": "2000-01-01T10:00:00",
                "close_time": "2099-01-01T12:00:00",
            },
        )
        assert theme.status_code == 200
        theme_id = theme.json()["id"]

        token_resp = await client.post("/voting/token", headers=headers, json={"theme_id": theme_id})
        assert token_resp.status_code == 200
        vote_token = token_resp.json()["token"]

        wrong_theme_vote = await client.post(
            "/vote",
            json={"theme_id": theme_id + 1, "option": "A", "token": vote_token},
        )
        assert wrong_theme_vote.status_code == 400


@pytest.mark.anyio
async def test_camara_snapshots_route_supports_filter_and_limit():
    db_instance.upsert_camara_snapshot(
        endpoint="/teste-endpoint-a",
        item_id="item-a",
        source_url="https://dadosabertos.camara.leg.br/api/v2/teste-a",
        sort_value="1",
        payload='{"ok": true, "name": "A"}',
    )
    db_instance.upsert_camara_snapshot(
        endpoint="/teste-endpoint-b",
        item_id="item-b",
        source_url="https://dadosabertos.camara.leg.br/api/v2/teste-b",
        sort_value="2",
        payload='{"ok": true, "name": "B"}',
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        filtered = await client.get("/camara/snapshots", params={"endpoint": "/teste-endpoint-a", "limit": 1})
        assert filtered.status_code == 200
        data = filtered.json()
        assert len(data) == 1
        assert data[0]["endpoint"] == "/teste-endpoint-a"
        assert data[0]["payload"]["name"] == "A"


@pytest.mark.anyio
async def test_deputados_normalizados_route_returns_rows():
    db_instance.upsert_deputado_normalizado(
        999777,
        {
            "uri": "https://dadosabertos.camara.leg.br/api/v2/deputados/999777",
            "nome_civil": "Deputado API",
            "cpf": "00000000000",
            "status_nome": "Deputado API",
            "status_email": "deputado@example.org",
            "status_sigla_partido": "API",
            "status_sigla_uf": "DF",
        },
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/deputados/normalizados", params={"limit": 5})
        assert resp.status_code == 200
        rows = resp.json()
        assert isinstance(rows, list)
        assert len(rows) >= 1

        resp_filtered = await client.get("/deputados/normalizados", params={"id": 999777, "limit": 5})
        assert resp_filtered.status_code == 200
        filtered_rows = resp_filtered.json()
        assert len(filtered_rows) >= 1
        assert all(row["id"] == 999777 for row in filtered_rows)
        assert "cpf" not in filtered_rows[0]
        assert "status_email" not in filtered_rows[0]


@pytest.mark.anyio
async def test_deputado_normalizado_detail_route_returns_404_when_missing():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/deputados/normalizados/123456789")
        assert resp.status_code == 404


@pytest.mark.anyio
async def test_deputado_normalizado_detail_route_returns_row():
    db_instance.upsert_deputado_normalizado(
        999778,
        {
            "uri": "https://dadosabertos.camara.leg.br/api/v2/deputados/999778",
            "nome_civil": "Deputado API 2",
            "cpf": "11111111111",
            "status_nome": "Deputado API 2",
            "status_email": "deputado2@example.org",
            "status_sigla_partido": "API",
            "status_sigla_uf": "SP",
        },
    )
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/deputados/normalizados/999778")
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == 999778
        assert body["status_nome"] == "Deputado API 2"
        assert "cpf" not in body
        assert "status_email" not in body


@pytest.mark.anyio
async def test_deputados_sync_status_route_returns_shape():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/deputados/sync-status")
        assert resp.status_code == 200
        body = resp.json()
        assert "ok" in body
        assert "total_normalizados" in body
        assert "last_sync" in body


@pytest.mark.anyio
async def test_deputados_despesas_resumo_route_returns_rows():
    db_instance.upsert_deputado_despesa(
        999778,
        {
            "ano": 2026,
            "mes": 1,
            "codLote": 1001,
            "codDocumento": "DOC-1",
            "parcela": 1,
            "tipoDespesa": "DIVULGAÇÃO DA ATIVIDADE PARLAMENTAR.",
            "valorLiquido": 1234.56,
            "nomeFornecedor": "Fornecedor Teste",
        },
    )
    db_instance.upsert_deputado_despesa(
        999778,
        {
            "ano": 2026,
            "mes": 2,
            "codLote": 1002,
            "codDocumento": "DOC-2",
            "parcela": 1,
            "tipoDespesa": "CONSULTORIAS, PESQUISAS E TRABALHOS TÉCNICOS.",
            "valorLiquido": 2345.67,
            "nomeFornecedor": "Fornecedor Teste 2",
        },
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/deputados/despesas/resumo", params={"limit": 10})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        row = next((item for item in data if item["id"] == 999778), None)
        assert row is not None
        assert "avg_last_3_months_liquido" in row
        assert "latest_total_liquido" in row


@pytest.mark.anyio
async def test_deputado_despesas_route_returns_rows():
    db_instance.upsert_deputado_despesa(
        999779,
        {
            "ano": 2026,
            "mes": 3,
            "codLote": 2001,
            "codDocumento": "DOC-A",
            "parcela": 1,
            "tipoDespesa": "PASSAGEM AÉREA - RPA",
            "valorLiquido": 987.65,
            "nomeFornecedor": "Fornecedor A",
            "dataDocumento": "2026-03-15",
        },
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/deputados/999779/despesas", params={"limit": 5, "page": 1})
        assert resp.status_code == 200
        rows = resp.json()
        assert isinstance(rows, list)
        assert len(rows) >= 1
        assert rows[0]["deputado_id"] == 999779
