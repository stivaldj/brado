import json
import time
from pathlib import Path
from typing import Any, Dict

STATUS_FILE = Path(__file__).resolve().parent / "logs" / "sync_status.json"


def write_sync_status(payload: Dict[str, Any]) -> None:
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = dict(payload)
    data.setdefault("updated_at", time.time())
    STATUS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_sync_status() -> Dict[str, Any]:
    if not STATUS_FILE.exists():
        return {}
    try:
        raw = STATUS_FILE.read_text(encoding="utf-8")
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}
