"""Populate all deputados snapshots from Câmara API.

This script fetches the full deputados list with pagination and then fetches
individual detail payloads for each deputado ID, storing both into
`camara_snapshots` using endpoints `/deputados` and `/deputados/{id}`.
"""

import argparse
import json
import socket
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from backend.database import db_instance

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
            return 0, {}, {}
    return 0, {}, {}


def extract_dados(body: Dict[str, Any]) -> List[Dict[str, Any]]:
    dados = body.get("dados", []) if isinstance(body, dict) else []
    if isinstance(dados, list):
        return [item for item in dados if isinstance(item, dict)]
    return []


def fetch_all_deputados(itens_por_pagina: int) -> List[Dict[str, Any]]:
    page = 1
    all_items: List[Dict[str, Any]] = []

    while True:
        status, body, headers = fetch_json("/deputados", {"pagina": page, "itens": itens_por_pagina, "ordem": "ASC", "ordenarPor": "id"})
        if status < 200 or status >= 300:
            print(f"falha listagem deputados pagina={page} status={status}")
            break

        items = extract_dados(body)
        if not items:
            break

        all_items.extend(items)
        total_hint = headers.get("X-Total-Count")
        print(f"listagem pagina={page} itens={len(items)} acumulado={len(all_items)} total_hint={total_hint or '?'}")

        if len(items) < itens_por_pagina:
            break
        page += 1
        time.sleep(0.08)

    return all_items


def store_list_snapshot(items: List[Dict[str, Any]]) -> int:
    stored = 0
    source_url = f"{API_BASE}/deputados"
    for item in items:
        dep_id = item.get("id")
        if dep_id is None:
            continue
        db_instance.upsert_camara_snapshot(
            endpoint="/deputados",
            item_id=str(dep_id),
            source_url=source_url,
            sort_value=str(dep_id),
            payload=json.dumps(item, ensure_ascii=False),
        )
        stored += 1
    return stored


def store_detail_snapshots(ids: List[int], delay_seconds: float) -> Tuple[int, int]:
    ok = 0
    fail = 0
    total = len(ids)

    for idx, dep_id in enumerate(ids, start=1):
        status, body, _ = fetch_json(f"/deputados/{dep_id}")
        if status < 200 or status >= 300:
            fail += 1
            print(f"[{idx}/{total}] falha detalhe deputado={dep_id} status={status}")
            continue

        payload = body.get("dados", body) if isinstance(body, dict) else body
        db_instance.upsert_camara_snapshot(
            endpoint="/deputados/{id}",
            item_id=str(dep_id),
            source_url=f"{API_BASE}/deputados/{dep_id}",
            sort_value=str(dep_id),
            payload=json.dumps(payload, ensure_ascii=False),
        )
        ok += 1

        if idx % 25 == 0 or idx == total:
            print(f"[{idx}/{total}] detalhes ok={ok} falhas={fail}")

        if delay_seconds > 0:
            time.sleep(delay_seconds)

    return ok, fail


def main() -> None:
    parser = argparse.ArgumentParser(description="Popula snapshots completos de deputados")
    parser.add_argument("--limit", type=int, default=513, help="Quantidade máxima de deputados")
    parser.add_argument("--itens-por-pagina", type=int, default=100, help="Itens por página na listagem")
    parser.add_argument("--delay", type=float, default=0.05, help="Delay entre requisições de detalhe")
    args = parser.parse_args()

    deputados = fetch_all_deputados(max(1, args.itens_por_pagina))
    if not deputados:
        print("nenhum deputado retornado pela API")
        return

    deputados = deputados[: max(1, args.limit)]
    ids = [int(item["id"]) for item in deputados if item.get("id") is not None]

    stored_list = store_list_snapshot(deputados)
    print(f"snapshot /deputados gravados={stored_list}")

    ok, fail = store_detail_snapshots(ids, max(0.0, args.delay))
    print(f"snapshot /deputados/{{id}} ok={ok} falhas={fail}")


if __name__ == "__main__":
    main()
