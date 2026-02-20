from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Any
from urllib.parse import urlencode

from sqlalchemy import func, select

from ..sql.models import Anchor, BatchItem, IngestionBatch, RawPayload
from ...proof.hashing import sha256_json_canonical
from ...proof.merkle import build_merkle
from ...proof.anchor import anchor_root


class RawStore:
    def __init__(self, session):
        self.session = session

    def start_batch(self, source: str, batch_type: str, range_start: date | None = None, range_end: date | None = None) -> IngestionBatch:
        batch = IngestionBatch(
            source=source,
            batch_type=batch_type,
            range_start=range_start,
            range_end=range_end,
            status="running",
            item_count=0,
        )
        self.session.add(batch)
        self.session.flush()
        return batch

    def add_payload(
        self,
        *,
        batch: IngestionBatch,
        endpoint: str,
        params: dict[str, Any],
        primary_key: str | None,
        http_status: int,
        body_json: Any,
        source: str = "camara",
    ) -> RawPayload:
        sha = sha256_json_canonical(body_json)
        query = urlencode(sorted(params.items())) if params else ""
        url = endpoint if not query else f"{endpoint}?{query}"

        raw = RawPayload(
            source=source,
            endpoint=endpoint,
            params_json=params,
            primary_key_value=primary_key,
            fetched_at=datetime.now(timezone.utc),
            http_status=http_status,
            url=url,
            sha256=sha,
            body_json=body_json,
            batch_id=batch.id,
        )
        self.session.add(raw)
        self.session.flush()

        next_leaf = self.session.scalar(
            select(func.count(BatchItem.id)).where(BatchItem.batch_id == batch.id)
        )
        item = BatchItem(
            batch_id=batch.id,
            raw_payload_id=raw.id,
            item_sha256=sha,
            leaf_index=int(next_leaf or 0),
        )
        self.session.add(item)
        batch.item_count = int(batch.item_count or 0) + 1
        self.session.flush()
        return raw

    def finish_batch(self, batch: IngestionBatch, metadata: dict[str, Any] | None = None) -> IngestionBatch:
        leaves = [
            row[0]
            for row in self.session.execute(
                select(BatchItem.item_sha256)
                .where(BatchItem.batch_id == batch.id)
                .order_by(BatchItem.leaf_index.asc())
            ).all()
        ]

        merkle = build_merkle(leaves)
        batch.merkle_root = merkle["root"]
        batch.finished_at = datetime.now(timezone.utc)
        batch.status = "success"
        if metadata is not None:
            batch.notes = json.dumps(metadata, ensure_ascii=True)

        anchor_entry = anchor_root(
            entry_type=f"camara:{batch.batch_type}",
            root=merkle["root"],
            batch_id=batch.id,
            metadata={"batch": batch.batch_type, "range_start": str(batch.range_start), "range_end": str(batch.range_end), **(metadata or {})},
            session=self.session,
        )

        anchor_id = anchor_entry.get("id")
        if anchor_id:
            anchor_row = self.session.get(Anchor, anchor_id)
            if anchor_row:
                batch.anchor_id = anchor_row.id

        self.session.add(batch)
        self.session.flush()
        return batch

    def fail_batch(self, batch: IngestionBatch, notes: str) -> None:
        batch.status = "failed"
        batch.notes = notes
        batch.finished_at = datetime.now(timezone.utc)
        self.session.add(batch)
        self.session.flush()
