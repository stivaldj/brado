from __future__ import annotations

from collections import defaultdict
from typing import Any

from sqlalchemy import select

from ..db.sql.models import LegislatorProfile, PartyProfile, RawPayload
from ..political_interview.constants import DIMENSIONS


def _normalize_vote(vote_text: str | None) -> float:
    normalized = (vote_text or "").strip().upper()
    mapping = {
        "SIM": 1.0,
        "NAO": -1.0,
        "NÃO": -1.0,
        "ABSTENCAO": 0.0,
        "ABSTENÇÃO": 0.0,
        "OBSTRUCAO": -0.2,
        "OBSTRUÇÃO": -0.2,
        "ART. 17": 0.0,
    }
    return mapping.get(normalized, 0.0)


def _vector_from_signal(signal: float) -> dict[str, float]:
    return {
        "ECO": round(signal, 4),
        "SOC": round(signal * 0.7, 4),
        "EST": round(signal * 0.5, 4),
        "AMB": round(-signal * 0.4, 4),
        "LIB": round(-signal * 0.6, 4),
        "GOV": round(signal * 0.8, 4),
        "GLB": round(signal * 0.3, 4),
        "INS": round(signal * 0.9, 4),
    }


class ProfileJobs:
    def __init__(self, session):
        self.session = session

    def refresh_from_raw_votes(self, limit_payloads: int = 500) -> dict[str, Any]:
        rows = (
            self.session.execute(
                select(RawPayload)
                .where(RawPayload.endpoint.like("%/votacoes/%/votos"))
                .order_by(RawPayload.fetched_at.desc())
                .limit(max(1, min(limit_payloads, 2000)))
            )
            .scalars()
            .all()
        )

        signals: dict[tuple[str, str], list[float]] = defaultdict(list)
        names: dict[tuple[str, str], str] = {}
        parties: dict[tuple[str, str], str] = {}

        for row in rows:
            payload = row.body_json if isinstance(row.body_json, dict) else {}
            for vote in payload.get("dados", []):
                dep = vote.get("deputado_") or {}
                ext_id = str(dep.get("id") or vote.get("id") or "").strip()
                if not ext_id:
                    continue
                key = (ext_id, "camara")
                signal = _normalize_vote(vote.get("tipoVoto"))
                signals[key].append(signal)
                names[key] = dep.get("nome") or vote.get("nome") or f"Deputado {ext_id}"
                parties[key] = dep.get("siglaPartido") or vote.get("siglaPartido") or "N/A"

        upserted_legislators = 0
        for (ext_id, chamber), values in signals.items():
            signal = sum(values) / len(values)
            vector = _vector_from_signal(signal)

            profile = self.session.execute(
                select(LegislatorProfile).where(
                    LegislatorProfile.external_id == ext_id,
                    LegislatorProfile.chamber == chamber,
                )
            ).scalar_one_or_none()

            if profile is None:
                profile = LegislatorProfile(
                    external_id=ext_id,
                    chamber=chamber,
                    name=names[(ext_id, chamber)],
                    party=parties[(ext_id, chamber)],
                    state=None,
                    vector_json=vector,
                )
                self.session.add(profile)
            else:
                profile.name = names[(ext_id, chamber)]
                profile.party = parties[(ext_id, chamber)]
                profile.vector_json = vector
            upserted_legislators += 1

        upserted_parties = self._refresh_party_profiles()

        return {
            "payloads_scanned": len(rows),
            "legislators_upserted": upserted_legislators,
            "parties_upserted": upserted_parties,
        }

    def _refresh_party_profiles(self) -> int:
        legislators = self.session.execute(select(LegislatorProfile)).scalars().all()
        by_party: dict[str, list[dict[str, float]]] = defaultdict(list)
        for row in legislators:
            by_party[row.party].append(row.vector_json or {})

        upserted = 0
        for party, vectors in by_party.items():
            averaged = {}
            for dim in DIMENSIONS:
                values = [float(vector.get(dim, 0.0)) for vector in vectors]
                averaged[dim] = round(sum(values) / len(values), 4) if values else 0.0

            profile = self.session.execute(select(PartyProfile).where(PartyProfile.acronym == party)).scalar_one_or_none()
            if profile is None:
                profile = PartyProfile(acronym=party, name=party, vector_json=averaged)
                self.session.add(profile)
            else:
                profile.name = party
                profile.vector_json = averaged
            upserted += 1

        return upserted
