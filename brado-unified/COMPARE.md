# Comparativo Técnico: Projeto A vs Projeto B

## Inventário técnico (resumo)

### Projeto A (`/Users/joseoliveira/CODING/bradoretumbante/br_manifest_app`)
- Backend: Python + FastAPI modular (`app/api`, `app/core`, `app/db`, `app/political_interview`).
- Banco: PostgreSQL + Neo4j (com fallback SQLite em partes do fluxo).
- Infra: `docker-compose.yml`, Helm chart (`deploy/helm`), observabilidade (`deploy/observability`), scripts de deploy/rollback.
- Migrações: Alembic em `backend/app/db/sql/alembic`.
- Testes: suíte extensa (`unit`, `integration`, `contract`, `e2e`).
- Frontend: estático (`index.html`, `script.js`, `styles.css`).
- CI/CD: workflows em `.github/workflows/ci.yml` e `deploy-staging.yml`.

### Projeto B (`/Users/joseoliveira/CODING/bradoretumbante 2/br_manifest_app`)
- Backend: Python + FastAPI simples, focado em eventos/checkin/votação, sem modularização equivalente ao A.
- Banco: SQLite/fallback local.
- Infra: Dockerfile simples, sem nível de observabilidade/helm do A.
- Migrações: Alembic básico.
- Testes: muito mais limitado.
- Frontend: Next.js (App Router) + TS + Tailwind + shadcn + TanStack Query + Zustand + Zod + Recharts.

## Lixo versionado detectado

### Projeto A
- `backend/__pycache__`
- `backend/.pytest_cache`
- artefatos locais em `backend/.env`

### Projeto B
- `frontend/node_modules`
- `frontend/.next`
- `frontend/tsconfig.tsbuildinfo`
- `backend/venv`
- `backend/__pycache__`
- `backend/.env`
- `fallback.db`

## Tabela comparativa

| Aspecto | Projeto A | Projeto B |
| --- | --- | --- |
| Backend estrutura | Modular, domínios claros, routers v1, segurança e observabilidade | Simples, menos camadas e menor separação |
| Migrations | Alembic estruturado no core SQL | Alembic básico |
| Docker/Infra | Compose + Helm + observabilidade + scripts deploy | Básico, sem helm/observabilidade equivalente |
| Observabilidade | Métricas e middleware dedicados | Praticamente ausente |
| Testes | Forte cobertura (unit/contract/integration/e2e) | Cobertura limitada |
| Frontend qualidade | Frontend estático | Frontend produto (Next + TS + shadcn + Query + Zustand) |
| Organização | Backend/infra maduros | Frontend moderno melhor estruturado |
| Lixo versionado | Moderado | Alto (node_modules, .next, venv) |

## Decisão explícita

- Core backend/infra: **Projeto A**
- Core frontend/produto: **Projeto B**

## Justificativa técnica

- O Projeto A já implementa o contrato de API alvo (`/api/v1/auth/*`, `/api/v1/interview/*`, `/api/v1/budget/simulate`, `/api/v1/legislative/propositions`) com arquitetura mais segura, testável e operável.
- O Projeto B entrega frontend em padrão produto com stack moderna já alinhada à exigência de UX/UI e engenharia.
- A consolidação reduz risco: mantém backend estável/observável do A e acelera entrega do frontend robusto do B com integração real imediata.
