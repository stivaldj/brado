#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import math
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass

BILLS_RE = re.compile(r"\[bills\s+(\d+)/(\d+)\b")
VOTES_RE = re.compile(r"\[votes\s+(\d+)/(\d+)\b")
EXPENSES_RE = re.compile(r"\[expenses\s+(\d+)/(\d+)\b")
TIMESTAMP_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z)\s?(.*)$")
TS_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"
TS_FMT_NO_MS = "%Y-%m-%dT%H:%M:%SZ"


def run(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout).strip() or f"command failed: {' '.join(cmd)}")
    return proc.stdout


def weeks_between(start: dt.date, end: dt.date) -> int:
    days = (end - start).days + 1
    return max(0, math.ceil(days / 7))


@dataclass
class ProgressSnapshot:
    done: int
    total: int
    stage: str
    status: str
    eta: str
    last_progress_age_s: float | None


def parse_ts(raw: str) -> dt.datetime | None:
    if raw.endswith("Z") and "." in raw:
        base, frac_z = raw.split(".", 1)
        frac = frac_z[:-1]
        frac = (frac[:6]).ljust(6, "0")
        raw = f"{base}.{frac}Z"
    for fmt in (TS_FMT, TS_FMT_NO_MS):
        try:
            return dt.datetime.strptime(raw, fmt).replace(tzinfo=dt.timezone.utc)
        except ValueError:
            continue
    return None


def find_backfill_container(compose_file: str) -> tuple[str | None, str]:
    out = run(["docker", "compose", "-f", compose_file, "ps", "-a"])
    lines = [line for line in out.splitlines() if line.strip()]
    if len(lines) <= 1:
        return None, "not_found"

    # Prefer running one-off backfill container.
    running = []
    exited = []
    for line in lines[1:]:
        name = line.split()[0]
        if "backend-run-" not in name:
            continue
        if "Up" in line:
            running.append(name)
        else:
            exited.append(name)

    if running:
        return running[-1], "running"
    if exited:
        return exited[-1], "exited"
    return None, "not_found"


def parse_progress(
    log_text: str,
    start: dt.date,
    end: dt.date,
    now_utc: dt.datetime,
    container_state: str,
    stuck_minutes: int,
) -> ProgressSnapshot:
    weeks = weeks_between(start, end)
    years = end.year - start.year + 1

    total_units = 1 + weeks + weeks + years
    done_deputados = 1 if "[deputados]" in log_text else 0

    bills_idx = 0
    votes_idx = 0
    expenses_idx = 0

    first_progress_ts = None
    last_progress_ts = None
    last_progress_units = 0
    events: list[tuple[dt.datetime, int]] = []

    for raw_line in log_text.splitlines():
        ts = None
        line = raw_line
        ts_match = TIMESTAMP_RE.match(raw_line)
        if ts_match:
            ts = parse_ts(ts_match.group(1))
            line = ts_match.group(2)

        m_bills = BILLS_RE.search(line)
        if m_bills:
            bills_idx = max(bills_idx, int(m_bills.group(1)))
        m_votes = VOTES_RE.search(line)
        if m_votes:
            votes_idx = max(votes_idx, int(m_votes.group(1)))
        m_expenses = EXPENSES_RE.search(line)
        if m_expenses:
            expenses_idx = max(expenses_idx, int(m_expenses.group(1)))

        if ts and ("[deputados]" in line or m_bills or m_votes or m_expenses):
            units = done_deputados + bills_idx + votes_idx + expenses_idx
            if not first_progress_ts:
                first_progress_ts = ts
            last_progress_ts = ts
            last_progress_units = units
            events.append((ts, units))

    if "Backfill completed." in log_text:
        return ProgressSnapshot(
            done=total_units,
            total=total_units,
            stage="completed",
            status="concluido",
            eta="0s",
            last_progress_age_s=0.0,
        )

    completed_units = done_deputados + bills_idx + votes_idx + expenses_idx

    if bills_idx < weeks:
        stage = f"bills {bills_idx}/{weeks}"
    elif votes_idx < weeks:
        stage = f"votes {votes_idx}/{weeks}"
    elif expenses_idx < years:
        stage = f"expenses {expenses_idx}/{years}"
    else:
        stage = "deputados"

    eta = "n/a"
    if len(events) >= 2:
        t0, u0 = events[0]
        t1, u1 = events[-1]
        dt_s = (t1 - t0).total_seconds()
        du = u1 - u0
        if dt_s > 0 and du > 0 and completed_units < total_units:
            rate = du / dt_s
            remaining = total_units - completed_units
            eta_s = int(remaining / rate)
            eta = str(dt.timedelta(seconds=eta_s))

    last_progress_age_s = None
    if last_progress_ts:
        last_progress_age_s = max(0.0, (now_utc - last_progress_ts).total_seconds())

    status = "rodando"
    if container_state == "exited":
        status = "parado"
    elif completed_units >= total_units:
        status = "concluido"
    elif last_progress_age_s is None:
        status = "sem progresso ainda"
    elif last_progress_age_s >= stuck_minutes * 60:
        status = "travado"

    return ProgressSnapshot(
        done=completed_units,
        total=total_units,
        stage=stage,
        status=status,
        eta=eta,
        last_progress_age_s=last_progress_age_s,
    )


def progress_bar(done: int, total: int, width: int = 40) -> str:
    if total <= 0:
        return "[" + ("-" * width) + "]"
    ratio = max(0.0, min(1.0, done / total))
    fill = int(ratio * width)
    return "[" + ("#" * fill) + ("-" * (width - fill)) + "]"


def main() -> int:
    parser = argparse.ArgumentParser(description="Monitor de progresso do backfill 2018+.")
    parser.add_argument("--compose-file", default="docker-compose.yml")
    parser.add_argument("--start", default="2018-01-01")
    parser.add_argument("--interval", type=float, default=5.0)
    parser.add_argument("--stuck-minutes", type=int, default=10)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    start = dt.date.fromisoformat(args.start)
    end = dt.date.today()

    while True:
        try:
            container, state = find_backfill_container(args.compose_file)
            if not container:
                msg = "nenhum container backend-run encontrado"
                line = msg
            else:
                logs = run(["docker", "logs", "--timestamps", container])
                snap = parse_progress(
                    logs,
                    start,
                    end,
                    now_utc=dt.datetime.now(dt.timezone.utc),
                    container_state=state,
                    stuck_minutes=args.stuck_minutes,
                )
                pct = (snap.done / snap.total * 100.0) if snap.total else 0.0
                bar_width = max(10, min(60, shutil.get_terminal_size((150, 20)).columns - 85))
                bar = progress_bar(snap.done, snap.total, bar_width)
                age = "n/a"
                if snap.last_progress_age_s is not None:
                    age = str(dt.timedelta(seconds=int(snap.last_progress_age_s)))
                line = (
                    f"{bar} {pct:6.2f}% ({snap.done}/{snap.total}) "
                    f"stage={snap.stage} status={snap.status} eta={snap.eta} "
                    f"ultimo_avanco={age} container={container}"
                )
        except Exception as exc:
            line = f"erro: {exc}"

        if args.once:
            print(line)
            return 0

        sys.stdout.write("\r" + line + " " * 8)
        sys.stdout.flush()
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
