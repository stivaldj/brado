# Data Dictionary

## RAW (Postgres)

### `raw_payloads`
- `source`: origem (`camara`)
- `endpoint`: endpoint consultado
- `params_json`: parâmetros HTTP
- `primary_key`: id lógico principal do recurso
- `fetched_at`: timestamp de coleta/versionamento
- `sha256`: hash canônico do payload
- `body_json`: payload bruto completo
- `batch_id`: lote de ingestão
- `body_json.metadata.error_type`: definido para falhas nominais de `/votacoes/{id}/votos` (`nominal_votes_not_available`, `upstream_error`, etc.)
- `source=camara_dataset`: payload de fallback CSV anual de despesas (`/datasets/despesas/{ano}`)

### `ingestion_batches`
- metadados do lote (`batch_type`, range, status, contagem)
- `merkle_root`: raiz Merkle do lote
- `anchor_id`: referência da ancoragem

### `batch_items`
- item por payload dentro do lote
- `item_sha256`: hash do payload
- `leaf_index`: ordem da folha

### `anchors`
- registro de ancoragem do root
- `anchor_type`: `file-log`/`postgres`/etc
- `provider_payload`: metadados do provider

### `job_state`
- checkpoint de jobs (`job_name`, cursor, status)

### `reconcile_reports`
- resultado dos checks de reconciliação

### `interview_questions`
- banco de perguntas estruturadas (`id`, `prompt`, `response_type`, `dimensions_json`, `tags_json`)
- dimensão base: vetor 8D (`ECO`, `SOC`, `EST`, `AMB`, `LIB`, `GOV`, `GLB`, `INS`)

### `interview_sessions`
- sessão de entrevista anonimizadas (`anon_user_hash`)
- status de ciclo de vida (`in_progress`, `completed`)

### `interview_answers`
- respostas por sessão
- regra de unicidade por `(session_id, question_id)`

### `interview_results`
- resultado consolidado (vetor 8D, projeção esquerda-direita, confiança, consistência)
- ranking de similaridade com parlamentares e partidos

### `legislator_profiles`
- perfis ideológicos de parlamentares para comparação de similaridade

### `party_profiles`
- perfis ideológicos de partidos para comparação de similaridade

## Canonical (Neo4j)

### IDs canônicos
- `Person.id = camara:person:{idDeputado}`
- `Bill.id = camara:bill:{idProposicao}`
- `VoteEvent.id = camara:vote_event:{idVotacao}`
- `VoteAction.id = camara:vote_action:{voteEventId}:{personId}`
- `Expense.id = camara:expense:{sourceRowIdOrComposite}`
- `Organization.id = camara:org:{normalizedNameOrId}`

### Nós e relações principais
- `(:Person)-[:MEMBER_OF]->(:Party)`
- `(:Person)-[:REPRESENTS]->(:State)`
- `(:VoteEvent)-[:ON_BILL]->(:Bill)`
- `(:Person)-[:CAST]->(:VoteAction)-[:IN_EVENT]->(:VoteEvent)`
- `(:Person)-[:HAS_EXPENSE]->(:Expense)-[:PAID_TO]->(:Organization)`

## Regras de normalização
- IDs determinísticos por domínio
- `MERGE` para idempotência
- atualização controlada de `lastSeenAt`, `rawRefs`, `source` fields

## Regras de geração de ID
- Person: `camara:person:{idDeputado}`
- Bill: `camara:bill:{idProposicao}`
- VoteEvent: `camara:vote_event:{idVotacao}`
- VoteAction: `camara:vote_action:{voteEventId}:{personId}`
- Expense: hash determinístico de `codDocumento` (ou chave composta quando ausente)
- Organization: hash determinístico de `cnpjCpfFornecedor` (ou nome fornecedor)

## RAW vs Canonical (resumo)
- RAW: payload integral por request HTTP, versionado por `fetched_at`, hash `sha256`, preservando status real.
- Canonical: entidades normalizadas no Neo4j, com IDs estáveis e relações referenciais.
