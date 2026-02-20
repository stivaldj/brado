# TODO (API Câmara - decisões em pontos ambíguos)

## Fontes oficiais consultadas
- Portal oficial API Dados Abertos da Câmara: https://dadosabertos.camara.leg.br/swagger/api.html

## Decisões implementadas
1. Votações nominais
- Implementado consumo de `/votacoes/{id}/votos`.
- Quando indisponível, o pipeline persiste RAW com `metadata.no_nominal_data=true` e segue sem quebrar ingestão global.

2. Despesas (CEAP)
- Prioridade para endpoint por deputado/ano: `/deputados/{id}/despesas?ano=...`.
- Se houver falhas por ano/deputado, registra `coverage_gap` no relatório de reconciliação.

3. Cobertura desde 2018
- Jobs de `bills/votes/expenses` aceitam `--from` (padrão `2018-01-01`).
- Lacunas de cobertura detectadas entram como `coverage_gap` e derrubam gate de reconciliação.

4. Paginação
- Implementada paginação pelo par `pagina` + leitura de `links.rel=next`.

## Pendências futuras
- Expandir mapeamentos de autores/temas/órgãos das proposições para maior completude semântica.
- Implementar provider real de ancoragem blockchain (placeholder existe).
