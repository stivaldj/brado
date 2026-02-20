"""Incremental sync for Câmara deputados snapshots and normalized table."""

import argparse
import json
import socket
import subprocess
import time
from hashlib import sha256
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from backend.database import CamaraSnapshot, DeputadoNormalizado, db_instance
from backend.normalize_deputados import map_deputado_payload
from backend.sync_status import write_sync_status

API_BASE = "https://dadosabertos.camara.leg.br/api/v2"
TIMEOUT_SECONDS = 20


def fetch_json(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Tuple[int, Dict[str, Any], Dict[str, str]]:
    query = f"?{urlencode(params, doseq=True)}" if params else ""
    url = f"{API_BASE}{endpoint}{query}"
    req = Request(url, headers={"Accept": "application/json", "User-Agent": "br-manifest-app/1.0"})
    attempts = 4
    for attempt in range(attempts):
        try:
            with urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                raw = resp.read().decode("utf-8")
                headers = {k: v for k, v in resp.headers.items()}
                return resp.status, (json.loads(raw) if raw else {}), headers
        except HTTPError as exc:
            raw = exc.read().decode("utf-8") if exc.fp is not None else ""
            try:
                body = json.loads(raw) if raw else {}
            except Exception:
                body = {}
            if exc.code in (429, 500, 502, 503, 504) and attempt < attempts - 1:
                time.sleep(0.6 * (attempt + 1))
                continue
            return exc.code, body, {}
        except (URLError, TimeoutError, socket.timeout):
            if attempt < attempts - 1:
                time.sleep(0.6 * (attempt + 1))
                continue
            break

    # Fallback for restricted environments where urllib networking is blocked.
    # Uses curl to keep sync viable under cron/sandbox constraints.
    try:
        cmd = ["curl", "-fsS", "--retry", "3", "--retry-delay", "1", url]
        raw = subprocess.check_output(cmd, timeout=TIMEOUT_SECONDS + 10).decode("utf-8")
        body = json.loads(raw) if raw else {}
        return 200, body, {}
    except Exception:
        return 0, {}, {}


def canonical_hash(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def fetch_all_deputados(itens_por_pagina: int = 100, max_pages: int = 20) -> List[Dict[str, Any]]:
    page = 1
    all_items: List[Dict[str, Any]] = []

    while page <= max_pages:
        status, body, _ = fetch_json(
            "/deputados",
            {"pagina": page, "itens": itens_por_pagina, "ordem": "ASC", "ordenarPor": "id"},
        )
        if status < 200 or status >= 300:
            raise RuntimeError(f"falha listagem deputados pagina={page} status={status}")
        dados = body.get("dados", []) if isinstance(body, dict) else []
        if not isinstance(dados, list) or not dados:
            break
        all_items.extend([item for item in dados if isinstance(item, dict)])
        if len(dados) < itens_por_pagina:
            break
        page += 1
        time.sleep(0.08)

    return all_items


def snapshots_by_id(endpoint: str) -> Dict[int, Dict[str, Any]]:
    rows = db_instance.list_camara_snapshots(endpoint=endpoint, limit=3000)
    out: Dict[int, Dict[str, Any]] = {}
    for row in rows:
        try:
            item_id = int(str(row.get("item_id")))
        except Exception:
            continue
        payload = row.get("payload")
        if isinstance(payload, dict):
            out[item_id] = payload
    return out


def normalized_ids() -> Set[int]:
    rows = db_instance.list_deputados_normalizados(limit=3000)
    out: Set[int] = set()
    for row in rows:
        dep_id = row.get("id")
        if isinstance(dep_id, int):
            out.add(dep_id)
    return out


def delete_removed_ids(removed_ids: Set[int]) -> Tuple[int, int, int]:
    if not removed_ids:
        return (0, 0, 0)

    deleted_normalizados = (
        db_instance.db.query(DeputadoNormalizado)
        .filter(DeputadoNormalizado.id.in_(sorted(removed_ids)))
        .delete(synchronize_session=False)
    )
    deleted_list = (
        db_instance.db.query(CamaraSnapshot)
        .filter(CamaraSnapshot.endpoint == "/deputados")
        .filter(CamaraSnapshot.item_id.in_([str(i) for i in sorted(removed_ids)]))
        .delete(synchronize_session=False)
    )
    deleted_detail = (
        db_instance.db.query(CamaraSnapshot)
        .filter(CamaraSnapshot.endpoint == "/deputados/{id}")
        .filter(CamaraSnapshot.item_id.in_([str(i) for i in sorted(removed_ids)]))
        .delete(synchronize_session=False)
    )
    db_instance.db.commit()
    return int(deleted_normalizados), int(deleted_list), int(deleted_detail)


def sync_deputados(delete_removed: bool = True, with_image: bool = False) -> Dict[str, int]:
    list_now = fetch_all_deputados(itens_por_pagina=100)
    list_now = [item for item in list_now if isinstance(item.get("id"), int)]
    current_ids: Set[int] = {int(item["id"]) for item in list_now}

    list_prev = snapshots_by_id("/deputados")
    detail_prev = snapshots_by_id("/deputados/{id}")

    list_new = 0
    list_changed = 0
    detail_new = 0
    detail_changed = 0
    normalized_upserts = 0

    for item in list_now:
        dep_id = int(item["id"])
        prev = list_prev.get(dep_id)
        if prev is None:
            list_new += 1
        elif canonical_hash(prev) != canonical_hash(item):
            list_changed += 1
        db_instance.upsert_camara_snapshot(
            endpoint="/deputados",
            item_id=str(dep_id),
            source_url=f"{API_BASE}/deputados",
            sort_value=str(dep_id),
            payload=json.dumps(item, ensure_ascii=False),
        )

    for dep_id in sorted(current_ids):
        status, body, _ = fetch_json(f"/deputados/{dep_id}")
        if status < 200 or status >= 300:
            continue
        payload = body.get("dados", body) if isinstance(body, dict) else body
        if not isinstance(payload, dict):
            continue

        prev = detail_prev.get(dep_id)
        is_new = prev is None
        is_changed = (not is_new) and canonical_hash(prev) != canonical_hash(payload)
        if is_new:
            detail_new += 1
        elif is_changed:
            detail_changed += 1

        if is_new or is_changed:
            db_instance.upsert_camara_snapshot(
                endpoint="/deputados/{id}",
                item_id=str(dep_id),
                source_url=f"{API_BASE}/deputados/{dep_id}",
                sort_value=str(dep_id),
                payload=json.dumps(payload, ensure_ascii=False),
            )
            mapped = map_deputado_payload(payload, with_image=with_image)
            db_instance.upsert_deputado_normalizado(dep_id, mapped)
            normalized_upserts += 1
        time.sleep(0.03)

    removed_ids: Set[int] = set()
    deleted_normalizados = 0
    deleted_list = 0
    deleted_detail = 0
    if delete_removed:
        removed_ids = normalized_ids() - current_ids
        deleted_normalizados, deleted_list, deleted_detail = delete_removed_ids(removed_ids)

    return {
        "current_ids": len(current_ids),
        "list_new": list_new,
        "list_changed": list_changed,
        "detail_new": detail_new,
        "detail_changed": detail_changed,
        "normalized_upserts": normalized_upserts,
        "removed_ids": len(removed_ids),
        "deleted_normalizados": deleted_normalizados,
        "deleted_list_snapshots": deleted_list,
        "deleted_detail_snapshots": deleted_detail,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync incremental de deputados")
    parser.add_argument("--with-image", action="store_true", help="Baixar e persistir imagem")
    parser.add_argument("--keep-removed", action="store_true", help="Nao remover deputados que sairam do mandato")
    args = parser.parse_args()

    started_at = time.time()
    try:
        summary = sync_deputados(delete_removed=not args.keep_removed, with_image=args.with_image)
        payload = {
            "ok": True,
            "started_at": started_at,
            "finished_at": time.time(),
            "duration_ms": int((time.time() - started_at) * 1000),
            "summary": summary,
        }
        write_sync_status(payload)
        print(json.dumps(summary, ensure_ascii=False))
    except Exception as exc:
        write_sync_status(
            {
                "ok": False,
                "started_at": started_at,
                "finished_at": time.time(),
                "duration_ms": int((time.time() - started_at) * 1000),
                "error": str(exc),
            }
        )
        raise


if __name__ == "__main__":
    main()
