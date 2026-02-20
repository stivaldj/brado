# Plano de Normalizacao de Deputados (com Imagem)

## Objetivo
Criar uma tabela relacional de deputados para consultas rapidas no app, mantendo compatibilidade com snapshots brutos da API.

## Fonte
- Endpoint detalhado: `/deputados/{id}`
- Snapshot bruto salvo em `camara_snapshots` (`endpoint = '/deputados/{id}'`)

## Campos normalizados
- Identificacao: `id`, `uri`, `nome_civil`, `cpf`, `sexo`
- Dados pessoais: `data_nascimento`, `data_falecimento`, `uf_nascimento`, `municipio_nascimento`, `escolaridade`
- Status atual: `status_nome`, `status_nome_eleitoral`, `status_sigla_partido`, `status_sigla_uf`, `status_id_legislatura`, `status_situacao`, `status_condicao_eleitoral`, `status_data`, `status_email`
- Gabinete: `gabinete_nome`, `gabinete_predio`, `gabinete_sala`, `gabinete_andar`, `gabinete_telefone`, `gabinete_email`
- Redes/website: `url_website`, `rede_social_json`

## Imagem (incluida no plano)
- `foto_url`: URL oficial da foto (`ultimoStatus.urlFoto`)
- `foto_bytes`: binario da imagem baixada da URL
- `foto_sha256`: hash do binario para deduplicacao e auditoria
- `foto_content_type`: MIME retornado no download

## Fluxo de carga
1. Ler snapshots de deputados detalhados.
2. Transformar payload JSON em colunas normalizadas.
3. Tentar baixar a foto; se falhar, manter apenas `foto_url`.
4. Executar upsert por `id`.

## Observacoes
- O snapshot bruto continua sendo a fonte de auditoria.
- A tabela normalizada privilegia leitura rapida para frontend e filtros SQL.
