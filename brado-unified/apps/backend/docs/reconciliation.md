# Reconciliation

## Checks implementados
- Cobertura deputados: contagem API atual vs contagem no grafo
- Cobertura deputados com despesas: `Person` com `HAS_EXPENSE` desde 2018 vs total de deputados atuais (gate habilitado para backfill completo sem filtro de deputado)
- Cobertura anual bills/votes/expenses desde 2018, com gate por ano completo ingerido
- Integridade referencial:
  - `VoteAction` deve ter `IN_EVENT -> VoteEvent`
  - `VoteAction` deve ter `Person -[:CAST]-> VoteAction`
  - `Expense` deve ter `Person -[:HAS_EXPENSE]-> Expense`
  - `VoteEvent.billId` deve implicar relação `ON_BILL -> Bill`
- Unicidade por ID canônico (`Person`, `Bill`, `VoteEvent`, `VoteAction`, `Expense`, `Organization`, `Party`, `State`)
- Consistência temporal dos batches (fetched_at dentro do range do batch)
- Auditoria amostral (até 50 por domínio: Bills/VoteEvents/Expenses) comparando canônico vs RAW
- Existência de RAW armazenado
- Votos nominais indisponíveis: exige `metadata.error_type` para respostas não-200 em `/votacoes/{id}/votos`
- Lacunas documentadas de despesas: `coverage_expenses_documented_gaps` falha quando último batch de despesas registra `coverage_gaps` > 0

## Gates
- `status=failed` quando existe qualquer item em `issues`
- `status=success` apenas com todos os checks OK e sem lacunas.

Cada issue contém:
- `issue_type`
- `check_name`
- `counts_expected`
- `counts_actual`
- `context`

## Saída
- Persistida em `reconcile_reports.report_json`
- Também exposta por:
  - `POST /admin/reconcile/all`
  - `GET /admin/reconcile/latest`

Exemplo resumido:
```json
{
  "status": "failed",
  "issues": [
    {
      "issue_type": "coverage_bills_year",
      "check_name": "coverage_bills_year",
      "counts_expected": 1200,
      "counts_actual": 1180,
      "context": {"year": 2020}
    }
  ]
}
```
