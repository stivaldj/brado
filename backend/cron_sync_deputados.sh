#!/usr/bin/env bash
set -euo pipefail

# Cron-safe wrapper for deputados sync with lock + logs.
# Example crontab (every 30 minutes):
# */30 * * * * cd /path/to/br_manifest_app && ./backend/cron_sync_deputados.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${ROOT_DIR}/backend/logs"
LOCK_FILE="/tmp/br_manifest_sync_deputados.lock"
LOCK_DIR="/tmp/br_manifest_sync_deputados.lockdir"
LOG_FILE="${LOG_DIR}/sync_deputados.log"

mkdir -p "${LOG_DIR}"

run_sync() {
  echo "$(date -Is) [cron-sync] start" >> "${LOG_FILE}"
  cd "${ROOT_DIR}"
  PYTHONDONTWRITEBYTECODE=1 python3 -m backend.sync_deputados >> "${LOG_FILE}" 2>&1
  status=$?
  echo "$(date -Is) [cron-sync] end status=${status}" >> "${LOG_FILE}"
  return ${status}
}

if command -v flock >/dev/null 2>&1; then
  (
    flock -n 9 || {
      echo "$(date -Is) [cron-sync] skipped: another sync is running" >> "${LOG_FILE}"
      exit 0
    }
    run_sync
  ) 9>"${LOCK_FILE}"
else
  if mkdir "${LOCK_DIR}" 2>/dev/null; then
    trap 'rmdir "${LOCK_DIR}" >/dev/null 2>&1 || true' EXIT
    run_sync
  else
    echo "$(date -Is) [cron-sync] skipped: another sync is running" >> "${LOG_FILE}"
    exit 0
  fi
fi
