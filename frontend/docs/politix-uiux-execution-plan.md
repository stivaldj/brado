# Plano de Execucao UI/UX Politix

Objetivo: alinhar todo o frontend ao estilo de `frontend/ref-politix.html` com consistencia visual, previsibilidade de manutencao e zero regressao funcional.

Escopo: todas as rotas em `frontend/app/(shell)` e componentes compartilhados de layout/visual.

## Principio de execucao
- Uma unica linguagem visual para todo o app.
- Estilos centralizados em design system (tokens + componentes base).
- Nada de ajuste visual isolado por pagina sem virar componente reutilizavel.
- Sem dependencia de prazo em dias: sequencia por PR, pronta para execucao imediata por agente.

## Ordem de PRs (pipeline)

## PR1 - Fundacao visual unica
Objetivo: eliminar conflitos de CSS global e definir base oficial do tema.

Arquivos alvo:
- `frontend/app/globals.css`
- `frontend/components/ui/glossy-card.tsx`
- `frontend/components/layout/kicker-header.tsx`

Tarefas:
1. Consolidar variaveis visuais em um bloco unico de tokens (cores, bordas, radius, spacing, tipografia).
2. Remover duplicacoes de classes `.civic-*` com definicoes conflitantes.
3. Definir primitives visuais base:
   - `window`
   - `window-header`
   - `window-content`
   - `stat-box`
   - `data-row`
   - `tag` (approve/reject/neutral)
4. Reduzir efeito glossy para um visual mais "politix" (mais estrutura, menos brilho).

Criterios de aceite:
- Nao existe classe global duplicada com semantica diferente.
- `globals.css` fica com hierarquia clara de tokens/base/components/utilities.
- Componentes nao dependem de style inline para visual principal.

---

## PR2 - Shell e navegacao
Objetivo: aplicar linguagem politix no frame inteiro da aplicacao.

Arquivos alvo:
- `frontend/components/layout/app-shell.tsx`
- `frontend/components/layout/sidebar.tsx`
- `frontend/components/layout/top-nav.tsx`
- `frontend/app/(shell)/layout.tsx`

Tarefas:
1. Refatorar top nav para padrao semantico do ref (kicker/titulo/acoes discretas).
2. Ajustar sidebar para contraste, espacamento e estados ativos padronizados.
3. Garantir comportamento mobile consistente (sheet/drawer sem quebra de layout).
4. Unificar paddings laterais e ritmo vertical de todas as paginas no shell.

Criterios de aceite:
- Shell visualmente consistente em todas as rotas.
- Desktop/tablet/mobile sem sobreposicoes ou scroll horizontal.

---

## PR3 - Pagina Parlamentares
Objetivo: transformar listagem em modulo de exploracao consistente com o tema.

Arquivos alvo:
- `frontend/app/(shell)/parlamentares/page.tsx`
- `frontend/components/parlamentares/ParlamentarCard.tsx`

Tarefas:
1. Aplicar barra de filtros no padrao visual politix.
2. Padronizar card de parlamentar com hierarquia forte (nome/cargo/partido/alinhamento).
3. Manter estados `loading/error/empty` no mesmo padrao da plataforma.
4. Eliminar estilos inline restantes.

Criterios de aceite:
- Leitura rapida da listagem com foco em nome + partido + alinhamento.
- Filtros legiveis e estaveis em todos os breakpoints.

---

## PR4 - Dossie (votos/projetos/gastos)
Objetivo: tornar o dossie o modulo mais fiel ao `ref-politix`.

Arquivos alvo:
- `frontend/app/(shell)/dossie/[id]/votos/page.tsx`
- `frontend/app/(shell)/dossie/[id]/projetos/page.tsx`
- `frontend/app/(shell)/dossie/[id]/gastos/page.tsx`
- `frontend/components/votes/VoteCard.tsx`
- `frontend/components/votes/TimelineVoteEntry.tsx`

Tarefas:
1. Estruturar pagina de votos em blocos "janela" (perfil/indicadores/listas/timeline).
2. Refatorar projetos para tabela-row com status e prioridade padronizados.
3. Refatorar gastos para blocos de metricas + fornecedores + timeline sem visual provisiorio.
4. Alinhar badges/tags para semantica unica (favoravel, contrario, controversia, outlier).

