#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

BACKEND_PORT="${BACKEND_PORT:-18000}"

echo "[smoke] subindo stack..."
docker compose up -d --build

echo "[smoke] aguardando backend /health..."
for i in {1..60}; do
  if curl -fsS "http://localhost:${BACKEND_PORT}/health" >/dev/null; then
    break
  fi
  sleep 2
done

curl -fsS "http://localhost:${BACKEND_PORT}/health" >/dev/null || {
  echo "[smoke] FAIL: /health indisponivel"
  exit 1
}

echo "[smoke] obtendo token..."
TOKEN_JSON="$(curl -fsS -X POST "http://localhost:${BACKEND_PORT}/api/v1/auth/token" -H "content-type: application/json" -d '{"client_id":"smoke-client"}')"
TOKEN="$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["access_token"])' <<< "$TOKEN_JSON")"

if [[ -z "${TOKEN}" ]]; then
  echo "[smoke] FAIL: token vazio"
  exit 1
fi

echo "[smoke] validando auth/me..."
HTTP_CODE="$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${BACKEND_PORT}/api/v1/auth/me" -H "authorization: Bearer ${TOKEN}")"
if [[ "${HTTP_CODE}" != "200" ]]; then
  echo "[smoke] FAIL: /api/v1/auth/me retornou ${HTTP_CODE}"
  exit 1
fi

echo "[smoke] PASS"
