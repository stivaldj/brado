# Sync de Deputados via Cron

## Objetivo
Rodar sincronização incremental dos dados da Câmara periodicamente, cobrindo:
- entrada de novos deputados
- saída/destituição de deputados
- alterações de partido/UF/nome/dados cadastrais

## Script
- `backend/cron_sync_deputados.sh`

O script:
1. Evita concorrência (lock com `flock` ou fallback com lock dir).
2. Executa `python3 -m backend.sync_deputados`.
3. Registra logs em `backend/logs/sync_deputados.log`.

## Exemplo de crontab (a cada 30 minutos)

```cron
*/30 * * * * cd /Users/joseoliveira/CODING/bradoretumbante\ 2/br_manifest_app && ./backend/cron_sync_deputados.sh
```

## Exemplo diário (03:10)

```cron
10 3 * * * cd /Users/joseoliveira/CODING/bradoretumbante\ 2/br_manifest_app && ./backend/cron_sync_deputados.sh
```

## Ver logs

```bash
tail -f backend/logs/sync_deputados.log
```

## Observações
- A rotina remove deputados que não aparecem mais na lista atual da Câmara.
- A rotina atualiza snapshots e a tabela `deputados_normalizados` de forma incremental.
- Por padrão, não baixa bytes de foto (somente URL/metadados).  
  Para baixar imagens no sync, use `python3 -m backend.sync_deputados --with-image`.
