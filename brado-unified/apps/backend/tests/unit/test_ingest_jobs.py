from __future__ import annotations

from datetime import date

import pytest

pytest.importorskip("sqlalchemy")

from app.db.sql.models import JobState
from app.jobs.ingest_jobs import IngestJobs


class _FakeBatch:
    def __init__(self, batch_id: str):
        self.id = batch_id


class _FakeRaw:
    def __init__(self, raw_id: str):
        self.id = raw_id


class _FakeRawStore:
    def __init__(self):
        self.payloads = []
        self._seq = 0

    def start_batch(self, *_args, **_kwargs):
        return _FakeBatch("batch-1")

    def add_payload(self, **kwargs):
        self._seq += 1
        raw = _FakeRaw(f"raw-{self._seq}")
        self.payloads.append({**kwargs, "raw_id": raw.id})
        return raw

    def finish_batch(self, *_args, **_kwargs):
        return None

    def fail_batch(self, *_args, **_kwargs):
        return None


class _FakeGraph:
    def __init__(self):
        self.expenses = []
        self.vote_events = []
        self.vote_actions = []
        self.bills = []

    def close(self):
        return None

    def ensure_constraints(self):
        return None

    def upsert_expense(self, node, _raw_ref=None):
        self.expenses.append(node)

    def upsert_vote_event(self, node, _raw_ref=None):
        self.vote_events.append(node)

    def upsert_vote_action(self, node, _raw_ref=None):
        self.vote_actions.append(node)

    def upsert_bill(self, node, _raw_ref=None):
        self.bills.append(node)


class _FakeSession:
    def __init__(self):
        self.states = {}

    def get(self, model, key):
        if model is JobState:
            return self.states.get(key)
        return None

    def add(self, obj):
        if isinstance(obj, JobState):
            self.states[obj.job_name] = obj

    def flush(self):
        return None


class _FakeClient:
    def __init__(
        self,
        dep_pages: list[list[int]],
        nominal_statuses: dict[int, tuple[int, dict]] | None = None,
        fail_expense_years: set[int] | None = None,
        fail_bills: bool = False,
        fail_votes: bool = False,
        dataset_csv: str = "",
        static_texts: dict[str, tuple[int, str]] | None = None,
    ):
        self.dep_pages = dep_pages
        self.nominal_statuses = nominal_statuses or {}
        self.fail_expense_years = fail_expense_years or set()
        self.fail_bills = fail_bills
        self.fail_votes = fail_votes
        self.dataset_csv = dataset_csv
        self.static_texts = static_texts or {}
        self.expense_calls: list[tuple[str, dict]] = []

    def close(self):
        return None

    def paginated(self, endpoint, params=None, max_pages=None):
        params = dict(params or {})
        if endpoint == "/deputados":
            pages = self.dep_pages[: max_pages or len(self.dep_pages)]
            for idx, ids in enumerate(pages, start=1):
                yield 200, {"dados": [{"id": i} for i in ids], "links": []}, {"itens": 100, "pagina": idx}
            return

        if endpoint.startswith("/deputados/") and endpoint.endswith("/despesas"):
            dep_id = int(endpoint.split("/")[2])
            year = int(params.get("ano"))
            if year in self.fail_expense_years:
                raise RuntimeError("api_expense_failure")
            self.expense_calls.append((endpoint, dict(params)))
            body = {
                "dados": [
                    {
                        "codDocumento": f"{dep_id}-{year}",
                        "ano": year,
                        "mes": 1,
                        "valorDocumento": 10.0,
                        "nomeFornecedor": "Fornecedor Teste",
                    }
                ],
                "links": [],
            }
            yield 200, body, {"ano": year, "itens": 100, "pagina": 1}
            return

        if endpoint == "/proposicoes":
            if self.fail_bills:
                raise RuntimeError("api_bills_failure")
            yield 200, {"dados": [{"id": 99}], "links": []}, {"pagina": 1, "itens": 100}
            return

        if endpoint == "/votacoes":
            if self.fail_votes:
                raise RuntimeError("api_votes_failure")
            yield 200, {"dados": [{"id": 10}, {"id": 11}], "links": []}, {"pagina": 1, "itens": 100}
            return

        raise AssertionError(f"Unexpected paginated endpoint: {endpoint}")

    def get_text(self, url, *, raise_for_status=True):
        if url in self.static_texts:
            return self.static_texts[url]
        return 200, self.dataset_csv

    def fetch_many(self, requests, *, max_workers=None, raise_for_status=True):
        response = []
        for endpoint, _params in requests:
            if endpoint.startswith("/proposicoes/"):
                prop_id = int(endpoint.split("/")[2])
                response.append((200, {"dados": {"id": prop_id, "ano": 2024, "numero": prop_id}}))
            elif endpoint.startswith("/votacoes/") and endpoint.endswith("/votos"):
                votacao_id = int(endpoint.split("/")[2])
                response.append(self.nominal_statuses[votacao_id])
            elif endpoint.startswith("/votacoes/"):
                votacao_id = int(endpoint.split("/")[2])
                response.append((200, {"dados": {"id": votacao_id, "idProposicao": None}}))
            else:
                raise AssertionError(f"Unexpected fetch endpoint: {endpoint}")
        return response


