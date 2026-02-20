from __future__ import annotations

import argparse
from datetime import date, timedelta
import multiprocessing as mp
import os
import socket
import time
import traceback
from typing import Any
from urllib.parse import urlparse

from app.db.sql import session_scope
from app.jobs.ingest_jobs import IngestJobs


def week_windows(start: date, end: date) -> list[tuple[date, date]]:
    windows: list[tuple[date, date]] = []
    cursor = start
    while cursor <= end:
        window_end = min(cursor + timedelta(days=6), end)
        windows.append((cursor, window_end))
        cursor = window_end + timedelta(days=1)
    return windows


def year_windows(start: date, end: date) -> list[tuple[date, date]]:
    windows: list[tuple[date, date]] = []
    for year in range(start.year, end.year + 1):
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)
        windows.append((max(start, year_start), min(end, year_end)))
    return windows


def _host_port_from_database_url(raw: str) -> tuple[str, int]:
    normalized = raw.replace("+psycopg", "")
    parsed = urlparse(normalized)
    host = parsed.hostname or "postgres"
    port = parsed.port or 5432
    return host, port


def _host_port_from_neo4j_uri(raw: str) -> tuple[str, int]:
    parsed = urlparse(raw)
    host = parsed.hostname or "neo4j"
    port = parsed.port or 7687
    return host, port


def _wait_tcp(host: str, port: int, timeout_seconds: int, label: str) -> None:
    deadline = time.time() + timeout_seconds
    last_err = "timeout"
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=3):
                print(f"[deps] {label} ready at {host}:{port}", flush=True)
                return
        except Exception as exc:
            last_err = str(exc)
            time.sleep(2)
    raise RuntimeError(f"{label} not ready at {host}:{port} after {timeout_seconds}s: {last_err}")