Criterios de aceite:
- Todas as subpaginas de dossie compartilham o mesmo vocabulário visual.
- Componentes de votos/gastos reutilizaveis sem duplicacao.

---

## PR5 - Dashboard, Propositions, Results, Budget, Interview
Objetivo: concluir migracao visual do restante do produto.

Arquivos alvo:
- `frontend/app/(shell)/dashboard/page.tsx`
- `frontend/app/(shell)/propositions/page.tsx`
- `frontend/app/(shell)/results/page.tsx`
- `frontend/app/(shell)/budget/page.tsx`
- `frontend/app/(shell)/interview/page.tsx`

Tarefas por pagina:
1. `dashboard`: faixa de indicadores + painel central + feed rapido em layout politix.
2. `propositions`: tabela com cabecalho, linhas e pesquisa no padrao de janelas.
3. `results`: radar/ranking com contraste e densidade visual consistentes.
4. `budget`: simulador com foco em leitura da soma e estado de validacao.
5. `interview`: fluxo de pergunta e resposta com CTA claro e sem salto visual.

Criterios de aceite:
- Todas as paginas compartilham mesmas regras de espacamento, tipografia e containers.
- Sem "ilhas" visuais desconectadas do tema principal.

---

## PR6 - Hardening visual + QA final
Objetivo: fechar consistencia, acessibilidade e manutencao.

Arquivos alvo:
- `frontend/app/globals.css`
- `frontend/components/**/*.tsx`
- `frontend/app/(shell)/**/*.tsx`

Tarefas:
1. Auditar contraste e focus-visible.
2. Remover restos de inline style e tokens nao usados.
3. Validar estados:
   - loading
   - error
   - empty
   - populated
4. Validar breakpoints:
   - 1440
   - 1280
   - 1024
   - 768
   - 390
5. Registrar guideline final de uso do tema.

Criterios de aceite:
- QA visual aprovado em todas as rotas shell.
- Sem regressao funcional nas rotas e interacoes.

## Backlog detalhado (task list)

Formato: `ID | Tipo | Escopo | Definicao de pronto`

- `UI-001 | refactor | globals.css tokens | tokens politix unicos e sem conflito`
- `UI-002 | refactor | globals.css classes | sem classes duplicadas .civic-*`
- `UI-003 | component | base window | componente visual equivalente a janela do ref`
- `UI-004 | component | tags/status | paleta semantica padronizada`
- `UI-005 | layout | shell | sidebar + top-nav consistentes`
- `UI-006 | page | /parlamentares | filtros e cards no padrao politix`
- `UI-007 | page | /dossie/[id]/votos | grid principal estilo ref-politix`
- `UI-008 | page | /dossie/[id]/projetos | tabela/rows padronizadas`
- `UI-009 | page | /dossie/[id]/gastos | metricas + fornecedores + timeline`
- `UI-010 | page | /dashboard | estrutura executiva padronizada`
- `UI-011 | page | /propositions | tabela e busca consistentes`
- `UI-012 | page | /results | visual de analise uniforme`
- `UI-013 | page | /budget | simulador com feedback claro`
- `UI-014 | page | /interview | fluxo de perguntas consistente`
- `UI-015 | qa | cross-page states | loading/error/empty/populated verificados`
- `UI-016 | qa | responsive | breakpoints validados`
- `UI-017 | docs | guideline | guia de manutencao visual publicado`

## Checklist de revisao por PR
- Nenhum estilo inline novo.
- Nenhuma variavel de cor hardcoded fora de tokens.
- Componentes reutilizados em vez de duplicacao de markup.
- Estado de hover/focus/active definido para elementos interativos.
- Verificacao em mobile e desktop antes do merge.

## Definicao final de concluido (DoD)
- 100% das paginas shell aderentes ao tema politix.
- CSS global sem conflitos de precedencia por duplicacao.
- Sistema visual documentado para manutencao por qualquer dev frontend.
