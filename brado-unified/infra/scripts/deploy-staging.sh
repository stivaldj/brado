#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-brado-staging}"
RELEASE="${RELEASE:-brado-analytics}"
CHART="deploy/helm/brado-analytics"

helm upgrade --install "$RELEASE" "$CHART" \
  --namespace "$NAMESPACE" \
  --create-namespace \
  --set image.tag="${IMAGE_TAG:-latest}"
