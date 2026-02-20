
"""Utility functions for salted hashing and salt generation."""
import hashlib
import secrets


def generate_salt(length: int = 16) -> str:
    """Generate a hexadecimal salt of the given length."""
    return secrets.token_hex(length)


def hash_value(value: str, salt: str) -> str:
    """Compute a SHA‑256 hash of the value concatenated with the salt."""
    data = (value + salt).encode('utf-8')
    return hashlib.sha256(data).hexdigest()
