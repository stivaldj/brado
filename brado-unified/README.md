# brado-unified

Monorepo consolidado com backend/infra do Projeto A e frontend produto do Projeto B.

## Visão geral

- `apps/backend`: API FastAPI com contrato `/api/v1/*`, autenticação JWT, entrevista política, orçamento e proposições.
- `apps/frontend`: Next.js App Router com TS, Tailwind, shadcn/ui, TanStack Query, Zustand, Zod e Recharts.
- `infra`: helm, observabilidade e scripts de deploy herdados do core infra.
- `scripts/smoke.sh`: validação automática fim-a-fim da stack docker.

## Arquitetura

- Backend: FastAPI + SQLAlchemy + Alembic + Postgres + Neo4j.
- Frontend: Next.js (App Router), cliente API com refresh automático em `401`.
- Infra local: Docker Compose com healthchecks.

## Estrutura

```text
brado-unified/
  apps/
    backend/
    frontend/
  infra/
  scripts/
  docs/
  README.md
  docker-compose.yml
  .env.example
```

## Setup local

### Backend

```bash
cd apps/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd apps/frontend
npm install
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

## Setup docker

```bash
docker compose up --build
```

- Frontend: `http://localhost:13000` (ou `FRONTEND_PORT`)
- Backend: `http://localhost:18000` (ou `BACKEND_PORT`)
- Health: `http://localhost:18000/health`

## Variáveis de ambiente

Base em `.env.example`:

- Backend: `DATABASE_URL`, `NEO4J_*`, `API_V1_*`, `CORS_ALLOW_ORIGINS`, etc.
- Frontend: `NEXT_PUBLIC_API_BASE_URL`, `FRONTEND_PORT`, `BACKEND_PORT`.

## Como rodar testes

```bash
cd apps/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest tests/unit/test_auth_v1_router.py tests/unit/test_interview_router.py tests/contract/test_interview_openapi.py
```

## Como rodar smoke

```bash
./scripts/smoke.sh
```

## Troubleshooting

- `401` no frontend:
  - confirme `API_V1_AUTH_REQUIRED=true` no backend e `NEXT_PUBLIC_API_BASE_URL` correto no frontend.
- CORS:
  - ajuste `CORS_ALLOW_ORIGINS` para incluir host/porta do frontend.
- backend não sobe no docker:
  - valide portas ocupadas (`5432`, `7474`, `7687`, `8000`, `3000`) e reinicie `docker compose down -v`.
