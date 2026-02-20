#!/usr/bin/env bash
set -euo pipefail

# Full pipeline:
# 1) Download all deputados (list + details) from Câmara API
# 2) Upsert snapshots into local DB
# 3) Normalize to deputados_normalizados
# 4) Remove known synthetic test IDs
# 5) Print final counts

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="${TMP_DIR:-/tmp/camara513}"
DETAILS_DIR="$TMP_DIR/details"
LIMIT="${LIMIT:-513}"
ITEMS_PER_PAGE="${ITEMS_PER_PAGE:-100}"
DOWNLOAD="${DOWNLOAD:-true}"
WITH_IMAGE="${WITH_IMAGE:-false}"
CLEAN_TEST_IDS="${CLEAN_TEST_IDS:-true}"

echo "[load-513] root=$ROOT_DIR"
echo "[load-513] limit=$LIMIT items_per_page=$ITEMS_PER_PAGE download=$DOWNLOAD with_image=$WITH_IMAGE"

mkdir -p "$TMP_DIR" "$DETAILS_DIR"

if [[ "$DOWNLOAD" == "true" ]]; then
  echo "[load-513] downloading paginated /deputados list..."
  rm -f "$TMP_DIR"/page-*.json "$TMP_DIR"/ids.txt
  rm -f "$DETAILS_DIR"/*.json 2>/dev/null || true

  for p in 1 2 3 4 5 6 7 8 9 10; do
    url="https://dadosabertos.camara.leg.br/api/v2/deputados?pagina=$p&itens=$ITEMS_PER_PAGE&ordem=ASC&ordenarPor=id"
    file="$TMP_DIR/page-$p.json"
    curl -fsS --retry 3 --retry-delay 1 "$url" > "$file"
    count="$(python3 -c "import json,sys;print(len(json.load(open(sys.argv[1],encoding='utf-8')).get('dados',[])))" "$file")"
    echo "[load-513] page=$p count=$count"
    if [[ "$count" -lt "$ITEMS_PER_PAGE" ]]; then
      break
    fi
  done

  python3 - <<'PY'
import glob
import json
import os

tmp_dir = os.environ["TMP_DIR"]
limit = int(os.environ["LIMIT"])

ids = []
for path in sorted(glob.glob(os.path.join(tmp_dir, "page-*.json"))):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for item in data.get("dados", []):
        dep_id = item.get("id")
        if isinstance(dep_id, int):
            ids.append(dep_id)

ids = sorted(set(ids))[:limit]
with open(os.path.join(tmp_dir, "ids.txt"), "w", encoding="utf-8") as f:
    for dep_id in ids:
        f.write(f"{dep_id}\n")

print(f"[load-513] ids_total={len(ids)}")
PY

  echo "[load-513] downloading /deputados/{id} details..."
  n=0
  while IFS= read -r id; do
    curl -fsS --retry 3 --retry-delay 1 "https://dadosabertos.camara.leg.br/api/v2/deputados/$id" > "$DETAILS_DIR/$id.json"
    n=$((n + 1))
    if [[ $((n % 50)) -eq 0 ]]; then
      echo "[load-513] details_downloaded=$n"
    fi
  done < "$TMP_DIR/ids.txt"
  echo "[load-513] details_downloaded_total=$n"
else
  echo "[load-513] skipping download (DOWNLOAD=false)"
fi

echo "[load-513] importing snapshots into DB..."
PYTHONDONTWRITEBYTECODE=1 TMP_DIR="$TMP_DIR" python3 - <<'PY'
import glob
import json
import os

from backend.database import db_instance

tmp_dir = os.environ["TMP_DIR"]
detail_dir = os.path.join(tmp_dir, "details")

list_count = 0
for path in sorted(glob.glob(os.path.join(tmp_dir, "page-*.json"))):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for item in data.get("dados", []):
        dep_id = item.get("id")
        if dep_id is None:
            continue
        db_instance.upsert_camara_snapshot(
            endpoint="/deputados",
            item_id=str(dep_id),
            source_url="https://dadosabertos.camara.leg.br/api/v2/deputados",
            sort_value=str(dep_id),
            payload=json.dumps(item, ensure_ascii=False),
        )
        list_count += 1

detail_count = 0
for path in sorted(glob.glob(os.path.join(detail_dir, "*.json"))):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    payload = data.get("dados", data)
    dep_id = payload.get("id") if isinstance(payload, dict) else None
    if dep_id is None:
        continue
    db_instance.upsert_camara_snapshot(
        endpoint="/deputados/{id}",
        item_id=str(dep_id),
        source_url=f"https://dadosabertos.camara.leg.br/api/v2/deputados/{dep_id}",
        sort_value=str(dep_id),
        payload=json.dumps(payload, ensure_ascii=False),
    )
    detail_count += 1

print(f"[load-513] upserted_list={list_count}")
print(f"[load-513] upserted_detail={detail_count}")
PY

echo "[load-513] normalizing deputados..."
if [[ "$WITH_IMAGE" == "true" ]]; then
  PYTHONDONTWRITEBYTECODE=1 python3 -m backend.normalize_deputados --limit "$LIMIT"
else
  PYTHONDONTWRITEBYTECODE=1 python3 -m backend.normalize_deputados --limit "$LIMIT" --no-image
fi

if [[ "$CLEAN_TEST_IDS" == "true" ]]; then
  echo "[load-513] cleaning synthetic test IDs (999001, 999777)..."
  PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from backend.database import db_instance, DeputadoNormalizado
deleted = db_instance.db.query(DeputadoNormalizado).filter(DeputadoNormalizado.id.in_([999001, 999777])).delete(synchronize_session=False)
db_instance.db.commit()
print(f"[load-513] deleted_normalizados={deleted}")
PY
fi

echo "[load-513] final counts..."
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from backend.database import db_instance
print("[load-513] snapshots_/deputados=", len(db_instance.list_camara_snapshots(endpoint="/deputados", limit=2000)))
print("[load-513] snapshots_/deputados/{id}=", len(db_instance.list_camara_snapshots(endpoint="/deputados/{id}", limit=2000)))
print("[load-513] normalizados=", len(db_instance.list_deputados_normalizados(limit=2000)))
PY

echo "[load-513] done."
