#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-brado-staging}"
RELEASE="${RELEASE:-brado-analytics}"
REVISION="${1:-}"

if [[ -z "$REVISION" ]]; then
  echo "usage: $0 <revision>"
  exit 1
fi

helm rollback "$RELEASE" "$REVISION" --namespace "$NAMESPACE"