def _build_jobs(fake_client: _FakeClient):
    jobs = IngestJobs.__new__(IngestJobs)
    jobs.session = _FakeSession()
    jobs.raw_store = _FakeRawStore()
    jobs.client = fake_client
    jobs.graph = _FakeGraph()
    jobs._max_workers = 8
    return jobs


def test_ingest_expenses_since_paginates_all_deputados_513():
    dep_pages = [list(range(1, 151)), list(range(151, 301)), list(range(301, 451)), list(range(451, 514))]
    jobs = _build_jobs(_FakeClient(dep_pages=dep_pages))

    result = jobs.ingest_expenses_since(date(2024, 1, 1), to_date=date(2024, 12, 31))

    assert result["status"] == "success"
    assert result["processed"] == 513
    assert len(jobs.graph.expenses) == 513
    assert len({expense["personId"] for expense in jobs.graph.expenses}) == 513

    dep_seed_payloads = [p for p in jobs.raw_store.payloads if p["endpoint"] == "/deputados"]
    assert len(dep_seed_payloads) == 4


def test_ingest_expenses_since_collects_all_years_from_2018_window():
    jobs = _build_jobs(_FakeClient(dep_pages=[[1, 2]]))

    result = jobs.ingest_expenses_since(date(2018, 1, 1), to_date=date(2020, 12, 31))

    assert result["processed"] == 6
    years = sorted({call[1]["ano"] for call in jobs.client.expense_calls})
    assert years == [2018, 2019, 2020]


def test_ingest_votes_since_stores_real_http_status_for_nominal_fallbacks():
    jobs = _build_jobs(
        _FakeClient(
            dep_pages=[[1]],
            nominal_statuses={
                10: (404, {"dados": []}),
                11: (500, {"erro": "upstream"}),
            },
        )
    )

    result = jobs.ingest_votes_since(date(2024, 1, 1), to_date=date(2024, 1, 31))

    assert result["events"] == 2
    assert result["actions"] == 0

    nominal_payloads = [
        p for p in jobs.raw_store.payloads if p["endpoint"].startswith("/votacoes/") and p["endpoint"].endswith("/votos")
    ]
    status_by_endpoint = {payload["endpoint"]: payload["http_status"] for payload in nominal_payloads}
    assert status_by_endpoint["/votacoes/10/votos"] == 404
    assert status_by_endpoint["/votacoes/11/votos"] == 500

    body_404 = next(p["body_json"] for p in nominal_payloads if p["endpoint"] == "/votacoes/10/votos")
    body_500 = next(p["body_json"] for p in nominal_payloads if p["endpoint"] == "/votacoes/11/votos")
    assert body_404["metadata"]["error_type"] == "nominal_votes_not_available"
    assert body_500["metadata"]["error_type"] == "upstream_error"


def test_smoke_real_samples_5_deputados_from_full_pagination(monkeypatch):
    dep_pages = [list(range(1, 151)), list(range(151, 301)), list(range(301, 451)), list(range(451, 514))]
    jobs = _build_jobs(_FakeClient(dep_pages=dep_pages))

    monkeypatch.setattr("app.jobs.ingest_jobs.random.sample", lambda seq, k: list(seq[-k:]))
    jobs.ingest_deputados_current = lambda max_pages=None: {"status": "success", "processed": 513}
    jobs.ingest_votes_since = lambda *args, **kwargs: {"status": "success", "actions": 0}
    captured = {}

    def _fake_ingest_expenses(_from, to_date=None, deputado_ids=None):
        captured["deputado_ids"] = deputado_ids
        return {"status": "success", "processed": len(deputado_ids or [])}

    jobs.ingest_expenses_since = _fake_ingest_expenses

    result = jobs.smoke_real(sample_size=5)

    assert len(result["selected_deputados"]) == 5
    assert result["selected_deputados"] == [509, 510, 511, 512, 513]
    assert captured["deputado_ids"] == [509, 510, 511, 512, 513]


