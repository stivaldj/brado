#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-3000}"
MOCKS="${NEXT_PUBLIC_USE_MOCKS:-false}"

echo "[dev-clean] encerrando processos next dev antigos..."
pkill -f "next dev --webpack" >/dev/null 2>&1 || true
pkill -f "next/dist/bin/next dev" >/dev/null 2>&1 || true

if command -v lsof >/dev/null 2>&1; then
  PIDS="$(lsof -ti tcp:${PORT} -sTCP:LISTEN || true)"
  if [[ -n "${PIDS}" ]]; then
    echo "[dev-clean] liberando porta ${PORT}: ${PIDS}"
    kill -9 ${PIDS} >/dev/null 2>&1 || true
  fi
fi

if [[ -f .next/dev/lock ]]; then
  echo "[dev-clean] removendo lock stale .next/dev/lock"
  rm -f .next/dev/lock
fi

if command -v docker >/dev/null 2>&1; then
  if docker ps >/dev/null 2>&1; then
    CONTAINERS="$(docker ps --format '{{.ID}}\t{{.Ports}}' | awk -v p=":${PORT}" '$0 ~ p {print $1}')"
    if [[ -n "${CONTAINERS}" ]]; then
      echo "[dev-clean] parando containers na porta ${PORT}: ${CONTAINERS}"
      docker stop ${CONTAINERS} >/dev/null 2>&1 || true
    fi
  fi
fi

echo "[dev-clean] iniciando frontend em http://localhost:${PORT} (mocks=${MOCKS})"
NEXT_PUBLIC_USE_MOCKS="${MOCKS}" next dev --webpack --port "${PORT}"
