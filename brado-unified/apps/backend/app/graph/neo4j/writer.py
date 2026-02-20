from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .constraints import CONSTRAINTS
from .driver import Neo4jClient


class Neo4jWriter:
    def __init__(self) -> None:
        self.client = Neo4jClient()

    def close(self) -> None:
        self.client.close()

    def ensure_constraints(self) -> None:
        with self.client.driver.session() as session:
            for statement in CONSTRAINTS:
                session.run(statement)

    def upsert_person(self, node: dict[str, Any], raw_ref: str | None = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self.client.driver.session() as session:
            session.run(
                """
                MERGE (p:Person {id: $id})
                SET p += $props,
                    p.lastSeenAt = $now,
                    p.rawRefs = CASE
                        WHEN $raw_ref IS NULL THEN coalesce(p.rawRefs, [])
                        WHEN p.rawRefs IS NULL THEN [$raw_ref]
                        WHEN $raw_ref IN p.rawRefs THEN p.rawRefs
                        ELSE p.rawRefs + $raw_ref
                    END
                """,
                id=node["id"],
                props=node,
                now=now,
                raw_ref=raw_ref,
            )

            if node.get("party"):
                party_id = f"camara:party:{node['party']}"
                session.run(
                    """
                    MERGE (party:Party {id:$party_id})
                    SET party.sigla = $sigla
                    WITH party
                    MATCH (p:Person {id:$person_id})
                    MERGE (p)-[:MEMBER_OF]->(party)
                    """,
                    party_id=party_id,
                    sigla=node["party"],
                    person_id=node["id"],
                )

            if node.get("state"):
                state_id = f"camara:state:{node['state']}"
                session.run(
                    """
                    MERGE (s:State {id:$state_id})
                    SET s.uf = $uf
                    WITH s
                    MATCH (p:Person {id:$person_id})
                    MERGE (p)-[:REPRESENTS]->(s)
                    """,
                    state_id=state_id,
                    uf=node["state"],
                    person_id=node["id"],
                )

    def upsert_bill(self, node: dict[str, Any], raw_ref: str | None = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self.client.driver.session() as session:
            session.run(
                """
                MERGE (b:Bill {id:$id})
                SET b += $props,
                    b.lastSeenAt = $now,
                    b.rawRefs = CASE
                        WHEN $raw_ref IS NULL THEN coalesce(b.rawRefs, [])
                        WHEN b.rawRefs IS NULL THEN [$raw_ref]
                        WHEN $raw_ref IN b.rawRefs THEN b.rawRefs
                        ELSE b.rawRefs + $raw_ref
                    END
                """,
                id=node["id"],
                props=node,
                now=now,
                raw_ref=raw_ref,
            )

    def upsert_vote_event(self, node: dict[str, Any], raw_ref: str | None = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self.client.driver.session() as session:
            session.run(
                """
                MERGE (v:VoteEvent {id:$id})
                SET v += $props,
                    v.lastSeenAt = $now,
                    v.rawRefs = CASE
                        WHEN $raw_ref IS NULL THEN coalesce(v.rawRefs, [])
                        WHEN v.rawRefs IS NULL THEN [$raw_ref]
                        WHEN $raw_ref IN v.rawRefs THEN v.rawRefs
                        ELSE v.rawRefs + $raw_ref
                    END
                """,
                id=node["id"],
                props=node,
                now=now,
                raw_ref=raw_ref,
            )
            if node.get("billId"):
                session.run(
                    """
                    MATCH (v:VoteEvent {id:$vote_event_id})
                    MATCH (b:Bill {id:$bill_id})
                    MERGE (v)-[:ON_BILL]->(b)
                    """,
                    vote_event_id=node["id"],
                    bill_id=node["billId"],
                )

    def upsert_vote_action(self, node: dict[str, Any], raw_ref: str | None = None) -> None:
        with self.client.driver.session() as session:
            session.run(
                """
                MERGE (va:VoteAction {id:$id})
                SET va += $props
                WITH va
                MATCH (v:VoteEvent {id:$vote_event_id})
                MATCH (p:Person {id:$person_id})
                MERGE (va)-[:IN_EVENT]->(v)
                MERGE (p)-[:CAST]->(va)
                """,
                id=node["id"],
                props={**node, "rawRef": raw_ref},
                vote_event_id=node["voteEventId"],
                person_id=node["personId"],
            )

    def upsert_expense(self, node: dict[str, Any], raw_ref: str | None = None) -> None:
        with self.client.driver.session() as session:
            session.run(
                """
                MERGE (e:Expense {id:$id})
                SET e += $props
                WITH e
                MATCH (p:Person {id:$person_id})
                MERGE (p)-[:HAS_EXPENSE]->(e)
                MERGE (o:Organization {id:$organization_id})
                SET o.name = $supplier_name
                MERGE (e)-[:PAID_TO]->(o)
                """,
                id=node["id"],
                props={**node, "rawRef": raw_ref},
                person_id=node["personId"],
                organization_id=node["organizationId"],
                supplier_name=node.get("supplierName"),
            )
