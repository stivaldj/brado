import pytest

pytest.importorskip("sqlalchemy")

from app.reconcile.service import ReconcileService


class _FakeResult:
    def __init__(self, single_row=None, rows=None):
        self._single_row = single_row
        self._rows = rows or []

    def single(self):
        return self._single_row

    def __iter__(self):
        return iter(self._rows)


class _FakeNeoSession:
    def __init__(self, handler):
        self._handler = handler

    def run(self, query, **params):
        return self._handler(query, params)


class _FakeNeoSessionCtx:
    def __init__(self, handler):
        self._handler = handler

    def __enter__(self):
        return _FakeNeoSession(self._handler)

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeDriver:
    def __init__(self, handler):
        self._handler = handler

    def session(self):
        return _FakeNeoSessionCtx(self._handler)


class _FakeGraph:
    def __init__(self, handler):
        self.client = type("Client", (), {"driver": _FakeDriver(handler)})()


class _FakeRawPayload:
    def __init__(self, body_json):
        self.body_json = body_json


class _FakeDbSession:
    def __init__(self, raw_map=None):
        self.raw_map = raw_map or {}

    def get(self, _model, key):
        return self.raw_map.get(key)


def _build_service(graph_handler, raw_map=None):
    svc = ReconcileService.__new__(ReconcileService)
    svc.graph = _FakeGraph(graph_handler)
    svc.session = _FakeDbSession(raw_map)
    return svc


def test_estimate_api_total_with_last_link():
    body = {
        "dados": [{"id": 1}],
        "links": [
            {"rel": "self", "href": "https://example.test/recurso?pagina=1&itens=1"},
            {"rel": "last", "href": "https://example.test/recurso?pagina=37&itens=1"},
        ],
    }
    assert ReconcileService._estimate_api_total(body, itens_per_page=1) == 37


def test_audit_samples_detects_match_and_mismatch():
    def handler(query, params):
        if "MATCH (n:Bill)" in query:
            return _FakeResult(
                rows=[
                    {
                        "id": "camara:bill:1",
                        "sourceId": 1,
                        "rawRefs": ["raw_ok"],
                        "rawRef": None,
                        "ano": 2024,
                        "numero": 100,
                        "dataHoraRegistro": None,
                        "year": None,
                        "month": None,
                    },
                    {
                        "id": "camara:bill:2",
                        "sourceId": 2,
                        "rawRefs": ["raw_bad"],
                        "rawRef": None,
                        "ano": 2024,
                        "numero": 200,
                        "dataHoraRegistro": None,
                        "year": None,
                        "month": None,
                    },
                ]
            )
        return _FakeResult(single_row={"c": 0})

    raw_map = {
        "raw_ok": _FakeRawPayload({"dados": {"id": 1, "ano": 2024, "numero": 100}}),
        "raw_bad": _FakeRawPayload({"dados": {"id": 2, "ano": 2024, "numero": 999}}),
    }

    svc = _build_service(handler, raw_map)
    audit = svc._audit_samples("Bill", limit=50)

    assert audit["checked"] == 2
    assert audit["mismatches"] == 1
    assert audit["ok"] is False


def test_reconcile_gate_fails_with_coverage_gap():
    class _SessionWithReport(_FakeDbSession):
        def __init__(self):
            super().__init__()
            self.added = []

        def scalar(self, *_args, **_kwargs):
            return 1

        def add(self, obj):
            if getattr(obj, "id", None) is None:
                obj.id = "report-1"
            self.added.append(obj)

        def flush(self):
            return None

    svc = ReconcileService.__new__(ReconcileService)
    svc.session = _SessionWithReport()
    svc.client = type("C", (), {"close": lambda self: None})()
    svc.graph = type("G", (), {"close": lambda self: None})()

    svc._coverage_checks = lambda: ([{"name": "dummy_cov", "ok": True}], [{"domain": "bills", "year": 2018, "reason": "gap"}])
    svc._integrity_checks = lambda: [{"name": "int", "ok": True}]
    svc._uniqueness_checks = lambda: [{"name": "uniq", "ok": True}]
    svc._temporal_checks = lambda: [{"name": "temp", "ok": True}]
    svc._audit_samples = lambda _label, _limit=50: {"label": _label, "checked": 1, "mismatches": 0, "ok": True}

    result = svc.reconcile_all()
    assert result.status == "failed"
    assert result.report["coverage_gap"]


def test_expense_people_coverage_gate_enabled_only_for_full_backfill():
    class _State:
        def __init__(self, status, cursor_json):
            self.status = status
            self.cursor_json = cursor_json

    class _Session:
        def __init__(self, state):
            self._state = state

        def get(self, _model, key):
            if key == "ingest_expenses_since":
                return self._state
            return None

    svc = ReconcileService.__new__(ReconcileService)
    svc.session = _Session(_State("success", {"deputado_ids": []}))
    assert svc._expense_people_coverage_gate_enabled() is True

    svc.session = _Session(_State("success", {"deputado_ids": [10, 11]}))
    assert svc._expense_people_coverage_gate_enabled() is False

    svc.session = _Session(_State("failed", {"deputado_ids": []}))
    assert svc._expense_people_coverage_gate_enabled() is False


def test_documented_expense_gap_check_fails_when_batch_notes_has_gaps():
    class _Batch:
        notes = '{"coverage_gaps":[{"deputado_id":1,"year":2024}]}'

    class _ScalarResult:
        def first(self):
            return _Batch()

    class _ExecResult:
        def scalars(self):
            return _ScalarResult()

    class _Session:
        def execute(self, *_args, **_kwargs):
            return _ExecResult()

    svc = ReconcileService.__new__(ReconcileService)
    svc.session = _Session()
    check = svc._documented_expense_gap_check()
    assert check["name"] == "coverage_expenses_documented_gaps"
    assert check["ok"] is False
    assert check["counts_actual"] == 1
