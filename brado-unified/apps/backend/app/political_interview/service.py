from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from typing import Any

from sqlalchemy import func, select

from ..core.config import get_settings
from ..db.sql import session_scope
from ..db.sql.models import (
    InterviewAnswer,
    InterviewQuestion,
    InterviewResult,
    InterviewSession,
    LegislatorProfile,
    PartyProfile,
    RawPayload,
)
from .budget import simulate_budget
from .constants import DIMENSIONS
from .question_bank import build_seed_questions, pick_next_question
from .report_export import build_pdf_report, format_result_lines
from .scoring import score_interview
from .similarity import cosine_similarity, explain_similarity


class InterviewService:
    def seed_questions(self, total: int = 600) -> dict[str, Any]:
        with session_scope() as session:
            existing = session.scalar(select(func.count(InterviewQuestion.id))) or 0
            if existing >= total:
                return {"seeded": 0, "total": int(existing)}

            questions = build_seed_questions(total=total)
            to_insert = [q for q in questions if session.get(InterviewQuestion, q["id"]) is None]
            for row in to_insert:
                session.add(InterviewQuestion(**row))

            return {"seeded": len(to_insert), "total": int(existing) + len(to_insert)}

    def start_session(self, user_id: str | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        with session_scope() as session:
            self._ensure_question_bank(session)
            anon = self._anonymize_user(user_id)
            row = InterviewSession(anon_user_hash=anon, metadata_json=metadata or {}, status="in_progress")
            session.add(row)
            session.flush()

            first = self._next_question(session, session_id=row.id)
            return {"session_id": row.id, "question": self._serialize_question(first)}

    def submit_answer(self, session_id: str, question_id: str, answer: int) -> dict[str, Any]:
        with session_scope() as session:
            interview = session.get(InterviewSession, session_id)
            if interview is None:
                raise ValueError("Session not found")
            if interview.status != "in_progress":
                raise ValueError("Session is already closed")

            question = session.get(InterviewQuestion, question_id)
            if question is None or int(question.active) != 1:
                raise ValueError("Question not found")

            existing = session.execute(
                select(InterviewAnswer).where(
                    InterviewAnswer.session_id == session_id,
                    InterviewAnswer.question_id == question_id,
                )
            ).scalar_one_or_none()
            if existing is None:
                session.add(InterviewAnswer(session_id=session_id, question_id=question_id, answer_value=answer))
                session.flush()

            answered_count = int(
                session.scalar(select(func.count(InterviewAnswer.id)).where(InterviewAnswer.session_id == session_id))
                or 0
            )

            next_question = self._next_question(session, session_id=session_id)
            return {
                "session_id": session_id,
                "answered_questions": answered_count,
                "next_question": self._serialize_question(next_question) if next_question else None,
            }

    def finish_session(self, session_id: str) -> dict[str, Any]:
        with session_scope() as session:
            interview = session.get(InterviewSession, session_id)
            if interview is None:
                raise ValueError("Session not found")

            min_questions = get_settings().interview_min_questions_for_finish
            answers = self._load_answers_with_dimensions(session, session_id=session_id)
            if len(answers) < min_questions:
                raise ValueError(f"At least {min_questions} answers are required to finish")

            scoring = score_interview(answers)
            ranking = self._build_ranking(session, scoring.vector)

            existing = session.execute(select(InterviewResult).where(InterviewResult.session_id == session_id)).scalar_one_or_none()
            if existing is None:
                result = InterviewResult(
                    session_id=session_id,
                    vector_json=scoring.vector,
                    left_right_score=scoring.left_right_score,
                    confidence=scoring.confidence,
                    consistency=scoring.consistency,
                    ranking_json={"items": ranking},
                )
                session.add(result)
            else:
                existing.vector_json = scoring.vector
                existing.left_right_score = scoring.left_right_score
                existing.confidence = scoring.confidence
                existing.consistency = scoring.consistency
                existing.ranking_json = {"items": ranking}

            interview.status = "completed"
            interview.completed_at = datetime.now(timezone.utc)
            session.add(interview)

            return {
                "session_id": session_id,
                "resultado": {
                    "vetor": scoring.vector,
                    "esquerda_direita": scoring.left_right_score,
                    "confianca": scoring.confidence,
                    "consistencia": scoring.consistency,
                },
                "ranking": ranking,
            }

    def get_result(self, session_id: str) -> dict[str, Any]:
        with session_scope() as session:
            row = session.execute(select(InterviewResult).where(InterviewResult.session_id == session_id)).scalar_one_or_none()
            if row is None:
                raise ValueError("Result not found")

            return {
                "session_id": session_id,
                "resultado": {
                    "vetor": row.vector_json,
                    "esquerda_direita": row.left_right_score,
                    "confianca": row.confidence,
                    "consistencia": row.consistency,
                },
                "ranking": list((row.ranking_json or {}).get("items", [])),
            }

    def export_result_json(self, session_id: str) -> dict[str, Any]:
        return self.get_result(session_id)

    def export_result_pdf(self, session_id: str) -> bytes:
        result = self.get_result(session_id)
        lines = format_result_lines(result)
        return build_pdf_report(title="Relatorio Politico-Analitico", lines=lines)

    def upsert_legislator_profiles(self, profiles: list[dict[str, Any]]) -> dict[str, int]:
        with session_scope() as session:
            upserted = 0
            for payload in profiles:
                row = session.execute(
                    select(LegislatorProfile).where(
                        LegislatorProfile.external_id == payload["external_id"],
                        LegislatorProfile.chamber == payload["chamber"],
                    )
                ).scalar_one_or_none()
                if row is None:
                    row = LegislatorProfile(
                        external_id=payload["external_id"],
                        name=payload["name"],
                        chamber=payload["chamber"],
                        party=payload["party"],
                        state=payload.get("state"),
                        vector_json=payload["vector"],
                    )
                    session.add(row)
                else:
                    row.name = payload["name"]
                    row.party = payload["party"]
                    row.state = payload.get("state")
                    row.vector_json = payload["vector"]
                upserted += 1
            return {"upserted": upserted}

    def upsert_party_profiles(self, profiles: list[dict[str, Any]]) -> dict[str, int]:
        with session_scope() as session:
            upserted = 0
            for payload in profiles:
                row = session.execute(select(PartyProfile).where(PartyProfile.acronym == payload["acronym"])).scalar_one_or_none()
                if row is None:
                    row = PartyProfile(acronym=payload["acronym"], name=payload["name"], vector_json=payload["vector"])
                    session.add(row)
                else:
                    row.name = payload["name"]
                    row.vector_json = payload["vector"]
                upserted += 1
            return {"upserted": upserted}

    def run_budget_simulation(self, allocations: list[dict[str, Any]]) -> dict[str, Any]:
        return simulate_budget(allocations)

    def query_legislative_items(self, limit: int = 20) -> dict[str, Any]:
        with session_scope() as session:
            rows = (
                session.execute(
                    select(RawPayload)
                    .where(RawPayload.endpoint.like("%/proposicoes%"))
                    .order_by(RawPayload.fetched_at.desc())
                    .limit(max(1, min(limit, 100)))
                )
                .scalars()
                .all()
            )
            items = []
            for row in rows:
                payload = row.body_json if isinstance(row.body_json, dict) else {}
                for entry in payload.get("dados", [])[:3]:
                    items.append(
                        {
                            "id": entry.get("id"),
                            "ementa": entry.get("ementa"),
                            "siglaTipo": entry.get("siglaTipo"),
                            "numero": entry.get("numero"),
                            "ano": entry.get("ano"),
                        }
                    )
            return {"items": items[: limit]}

    def _ensure_question_bank(self, session) -> None:
        existing = session.scalar(select(func.count(InterviewQuestion.id))) or 0
        if existing > 0:
            return

        for question in build_seed_questions(600):
            session.add(InterviewQuestion(**question))
        session.flush()

    def _next_question(self, session, session_id: str) -> InterviewQuestion | None:
        answered_ids = {
            row[0]
            for row in session.execute(select(InterviewAnswer.question_id).where(InterviewAnswer.session_id == session_id)).all()
        }
        all_questions = session.execute(
            select(InterviewQuestion).where(InterviewQuestion.active == 1).order_by(InterviewQuestion.id.asc())
        ).scalars().all()
        unanswered = [
            {
                "id": q.id,
                "prompt": q.prompt,
                "response_type": q.response_type,
                "dimensions_json": q.dimensions_json,
                "tags_json": q.tags_json,
            }
            for q in all_questions
            if q.id not in answered_ids
        ]
        answers = self._load_answers_with_dimensions(session, session_id=session_id)
        scoring = score_interview(answers)
        picked = pick_next_question(unanswered_questions=unanswered, partial_vector=scoring.vector)
        if picked is None:
            return None
        return session.get(InterviewQuestion, picked["id"])

    def _load_answers_with_dimensions(self, session, session_id: str) -> list[dict]:
        rows = (
            session.execute(
                select(InterviewAnswer, InterviewQuestion)
                .join(InterviewQuestion, InterviewQuestion.id == InterviewAnswer.question_id)
                .where(InterviewAnswer.session_id == session_id)
            )
            .all()
        )
        return [
            {
                "question_id": answer.question_id,
                "answer_value": answer.answer_value,
                "dimensions": question.dimensions_json,
            }
            for answer, question in rows
        ]

    def _build_ranking(self, session, user_vector: dict[str, float], top_k: int = 8) -> list[dict[str, Any]]:
        ranking: list[dict[str, Any]] = []

        legislators = session.execute(select(LegislatorProfile)).scalars().all()
        for row in legislators:
            similarity = cosine_similarity(user_vector, row.vector_json or {})
            ranking.append(
                {
                    "tipo": "deputado",
                    "id": row.external_id,
                    "nome": row.name,
                    "sigla": row.party,
                    "similaridade": similarity,
                    "explicacao": explain_similarity(user_vector, row.vector_json or {}),
                }
            )

        parties = session.execute(select(PartyProfile)).scalars().all()
        for row in parties:
            similarity = cosine_similarity(user_vector, row.vector_json or {})
            ranking.append(
                {
                    "tipo": "partido",
                    "id": row.acronym,
                    "nome": row.name,
                    "sigla": row.acronym,
                    "similaridade": similarity,
                    "explicacao": explain_similarity(user_vector, row.vector_json or {}),
                }
            )

        ranking.sort(key=lambda item: item["similaridade"], reverse=True)
        return ranking[:top_k]

    def _serialize_question(self, question: InterviewQuestion) -> dict[str, Any]:
        return {
            "id": question.id,
            "pergunta": question.prompt,
            "tipo_resposta": question.response_type,
            "dimensoes_afetadas": question.dimensions_json,
            "tags": list(question.tags_json or []),
        }

    def _anonymize_user(self, user_id: str | None) -> str:
        settings = get_settings()
        raw = f"{settings.interview_anonymization_salt}:{user_id or 'anonymous'}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
