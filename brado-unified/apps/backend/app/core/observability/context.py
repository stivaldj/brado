from __future__ import annotations

from contextvars import ContextVar
import secrets

_trace_id: ContextVar[str] = ContextVar("trace_id", default="")
_span_id: ContextVar[str] = ContextVar("span_id", default="")


def generate_trace_id() -> str:
    return secrets.token_hex(16)


def generate_span_id() -> str:
    return secrets.token_hex(8)


def set_trace_context(trace_id: str, span_id: str) -> None:
    _trace_id.set(trace_id)
    _span_id.set(span_id)


def get_trace_id() -> str:
    return _trace_id.get()


def get_span_id() -> str:
    return _span_id.get()


def clear_trace_context() -> None:
    _trace_id.set("")
    _span_id.set("")
