# API Mapping

## Resultado

O backend consolidado (core do Projeto A) já expõe o contrato alvo do frontend.

## Contrato alvo x contrato real

- `POST /api/v1/auth/token` -> compatível
- `GET /api/v1/auth/me` -> compatível
- `POST /api/v1/interview/start` -> compatível
- `POST /api/v1/interview/{session_id}/answer` -> compatível
- `POST /api/v1/interview/{session_id}/finish` -> compatível
- `GET /api/v1/interview/{session_id}/result` -> compatível
- `GET /api/v1/interview/{session_id}/export?format=json|pdf` -> compatível
- `POST /api/v1/budget/simulate` -> compatível
- `GET /api/v1/legislative/propositions` -> compatível

## Observações de integração

- `NEXT_PUBLIC_API_BASE_URL` é obrigatório no frontend e aponta para o backend.
- Fluxo auth implementado no cliente:
  - `ensureToken()` para bootstrap/renovação antecipada.
  - `apiFetch()` injeta Bearer para rotas `/api/v1/*`.
  - Em `401`, ocorre refresh automático uma única vez e retry da requisição.