def test_ingest_expenses_since_uses_dataset_fallback_when_api_has_gaps(monkeypatch):
    monkeypatch.setenv("CAMARA_EXPENSES_DATASET_URL_TEMPLATE", "https://example.test/despesas-{year}.csv")
    monkeypatch.setenv("CAMARA_EXPENSES_DATASET_SEPARATOR", ",")
    from app.core.config import get_settings

    get_settings.cache_clear()
    csv_text = "idDeputado,mes,valorDocumento,nomeFornecedor\\n1,2,99.5,Fornecedor Dataset\\n"
    jobs = _build_jobs(_FakeClient(dep_pages=[[1]], fail_expense_years={2024}, dataset_csv=csv_text))

    result = jobs.ingest_expenses_since(date(2024, 1, 1), to_date=date(2024, 12, 31))

    assert result["status"] == "success"
    assert result["fallback_rows"] == 1
    dataset_payload = next(p for p in jobs.raw_store.payloads if p["endpoint"] == "/datasets/despesas/2024")
    assert dataset_payload["http_status"] == 200
    assert len(jobs.graph.expenses) == 1


def test_ingest_bills_since_uses_static_fallback_when_api_fails(monkeypatch):
    monkeypatch.setenv(
        "CAMARA_PROPOSICOES_STATIC_URL_TEMPLATE",
        "https://dadosabertos.camara.leg.br/arquivos/proposicoes/json/proposicoes-{year}.json",
    )
    from app.core.config import get_settings

    get_settings.cache_clear()
    static_url = "https://dadosabertos.camara.leg.br/arquivos/proposicoes/json/proposicoes-2024.json"
    static_payload = '[{"id":1234,"ano":2024,"numero":55,"siglaTipo":"PL","dataApresentacao":"2024-01-10"}]'
    jobs = _build_jobs(
        _FakeClient(
            dep_pages=[[1]],
            fail_bills=True,
            static_texts={static_url: (200, static_payload)},
        )
    )

    result = jobs.ingest_bills_since(date(2024, 1, 1), to_date=date(2024, 1, 31))

    assert result["status"] == "success"
    assert result["processed"] == 1
    dataset_payload = next(p for p in jobs.raw_store.payloads if p["endpoint"] == "/datasets/proposicoes/2024")
    assert dataset_payload["http_status"] == 200
    assert len(jobs.graph.bills) == 1


def test_ingest_votes_since_uses_static_fallback_when_api_fails(monkeypatch):
    monkeypatch.setenv(
        "CAMARA_VOTACOES_STATIC_URL_TEMPLATE",
        "https://dadosabertos.camara.leg.br/arquivos/votacoes/json/votacoes-{year}.json",
    )
    monkeypatch.setenv(
        "CAMARA_VOTACOES_VOTOS_STATIC_URL_TEMPLATE",
        "https://dadosabertos.camara.leg.br/arquivos/votacoesVotos/json/votacoesVotos-{year}.json",
    )
    from app.core.config import get_settings

    get_settings.cache_clear()
    votes_url = "https://dadosabertos.camara.leg.br/arquivos/votacoes/json/votacoes-2024.json"
    votes_votos_url = "https://dadosabertos.camara.leg.br/arquivos/votacoesVotos/json/votacoesVotos-2024.json"
    votes_payload = '[{"id":"v1","data":"2024-01-10","uriProposicao":"https://dadosabertos.camara.leg.br/api/v2/proposicoes/10"}]'
    votes_votos_payload = '[{"idVotacao":"v1","idDeputado":1,"voto":"Sim"}]'
    jobs = _build_jobs(
        _FakeClient(
            dep_pages=[[1]],
            fail_votes=True,
            static_texts={
                votes_url: (200, votes_payload),
                votes_votos_url: (200, votes_votos_payload),
            },
        )
    )

    result = jobs.ingest_votes_since(date(2024, 1, 1), to_date=date(2024, 1, 31))

    assert result["status"] == "success"
    assert result["events"] == 1
    assert result["actions"] == 1
    dataset_events_payload = next(p for p in jobs.raw_store.payloads if p["endpoint"] == "/datasets/votacoes/2024")
    dataset_actions_payload = next(p for p in jobs.raw_store.payloads if p["endpoint"] == "/datasets/votacoesVotos/2024")
    assert dataset_events_payload["http_status"] == 200
    assert dataset_actions_payload["http_status"] == 200
    get_settings.cache_clear()
