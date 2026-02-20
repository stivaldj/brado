# Guia: habilitar cronjob sem falha de DNS

Este guia reduz falhas como:
- `Could not resolve host: dadosabertos.camara.leg.br`
- execução do cron sem PATH/env corretos
- job rodando antes da rede estar pronta

## 1) Pré-requisitos

Confirme que os scripts já existem e são executáveis:

```bash
chmod +x backend/cron_sync_deputados.sh backend/install_cron_sync.sh
```

## 2) Validar DNS fora do cron

Teste resolução e acesso HTTP manualmente:

```bash
getent hosts dadosabertos.camara.leg.br || nslookup dadosabertos.camara.leg.br
curl -I 'https://dadosabertos.camara.leg.br/api/v2/deputados?itens=1'
```

Se isso falhar, o problema é de rede/DNS do host (não do Python).

## 3) Configure resolvers estáveis no host

Use resolvers públicos confiáveis no sistema (exemplos):
- `1.1.1.1` e `1.0.0.1` (Cloudflare)
- `8.8.8.8` e `8.8.4.4` (Google)

Verifique `/etc/resolv.conf` (ou equivalente do seu SO) e garanta que ele é persistente no boot.

## 4) Garanta ambiente mínimo no cron

Abra o crontab:

```bash
crontab -e
```

Adicione no topo:

```cron
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
```

## 5) Instale o job com o script idempotente

A cada 30 minutos:

```bash
./backend/install_cron_sync.sh "*/30 * * * *"
```

Ou diário às 03:10:

```bash
./backend/install_cron_sync.sh "10 3 * * *"
```

## 6) Versão recomendada com pré-check DNS

Se quiser máxima robustez, use esta linha no `crontab -e` (substitui a linha instalada):

```cron
*/30 * * * * cd /Users/joseoliveira/CODING/bradoretumbante\ 2/br_manifest_app && (getent hosts dadosabertos.camara.leg.br >/dev/null 2>&1 || nslookup dadosabertos.camara.leg.br >/dev/null 2>&1) && ./backend/cron_sync_deputados.sh >> backend/logs/sync_deputados.log 2>&1
```

Assim, se o DNS estiver indisponível no minuto exato, o job não quebra a execução com erro “host not found”.

## 7) Verificação pós-instalação

Checar cron instalado:

```bash
crontab -l | grep br_manifest_sync_deputados
```

Rodar manualmente uma vez:

```bash
./backend/cron_sync_deputados.sh
```

Monitorar logs:

```bash
tail -f backend/logs/sync_deputados.log
```

## 8) Troubleshooting rápido

1. `Could not resolve host`:
- confirme DNS do host (`nslookup`/`getent`)
- confirme `/etc/resolv.conf`
- teste de dentro do usuário que roda cron

2. `python3: command not found`:
- ajuste `PATH` no crontab
- ou use caminho absoluto do Python

3. Job não dispara:
- valide serviço cron ativo
- confira timezone e sintaxe do crontab

4. Conflito de execução paralela:
- já tratado no script com lock (`flock` + fallback lock dir)

## 9) Boas práticas operacionais

- mantenha rotação de logs (`logrotate`) para `backend/logs/sync_deputados.log`
- mantenha um alerta se o log ficar sem atualização por mais de 2 ciclos
- execute `sync` manual após manutenção de rede/DNS
