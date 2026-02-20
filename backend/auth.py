
"""Simple authentication module for demonstration.

In production, authentication would be handled via OIDC with gov.br.
Here we generate a random token on login and use it as a bearer token.
"""
import secrets
from typing import Optional

from fastapi import HTTPException, Header

from .database import db_instance


def login_user(cpf: str) -> str:
    """Register a new session for the given CPF and return a bearer token."""
    token = secrets.token_urlsafe(32)
    db_instance.register_user(token, cpf)
    return token


def get_current_token(authorization: Optional[str] = Header(None)) -> str:
    """Extract the bearer token from the Authorization header.

    Raises HTTPException if the header is missing or the token is invalid.
    """
    if authorization is None or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Missing Authorization header')
    token = authorization.split(' ', 1)[1]
    if not db_instance.validate_token(token):
        raise HTTPException(status_code=401, detail='Invalid or expired token')
    return token
