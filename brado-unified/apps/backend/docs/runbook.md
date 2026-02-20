# Runbook

## 1. Subir stack
```bash
cd br_manifest_app
docker compose up -d --build
```

## 2. Rodar migrações
```bash
docker compose exec backend alembic -c /app/alembic.ini upgrade head
```

## 3. Rodar backfill 2018..atual
```bash
docker compose exec backend python -m app.cli ingest:all --from 2018-01-01
```
- `ingest_expenses_since` agora pagina todos os deputados (`/deputados`, `itens=100`, todas as páginas) e todas as páginas de despesas por deputado/ano.
- Fallback opcional para dataset anual de despesas (quando a API REST falha por lacuna):
```bash
export CAMARA_EXPENSES_DATASET_URL_TEMPLATE="https://.../despesas-{year}.csv"
export CAMARA_EXPENSES_DATASET_SEPARATOR=","
```

## 4. Retomar após falha
- O estado fica em `job_state` (`job_name`, `cursor_json`, `status`).
- Reexecute o comando do job (`ingest:bills`, `ingest:votes`, etc.).
- O pipeline retoma da página/posição salva no cursor quando disponível.
- Inspecione o estado recente por API:
```bash
curl -H "X-API-Key: $ADMIN_API_KEY" "http://localhost:8000/admin/job_state?limit=20&offset=0"
```

## 5. Validar reconciliação
```bash
docker compose exec backend python -m app.cli reconcile:all
```
- Resultado detalhado fica em `reconcile_reports.report_json`.
- Se houver issue de gate (`issues`), o reconcile falha e o CLI retorna exit code diferente de zero.

## 6. Interpretar prova (Merkle + anchor)
- Cada batch gera folhas em `batch_items` (ordenadas por `leaf_index`).
- `ingestion_batches.merkle_root` guarda raiz do lote.
- `anchors` guarda ancoragem em Postgres.
- `app/proof/anchor_log.json` guarda ancoragem em arquivo (auditoria local).

## 7. Rodar testes
```bash
docker compose exec backend pytest -q
```
- Observação: `tests/unit/test_reconcile_logic.py` usa `importorskip("sqlalchemy")`.
  Em ambiente sem dependências instaladas localmente, esse teste fica `skipped`.

### Testes de integração (Postgres + Neo4j)
```bash
docker compose exec backend pytest -q -m integration
```
- `tests/integration/test_reconcile_integration.py` valida reconciliação com bancos reais.
- Se Postgres/Neo4j não estiverem acessíveis no ambiente local, os testes ficam `skipped`.

## 8. Smoke real
```bash
docker compose exec backend python -m app.cli test:smoke-real --sample-size 5
```
- Fluxo smoke:
  - ingere deputados atuais
  - seleciona 5 deputados aleatórios
  - ingere votos dos últimos 30 dias (com filtro de ações desses 5 quando nominal)
  - ingere despesas dos últimos 30 dias para esses 5
  - roda reconciliação

## 10. Endpoints Câmara (Swagger oficial)
- Swagger base: https://dadosabertos.camara.leg.br/swagger/api.html
- Usados na ingestão:
  - `GET /deputados` e `GET /deputados/{id}`
  - `GET /deputados/{id}/despesas`
  - `GET /proposicoes` e `GET /proposicoes/{id}`
  - `GET /votacoes`, `GET /votacoes/{id}`, `GET /votacoes/{id}/votos`

## 9. CI (GitHub Actions)
- Workflow: `br_manifest_app/.github/workflows/ci.yml`
- Jobs:
  - `unit-contract`: roda `pytest -q tests/unit tests/contract`
  - `integration`: sobe Postgres + Neo4j como services, roda migrations e `pytest -q -m integration`
