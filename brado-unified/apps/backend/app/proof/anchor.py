from __future__ import annotations

import json
import os
import time
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List

ANCHOR_FILE = Path(__file__).parent / "anchor_log.json"


def _load_log() -> List[Dict[str, Any]]:
    if ANCHOR_FILE.exists():
        try:
            return json.loads(ANCHOR_FILE.read_text())
        except Exception:
            return []
    return []


class AnchorProvider(ABC):
    @abstractmethod
    def anchor_root(
        self,
        entry_type: str,
        root: str,
        batch_id: str = "",
        metadata: Dict[str, Any] | None = None,
        session=None,
    ) -> Dict[str, Any]:
        raise NotImplementedError


class FileAnchorProvider(AnchorProvider):
    def anchor_root(
        self,
        entry_type: str,
        root: str,
        batch_id: str = "",
        metadata: Dict[str, Any] | None = None,
        session=None,
    ) -> Dict[str, Any]:
        payload = metadata or {}
        log = _load_log()
        entry = {
            "id": str(uuid.uuid4()),
            "anchor_type": "file-log",
            "entry_type": entry_type,
            "root": root,
            "batch_id": batch_id,
            "metadata": payload,
            "anchored_at": int(time.time()),
        }
        log.append(entry)
        ANCHOR_FILE.write_text(json.dumps(log, indent=2))
        return entry


class PostgresAnchorProvider(AnchorProvider):
    def anchor_root(
        self,
        entry_type: str,
        root: str,
        batch_id: str = "",
        metadata: Dict[str, Any] | None = None,
        session=None,
    ) -> Dict[str, Any]:
        if session is None:
            raise ValueError("PostgresAnchorProvider requires SQLAlchemy session")

        from ..db.sql.models import Anchor

        anchor = Anchor(
            id=str(uuid.uuid4()),
            anchor_type="postgres",
            entry_type=entry_type,
            root=root,
            provider_payload={"batch_id": batch_id, **(metadata or {})},
        )
        session.add(anchor)
        session.flush()
        return {
            "id": anchor.id,
            "anchor_type": anchor.anchor_type,
            "entry_type": anchor.entry_type,
            "root": anchor.root,
            "batch_id": batch_id,
            "metadata": metadata or {},
            "anchored_at": int(time.time()),
        }


class BlockchainAnchorProvider(AnchorProvider):
    def anchor_root(
        self,
        entry_type: str,
        root: str,
        batch_id: str = "",
        metadata: Dict[str, Any] | None = None,
        session=None,
    ) -> Dict[str, Any]:
        return {
            "id": str(uuid.uuid4()),
            "anchor_type": "blockchain-placeholder",
            "entry_type": entry_type,
            "root": root,
            "batch_id": batch_id,
            "metadata": metadata or {},
            "anchored_at": int(time.time()),
        }


class CompositeAnchorProvider(AnchorProvider):
    def __init__(self) -> None:
        self.file_provider = FileAnchorProvider()
        self.db_provider = PostgresAnchorProvider()

    def anchor_root(
        self,
        entry_type: str,
        root: str,
        batch_id: str = "",
        metadata: Dict[str, Any] | None = None,
        session=None,
    ) -> Dict[str, Any]:
        file_entry = self.file_provider.anchor_root(entry_type, root, batch_id, metadata)
        db_entry = self.db_provider.anchor_root(entry_type, root, batch_id, metadata, session=session)
        return {**file_entry, "id": db_entry["id"], "db": db_entry}


def _get_provider() -> AnchorProvider:
    provider_name = os.getenv("ANCHOR_PROVIDER", "composite").lower()
    if provider_name == "file":
        return FileAnchorProvider()
    if provider_name == "postgres":
        return PostgresAnchorProvider()
    if provider_name == "blockchain":
        return BlockchainAnchorProvider()
    return CompositeAnchorProvider()


def anchor_root(
    entry_type: str,
    root: str,
    batch_id: str = "",
    metadata: Dict[str, Any] | None = None,
    session=None,
) -> Dict[str, Any]:
    provider = _get_provider()
    return provider.anchor_root(entry_type, root, batch_id, metadata or {}, session=session)
