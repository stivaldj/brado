#!/usr/bin/env bash
set -euo pipefail

# Instala (ou atualiza) entrada de cron para sync de deputados.
# Uso:
#   ./backend/install_cron_sync.sh "*/30 * * * *"
#   ./backend/install_cron_sync.sh "10 3 * * *"

SCHEDULE="${1:-*/30 * * * *}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CMD="cd ${ROOT_DIR// /\\ } && ./backend/cron_sync_deputados.sh"
TAG="# br_manifest_sync_deputados"
LINE="${SCHEDULE} ${CMD} ${TAG}"

TMP_FILE="$(mktemp)"
crontab -l 2>/dev/null | grep -v "${TAG}" > "${TMP_FILE}" || true
echo "${LINE}" >> "${TMP_FILE}"
crontab "${TMP_FILE}"
rm -f "${TMP_FILE}"

echo "[install-cron] instalado:"
echo "${LINE}"
