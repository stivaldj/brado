from __future__ import annotations

import hashlib
from datetime import date, datetime
from typing import Any


def _safe(v: Any) -> str:
    return str(v).strip()


def person_id(id_deputado: Any) -> str:
    return f"camara:person:{_safe(id_deputado)}"


def bill_id(id_proposicao: Any) -> str:
    return f"camara:bill:{_safe(id_proposicao)}"


def vote_event_id(id_votacao: Any) -> str:
    return f"camara:vote_event:{_safe(id_votacao)}"


def vote_action_id(vote_event: str, person: str) -> str:
    return f"camara:vote_action:{vote_event}:{person}"


def expense_id(source_row: Any) -> str:
    raw = _safe(source_row)
    if not raw:
        raw = hashlib.sha256(str(source_row).encode("utf-8")).hexdigest()[:24]
    return f"camara:expense:{raw}"


def organization_id(name_or_id: Any) -> str:
    normalized = " ".join(_safe(name_or_id).upper().split())
    if not normalized:
        normalized = "UNKNOWN"
    return f"camara:org:{normalized}"


def parse_date(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except Exception:
        return None
