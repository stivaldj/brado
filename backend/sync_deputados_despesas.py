"""Backfill/sync de despesas parlamentares por deputado (a partir de 2023)."""

import argparse
import json
import socket
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from backend.database import db_instance

API_BASE = "https://dadosabertos.camara.leg.br/api/v2"
TIMEOUT_SECONDS = 20
ITEMS_PER_PAGE = 100


def format_eta(seconds: float) -> str:
    total = max(0, int(seconds))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def render_progress(
    completed: int,
    total: int,
    started_at: float,
    api_items: int,
    failures: int,
    width: int = 28,
) -> None:
    safe_total = max(1, total)
    ratio = min(1.0, max(0.0, completed / safe_total))
    filled = int(ratio * width)
    bar = "#" * filled + "-" * (width - filled)
    pct = ratio * 100.0
    elapsed = max(0.001, time.time() - started_at)
    rate = completed / elapsed
    remaining = max(0, safe_total - completed)
    eta_seconds = remaining / rate if rate > 0 else 0
    line = (
        f"\r[{bar}] {pct:6.2f}%  "
        f"{completed}/{safe_total} dep-ano  "
        f"ETA {format_eta(eta_seconds)}  "
        f"itens_api={api_items}  falhas={failures}"
    )
    sys.stdout.write(line)
    sys.stdout.flush()


def fetch_json(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Tuple[int, Dict[str, Any]]:
    query = f"?{urlencode(params, doseq=True)}" if params else ""
    url = f"{API_BASE}{endpoint}{query}"
    req = Request(url, headers={"Accept": "application/json", "User-Agent": "br-manifest-app/1.0"})
    attempts = 4
    for attempt in range(attempts):
        try:
            with urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                raw = resp.read().decode("utf-8")
                return resp.status, (json.loads(raw) if raw else {})
        except HTTPError as exc:
            raw = exc.read().decode("utf-8") if exc.fp is not None else ""
            try:
                body = json.loads(raw) if raw else {}
            except Exception:
                body = {}
            if exc.code in (429, 500, 502, 503, 504) and attempt < attempts - 1:
                time.sleep(0.6 * (attempt + 1))
                continue
            return exc.code, body
        except (URLError, TimeoutError, socket.timeout):
            if attempt < attempts - 1:
                time.sleep(0.6 * (attempt + 1))
                continue
            return 0, {}
    return 0, {}


def get_deputado_ids(limit: Optional[int] = None) -> List[int]:
    rows = db_instance.list_deputados_normalizados(limit=3000)
    ids = sorted({int(row["id"]) for row in rows if isinstance(row.get("id"), int)})
    if limit is not None and limit > 0:
        return ids[:limit]
    return ids


def sync_deputado_year(
    deputado_id: int,
    ano: int,
    sleep_seconds: float = 0.03,
) -> Dict[str, int]:
    page = 1
    inserted_or_updated = 0
    total_api_items = 0
    failed_pages = 0

    while True:
        db_instance.upsert_deputado_despesa_sync_state(
            deputado_id=deputado_id,
            ano=ano,
            pagina_atual=page,
            status="running",
            erro=None,
        )
        status, body = fetch_json(
            f"/deputados/{deputado_id}/despesas",
            {
                "ano": ano,
                "itens": ITEMS_PER_PAGE,
                "pagina": page,
                "ordem": "ASC",
                "ordenarPor": "dataDocumento",
            },
        )
        if status < 200 or status >= 300:
            failed_pages += 1
            db_instance.upsert_deputado_despesa_sync_state(
                deputado_id=deputado_id,
                ano=ano,
                pagina_atual=page,
                status="error",
                erro=f"status={status}",
            )
            break

        dados = body.get("dados", []) if isinstance(body, dict) else []
        if not isinstance(dados, list):
            dados = []
        if not dados:
            db_instance.upsert_deputado_despesa_sync_state(
                deputado_id=deputado_id,
                ano=ano,
                pagina_atual=page,
                status="completed",
                erro=None,
            )
            break

        for item in dados:
            if not isinstance(item, dict):
                continue
            db_instance.upsert_deputado_despesa(deputado_id, item)
            inserted_or_updated += 1
        total_api_items += len(dados)

        if len(dados) < ITEMS_PER_PAGE:
            db_instance.upsert_deputado_despesa_sync_state(
                deputado_id=deputado_id,
                ano=ano,
                pagina_atual=page,
                status="completed",
                erro=None,
            )
            break

        page += 1
        time.sleep(max(0.0, sleep_seconds))

    return {
        "inserted_or_updated": inserted_or_updated,
        "total_api_items": total_api_items,
        "failed_pages": failed_pages,
    }


def sync_deputados_despesas(
    start_year: int = 2023,
    end_year: Optional[int] = None,
    limit_deputados: Optional[int] = None,
    sleep_seconds: float = 0.03,
    show_progress: bool = True,
) -> Dict[str, int]:
    year_end = end_year if end_year is not None else datetime.utcnow().year
    years = [year for year in range(start_year, year_end + 1)]
    deputado_ids = get_deputado_ids(limit=limit_deputados)

    total_dep_years = 0
    total_inserted_or_updated = 0
    total_api_items = 0
    total_failed_pages = 0
    completed_dep_years = 0
    started_at = time.time()
    total_work = len(deputado_ids) * len(years)

    for dep_id in deputado_ids:
        for ano in years:
            total_dep_years += 1
            summary = sync_deputado_year(dep_id, ano, sleep_seconds=sleep_seconds)
            total_inserted_or_updated += summary["inserted_or_updated"]
            total_api_items += summary["total_api_items"]
            total_failed_pages += summary["failed_pages"]
            completed_dep_years += 1
            if show_progress:
                render_progress(
                    completed=completed_dep_years,
                    total=total_work,
                    started_at=started_at,
                    api_items=total_api_items,
                    failures=total_failed_pages,
                )

    if show_progress:
        sys.stdout.write("\n")
        sys.stdout.flush()

    return {
        "deputados_processados": len(deputado_ids),
        "anos_processados_por_deputado": len(years),
        "dep_ano_processados": total_dep_years,
        "api_items_lidos": total_api_items,
        "linhas_insert_or_update": total_inserted_or_updated,
        "paginas_falhas": total_failed_pages,
        "despesas_total_armazenadas": db_instance.count_deputado_despesas(ano_min=start_year),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync de despesas parlamentares por deputado")
    parser.add_argument("--start-year", type=int, default=2023, help="Ano inicial (inclusive)")
    parser.add_argument("--end-year", type=int, default=None, help="Ano final (inclusive); default=ano atual")
    parser.add_argument("--limit-deputados", type=int, default=None, help="Limita quantidade de deputados para testes")
    parser.add_argument("--sleep", type=float, default=0.03, help="Intervalo entre páginas (segundos)")
    parser.add_argument("--no-progress", action="store_true", help="Desativa barra de progresso")
    args = parser.parse_args()

    show_progress = (not args.no_progress) and sys.stdout.isatty()
    summary = sync_deputados_despesas(
        start_year=max(2000, args.start_year),
        end_year=args.end_year,
        limit_deputados=args.limit_deputados,
        sleep_seconds=max(0.0, args.sleep),
        show_progress=show_progress,
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
