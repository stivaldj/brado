import hashlib
import secrets
import json
from typing import Any


def generate_salt(length: int = 16) -> str:
    """Generate a hexadecimal salt of the given length."""
    return secrets.token_hex(length)


def hash_value(value: str, salt: str) -> str:
    """Compute a SHA‑256 hash of the value concatenated with the salt."""
    data = (value + salt).encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def sha256_json_canonical(obj: Any) -> str:
    """Return a deterministic SHA‑256 hash of a JSON‑serializable object.

    The object is JSON‑encoded with keys sorted and whitespace removed
    (using ``separators=(',', ':')``) to ensure a canonical representation.
    The resulting UTF‑8 string is then hashed with SHA‑256 and the hex digest
    is returned.
    """
    # Ensure deterministic JSON representation
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
