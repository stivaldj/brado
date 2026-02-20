#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:3100}"
export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
export PWCLI="$CODEX_HOME/skills/playwright/scripts/playwright_cli.sh"

if ! command -v npx >/dev/null 2>&1; then
  echo "npx não encontrado. Instale Node.js/npm para executar o smoke playwright." >&2
  exit 1
fi

if [[ ! -x "$PWCLI" ]]; then
  echo "Wrapper do Playwright não encontrado em $PWCLI" >&2
  exit 1
fi

assert_true() {
  local expr="$1"
  local tries=0
  local out=""
  while [[ $tries -lt 20 ]]; do
    out="$($PWCLI eval "$expr")"
    if [[ "$out" == *"true"* ]]; then
      return 0
    fi
    tries=$((tries + 1))
    sleep 0.3
  done
  echo "Assertion falhou para expressão: $expr" >&2
  echo "Saída: $out" >&2
  exit 1
}

"$PWCLI" open "$BASE_URL"
assert_true "document.body.innerText.includes('Painel Analítico Legislativo')"

"$PWCLI" goto "$BASE_URL/parlamentares"
assert_true "document.body.innerText.includes('Parlamentares')"
assert_true "document.querySelectorAll('[role=\"button\"]').length > 0"

"$PWCLI" goto "$BASE_URL/dossie/mendes/votos"
assert_true "document.body.innerText.includes('Dossiê') || document.body.innerText.includes('Dossie')"
assert_true "document.querySelectorAll('[role=\"button\"]').length >= 6"

"$PWCLI" goto "$BASE_URL/propositions"
assert_true "document.body.innerText.includes('Proposições')"

"$PWCLI" goto "$BASE_URL/results"
assert_true "document.body.innerText.includes('Resultados')"

"$PWCLI" close

echo "Smoke playwright concluído com sucesso."
