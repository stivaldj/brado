# Political Interview Module

## Objetivo
Camada analitica para entrevista politica adaptativa com vetor ideologico 8D, ranking por similaridade e simulacao orcamentaria.

## Componentes
- `app/political_interview/service.py`: orchestrator da entrevista e persistencia.
- `app/political_interview/scoring.py`: calculo de vetor 8D, esquerda-direita, confianca e consistencia.
- `app/political_interview/similarity.py`: similaridade por cosseno e explicacao de proximidade.
- `app/political_interview/budget.py`: validacao de 100% e trade-offs.
- `app/political_interview/question_bank.py`: seed de 600 perguntas e selecao adaptativa.

## Endpoints
- `POST /api/v1/auth/token`
- `GET /api/v1/auth/me`
- `POST /api/v1/interview/start`
- `POST /api/v1/interview/{session_id}/answer`
- `POST /api/v1/interview/{session_id}/finish`
- `GET /api/v1/interview/{session_id}/result`
- `GET /api/v1/interview/{session_id}/export?format=json|pdf`
- `POST /api/v1/budget/simulate`
- `GET /api/v1/legislative/propositions`
- `POST /api/v1/profiles/legislators`
- `POST /api/v1/profiles/parties`

## Fluxo
1. `start`: cria sessao anonimizada por hash SHA-256 com salt.
2. `answer`: grava resposta e escolhe proxima pergunta pela menor confianca dimensional.
3. `finish`: exige minimo configuravel de respostas, calcula resultado e gera ranking.

## Seguranca de API v1
- JWT HS256 com secret configuravel (`API_V1_JWT_SECRET`).
- TTL configuravel (`API_V1_JWT_TTL_SECONDS`).
- Modo obrigatorio opcional (`API_V1_AUTH_REQUIRED=true`).
- Rate limit por sessao (`API_V1_RATE_LIMIT_PER_MINUTE`).

## LGPD
- O identificador do usuario nao e persistido em texto puro.
- Campo persistido: `anon_user_hash`.
- Salt configuravel por `INTERVIEW_ANONYMIZATION_SALT`.

## Seed
```bash
python -m app.cli interview:seed --total 600
```

## Atualizacao de perfis ideologicos
Gera/atualiza `legislator_profiles` e `party_profiles` com base em votos nominais RAW ja coletados.
```bash
python -m app.cli interview:refresh-profiles --limit-payloads 500
```

## Observabilidade
O backend ja utiliza logging estruturado JSON em `app/core/logging`.

## Frontend de referencia
- `frontend/index.html`
- `frontend/script.js`
- `frontend/styles.css`

Painel inclui entrevista conversacional, radar 8D (ECharts), ranking, simulador de orcamento e export JSON/PDF.
O cliente web tambem faz refresh silencioso de JWT antes da expiracao e revalida auth ao retornar foco para a aba.