def wait_for_dependencies(timeout_seconds: int) -> None:
    db_host, db_port = _host_port_from_database_url(os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/brado"))
    neo_host, neo_port = _host_port_from_neo4j_uri(os.getenv("NEO4J_URI", "bolt://neo4j:7687"))
    _wait_tcp(db_host, db_port, timeout_seconds, "postgres")
    _wait_tcp(neo_host, neo_port, timeout_seconds, "neo4j")


def _worker_run_job(queue: mp.Queue, job_kind: str, start: date, end: date, force_serial: bool) -> None:
    try:
        if force_serial:
            os.environ["CAMARA_MAX_CONCURRENCY"] = "1"
            os.environ["CAMARA_MAX_RPS"] = "1"

        with session_scope() as session:
            jobs = IngestJobs(session)
            try:
                if job_kind == "deputados":
                    result = jobs.ingest_deputados_current()
                elif job_kind == "bills":
                    result = jobs.ingest_bills_since(start, to_date=end)
                elif job_kind == "votes":
                    result = jobs.ingest_votes_since(start, to_date=end)
                elif job_kind == "expenses":
                    result = jobs.ingest_expenses_since(start, to_date=end)
                else:
                    raise ValueError(f"Unknown job kind: {job_kind}")
                queue.put({"ok": True, "result": result})
            finally:
                jobs.close()
    except Exception as exc:
        queue.put({"ok": False, "error": str(exc), "traceback": traceback.format_exc()})


def _run_with_watchdog(
    job_kind: str,
    start: date,
    end: date,
    *,
    timeout_seconds: int,
    retries: int,
) -> dict[str, Any]:
    last_error: str | None = None
    for attempt in range(1, retries + 1):
        force_serial = attempt > 1
        queue: mp.Queue = mp.Queue()
        proc = mp.Process(target=_worker_run_job, args=(queue, job_kind, start, end, force_serial))
        proc.start()
        proc.join(timeout_seconds)

        if proc.is_alive():
            proc.terminate()
            proc.join()
            last_error = (
                f"timeout after {timeout_seconds}s (attempt {attempt}/{retries}, "
                f"{'serial' if force_serial else 'parallel'})"
            )
            print(f"[watchdog] {job_kind} {start}..{end} {last_error}", flush=True)
            time.sleep(min(5, attempt))
            continue

        if queue.empty():
            last_error = f"worker exited without result (attempt {attempt}/{retries})"
            print(f"[watchdog] {job_kind} {start}..{end} {last_error}", flush=True)
            time.sleep(min(5, attempt))
            continue

        payload = queue.get()
        if payload.get("ok"):
            if attempt > 1:
                print(
                    f"[watchdog] {job_kind} {start}..{end} recovered on attempt {attempt}/{retries} "
                    f"({'serial' if force_serial else 'parallel'})",
                    flush=True,
                )
            return payload["result"]

        last_error = payload.get("error", "unknown error")
        print(
            f"[watchdog] {job_kind} {start}..{end} failed attempt {attempt}/{retries}: {last_error}",
            flush=True,
        )
        time.sleep(min(5, attempt))

    raise RuntimeError(f"{job_kind} {start}..{end} failed after {retries} attempts: {last_error}")


def run_deputados(timeout_seconds: int, retries: int) -> None:
    today = date.today()
    result = _run_with_watchdog("deputados", today, today, timeout_seconds=timeout_seconds, retries=retries)
    print(f"[deputados] {result}", flush=True)


def run_bills(start: date, end: date, timeout_seconds: int, retries: int) -> None:
    windows = week_windows(start, end)
    for idx, (w_start, w_end) in enumerate(windows, start=1):
        print(f"[bills {idx}/{len(windows)} {w_start}..{w_end}] start", flush=True)
        result = _run_with_watchdog("bills", w_start, w_end, timeout_seconds=timeout_seconds, retries=retries)
        print(f"[bills {idx}/{len(windows)} {w_start}..{w_end}] processed={result.get('processed')}", flush=True)


def run_votes(start: date, end: date, timeout_seconds: int, retries: int) -> None:
    windows = week_windows(start, end)
    for idx, (w_start, w_end) in enumerate(windows, start=1):
        print(f"[votes {idx}/{len(windows)} {w_start}..{w_end}] start", flush=True)
        result = _run_with_watchdog("votes", w_start, w_end, timeout_seconds=timeout_seconds, retries=retries)
        print(
            f"[votes {idx}/{len(windows)} {w_start}..{w_end}] events={result.get('events')} actions={result.get('actions')}",
            flush=True,
        )


def run_expenses(start: date, end: date, timeout_seconds: int, retries: int) -> None:
    windows = year_windows(start, end)
    for idx, (w_start, w_end) in enumerate(windows, start=1):
        print(f"[expenses {idx}/{len(windows)} {w_start}..{w_end}] start", flush=True)
        result = _run_with_watchdog("expenses", w_start, w_end, timeout_seconds=timeout_seconds, retries=retries)
        print(
            f"[expenses {idx}/{len(windows)} {w_start}..{w_end}] processed={result.get('processed')} fallback={result.get('fallback_rows')}",
            flush=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill Câmara desde 2018 com watchdog anti-travamento.")
    parser.add_argument("--start", default="2018-01-01")
    parser.add_argument("--end", default=date.today().isoformat())
    parser.add_argument("--window-timeout-minutes", type=int, default=20)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--wait-deps-seconds", type=int, default=180)
    parser.add_argument("--force-deputados", action="store_true")
    args = parser.parse_args()

    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)
    timeout_seconds = max(60, int(args.window_timeout_minutes * 60))
    print(f"Backfill start: {start} .. {end}", flush=True)
    print(
        f"Watchdog: timeout={timeout_seconds}s retries={args.retries} (retry>=2 usa serial CAMARA_MAX_CONCURRENCY=1)",
        flush=True,
    )
    wait_for_dependencies(args.wait_deps_seconds)

    if args.force_deputados:
        run_deputados(timeout_seconds=timeout_seconds, retries=args.retries)
    else:
        print("[deputados] skipped (use --force-deputados para executar)", flush=True)
    run_bills(start, end, timeout_seconds=timeout_seconds, retries=args.retries)
    run_votes(start, end, timeout_seconds=timeout_seconds, retries=args.retries)
    run_expenses(start, end, timeout_seconds=timeout_seconds, retries=args.retries)

    print("Backfill completed.", flush=True)


if __name__ == "__main__":
    main()
