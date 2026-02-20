"""Populate local DB with recent data from Câmara API endpoints.

This script stores up to 10 recent records per OpenAPI endpoint
in the `camara_snapshots` table.
"""

import json
import socket
import time
from datetime import datetime
from hashlib import sha256
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from backend.database import db_instance


API_BASE = "https://dadosabertos.camara.leg.br/api/v2"
TIMEOUT_SECONDS = 10
MAX_ITEMS = 10

ORDERING_BY_ENDPOINT = {
    "/deputados": "id",
    "/eventos": "dataHoraInicio",
    "/proposicoes": "id",
    "/votacoes": "dataHoraRegistro",
    "/orgaos": "id",
    "/partidos": "id",
    "/blocos": "id",
    "/frentes": "id",
    "/grupos": "id",
    "/legislaturas": "id",
}


def fetch_json(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Tuple[int, Dict[str, Any]]:
    query = f"?{urlencode(params, doseq=True)}" if params else ""
    url = f"{API_BASE}{endpoint}{query}"
    req = Request(url, headers={"Accept": "application/json", "User-Agent": "br-manifest-app/1.0"})
    attempts = 3
    for attempt in range(attempts):
        try:
            with urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                raw = resp.read().decode("utf-8")
                return resp.status, json.loads(raw) if raw else {}
        except HTTPError as exc:
            raw = exc.read().decode("utf-8") if exc.fp is not None else ""
            try:
                body = json.loads(raw) if raw else {}
            except Exception:
                body = {}
            if exc.code in (429, 500, 502, 503, 504) and attempt < attempts - 1:
                time.sleep(0.4 * (attempt + 1))
                continue
            return exc.code, body
        except (URLError, TimeoutError, socket.timeout):
            if attempt < attempts - 1:
                time.sleep(0.4 * (attempt + 1))
                continue
            return 0, {}
    return 0, {}


def list_params_for(endpoint: str) -> Dict[str, Any]:
    params: Dict[str, Any] = {"itens": MAX_ITEMS, "pagina": 1}
    if endpoint == "/proposicoes":
        params["ano"] = datetime.utcnow().year
    if endpoint in ORDERING_BY_ENDPOINT:
        params["ordem"] = "desc"
        params["ordenarPor"] = ORDERING_BY_ENDPOINT[endpoint]
    return params


def extract_dados(body: dict[str, Any]) -> Any:
    if not isinstance(body, dict):
        return body
    return body.get("dados", body)


def as_item_id(item: Any, index: int) -> str:
    if isinstance(item, dict):
        if item.get("id") is not None:
            return str(item["id"])
        if item.get("uri") is not None:
            return str(item["uri"])
    digest = sha256(json.dumps(item, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return f"idx-{index}-{digest[:16]}"


def as_sort_value(item: Any) -> Optional[str]:
    if not isinstance(item, dict):
        return None
    for key in ("dataHoraRegistro", "dataHoraInicio", "data", "dataApresentacao", "id"):
        if item.get(key) is not None:
            return str(item[key])
    return None


def store_items(endpoint: str, source_url: str, payloads: list[Any]) -> int:
    stored = 0
    for idx, item in enumerate(payloads[:MAX_ITEMS]):
        db_instance.upsert_camara_snapshot(
            endpoint=endpoint,
            item_id=as_item_id(item, idx),
            source_url=source_url,
            sort_value=as_sort_value(item),
            payload=json.dumps(item, ensure_ascii=False),
        )
        stored += 1
    return stored


def fetch_collection(endpoint: str) -> tuple[int, dict[str, Any], str]:
    params = list_params_for(endpoint)
    status, body = fetch_json(endpoint, params)
    if status >= 400 and params:
        status, body = fetch_json(endpoint, {"itens": MAX_ITEMS, "pagina": 1})
        if status >= 400:
            status, body = fetch_json(endpoint, None)
            source_url = f"{API_BASE}{endpoint}"
        else:
            source_url = f"{API_BASE}{endpoint}?{urlencode({'itens': MAX_ITEMS, 'pagina': 1})}"
    else:
        source_url = f"{API_BASE}{endpoint}?{urlencode(params)}" if params else f"{API_BASE}{endpoint}"
    return status, body, source_url


def parent_endpoint(path: str) -> Optional[str]:
    token = "/{id}"
    if token not in path:
        return None
    return path.split(token, 1)[0]


def ids_from_parent(parent: str, cache: Dict[str, List[str]]) -> List[str]:
    if parent in cache:
        return cache[parent]
    status, body, _ = fetch_collection(parent)
    if status < 200 or status >= 300:
        cache[parent] = []
        return []
    dados = extract_dados(body)
    ids: list[str] = []
    if isinstance(dados, list):
        for item in dados[:MAX_ITEMS]:
            if isinstance(item, dict) and item.get("id") is not None:
                ids.append(str(item["id"]))
    elif isinstance(dados, dict) and dados.get("id") is not None:
        ids.append(str(dados["id"]))
    cache[parent] = ids[:MAX_ITEMS]
    return cache[parent]


def collect_paths() -> List[str]:
    status, spec = fetch_json("/api-docs")
    if status < 200 or status >= 300 or "paths" not in spec:
        raise RuntimeError("Nao foi possivel carregar /api-docs da Camara")
    return sorted(spec["paths"].keys())


def main() -> None:
    paths = collect_paths()
    parent_id_cache: Dict[str, List[str]] = {}
    stored_by_endpoint: Dict[str, int] = {}

    for idx, path in enumerate(paths, start=1):
        print(f"[{idx}/{len(paths)}] Processando {path}...")
        if "{id}" not in path:
            status, body, source_url = fetch_collection(path)
            if status < 200 or status >= 300:
                stored_by_endpoint[path] = 0
                continue
            dados = extract_dados(body)
            if isinstance(dados, list):
                stored_by_endpoint[path] = store_items(path, source_url, dados)
                ids = []
                for item in dados[:MAX_ITEMS]:
                    if isinstance(item, dict) and item.get("id") is not None:
                        ids.append(str(item["id"]))
                if ids:
                    parent_id_cache[path] = ids
            else:
                stored_by_endpoint[path] = store_items(path, source_url, [dados])
            time.sleep(0.08)
            continue

        if path.count("{") != 1 or "{id}" not in path:
            stored_by_endpoint[path] = 0
            continue

        parent = parent_endpoint(path)
        if not parent:
            stored_by_endpoint[path] = 0
            continue
        ids = ids_from_parent(parent, parent_id_cache)
        if not ids:
            stored_by_endpoint[path] = 0
            continue

        stored = 0
        for item_id in ids[:MAX_ITEMS]:
            endpoint = path.replace("{id}", item_id)
            status, body = fetch_json(endpoint)
            if status < 200 or status >= 300:
                continue
            dados = extract_dados(body)
            source_url = f"{API_BASE}{endpoint}"
            # For detail endpoints we store one record per requested id.
            db_instance.upsert_camara_snapshot(
                endpoint=path,
                item_id=str(item_id),
                source_url=source_url,
                sort_value=str(item_id),
                payload=json.dumps(dados, ensure_ascii=False),
            )
            stored += 1
            time.sleep(0.08)
        stored_by_endpoint[path] = stored

    total = sum(stored_by_endpoint.values())
    print(f"Endpoints processados: {len(paths)}")
    print(f"Registros gravados/atualizados: {total}")
    print("Resumo por endpoint:")
    for endpoint in sorted(stored_by_endpoint.keys()):
        print(f"{endpoint}: {stored_by_endpoint[endpoint]}")

    print("Contagem no banco:")
    counts = db_instance.camara_snapshot_counts()
    for endpoint in sorted(counts.keys()):
        print(f"{endpoint}: {counts[endpoint]}")


if __name__ == "__main__":
    main()
