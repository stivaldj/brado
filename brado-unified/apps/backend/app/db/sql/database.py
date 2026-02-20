from __future__ import annotations

"""Legacy in-memory prototype storage.

This module is intentionally isolated from the official ingestion pipeline.
Use SQL models + RawStore + jobs for production data flow.
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class DemoDatabase:
    users: Dict[str, str] = field(default_factory=dict)

    def register_user(self, token: str, cpf: str) -> None:
        self.users[token] = cpf

    def validate_token(self, token: str) -> bool:
        return token in self.users


db_instance = DemoDatabase()
