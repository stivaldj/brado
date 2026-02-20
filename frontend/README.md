# Brado Frontend (Next.js)

Frontend reconstruído com Next.js App Router + TypeScript + Tailwind + componentes estilo shadcn/ui.

## Requisitos

- Node 18+
- npm ou pnpm

## Variáveis de ambiente

Crie `frontend/.env.local` (opcional):

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## Rodar localmente

```bash
cd frontend
npm run dev
```

Acesse `http://localhost:3000`.

## Telas

- `/dashboard`
- `/interview`
- `/results`
- `/budget`
- `/propositions`

## Fluxos implementados

- Token automático via `POST /api/v1/auth/token`
- Refresh automático em `401` (1 retry)
- Entrevista (`start`, `answer`, `finish`, `result`, `export json/pdf`)
- Simulador de orçamento com validação de soma = 100%
- Proposições com busca, paginação local e visualização RAW JSON

## Estado global

- Store persistida com Zustand (`lib/state/session.store.ts`): token, sessão ativa, respostas, pergunta atual e último resultado.

