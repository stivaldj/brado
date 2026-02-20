"""
Interview engine: session management and political matching algorithm.

Fluxo:
1. start_session()    → cria sessão, retorna 1ª questão
2. answer_question()  → registra resposta Likert (1-7), retorna próxima questão
3. finish_session()   → calcula vetor 8D + ranking
4. get_result()       → retorna o resultado calculado
"""

import json
import math
import secrets
import time
from typing import Optional

from sqlalchemy.orm import Session

from .questions import QUESTIONS, ALL_DIMENSIONS, PARTY_PROFILES, get_question_by_id

# Quantas questões por sessão (subset do banco completo)
SESSION_QUESTION_COUNT = min(20, len(QUESTIONS))


def _create_session(db: Session, client_id: str, InterviewSession, InterviewAnswer) -> str:
    session_id = secrets.token_urlsafe(16)
    question_ids = [q["id"] for q in QUESTIONS[:SESSION_QUESTION_COUNT]]
    sess = InterviewSession(
        id=session_id,
        client_id=client_id,
        question_ids_json=json.dumps(question_ids),
        answers_json=json.dumps({}),
        result_json=None,
        completed=False,
        created_at=time.time(),
    )
    db.add(sess)
    db.commit()
    db.refresh(sess)
    return session_id


def _get_session(db: Session, session_id: str, InterviewSession):
    return db.query(InterviewSession).filter(InterviewSession.id == session_id).first()


def _normalize_answer(raw: int) -> float:
    """Map Likert 1-7 → [-1, +1]."""
    return (raw - 4) / 3.0


def _compute_vector(answers: dict) -> dict:
    """
    Compute 8D political vector from answered questions.
    answers: { question_id: likert_int }
    Returns: { dimension: float }
    """
    dim_scores: dict[str, list[float]] = {d: [] for d in ALL_DIMENSIONS}

    for qid, raw_answer in answers.items():
        question = get_question_by_id(qid)
        if question is None:
            continue
        normalized = _normalize_answer(int(raw_answer))
        for dim, weight in question["dims"]:
            dim_scores[dim].append(normalized * weight)

    result = {}
    for dim in ALL_DIMENSIONS:
        scores = dim_scores[dim]
        result[dim] = round(sum(scores) / len(scores), 4) if scores else 0.0

    return result


def _cosine_similarity(vec_a: dict, vec_b: dict) -> float:
    """Cosine similarity between two dimension vectors."""
    dims = ALL_DIMENSIONS
    a = [vec_a.get(d, 0.0) for d in dims]
    b = [vec_b.get(d, 0.0) for d in dims]

    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x ** 2 for x in a))
    mag_b = math.sqrt(sum(x ** 2 for x in b))

    if mag_a == 0 or mag_b == 0:
        return 0.0

    # Map from [-1, 1] to [0, 1]
    raw = dot / (mag_a * mag_b)
    return round((raw + 1) / 2, 4)


def _compute_metrics(user_vector: dict, answers: dict) -> dict:
    """Compute esquerda_direita, confianca, consistencia."""
    # esquerda_direita: average of economic + social dimensions
    ed_dims = ["economico", "social", "laicidade"]
    ed_scores = [user_vector.get(d, 0.0) for d in ed_dims]
    esquerda_direita = round(sum(ed_scores) / len(ed_dims), 4)

    # confianca: proportion of questions actually answered
    total_questions = SESSION_QUESTION_COUNT
    answered = len(answers)
    confianca = round(min(1.0, answered / total_questions), 4)

    # consistencia: check that dimensions with multiple questions don't wildly contradict
    # Simple heuristic: std deviation of dimension scores (lower = more consistent)
    scores = list(user_vector.values())
    if len(scores) > 1:
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std = math.sqrt(variance)
        # Normalize: std range is ~0 to 1.2; lower std = higher consistency
        consistencia = round(max(0.0, 1.0 - std / 1.2), 4)
    else:
        consistencia = 1.0

    return {
        "esquerda_direita": esquerda_direita,
        "confianca": confianca,
        "consistencia": consistencia,
    }


def _rank_parties(user_vector: dict) -> list:
    ranked = []
    for profile in PARTY_PROFILES:
        sim = _cosine_similarity(user_vector, profile["vetor"])
        ranked.append({
            "tipo": profile["tipo"],
            "nome": profile["nome"],
            "sigla": profile["sigla"],
            "similaridade": sim,
            "explicacao": None,
        })
    ranked.sort(key=lambda x: x["similaridade"], reverse=True)
    return ranked


# -------------------------------------------------------------------------
# Public API used by the router
# -------------------------------------------------------------------------

def start_session(db: Session, client_id: str, InterviewSession, InterviewAnswer) -> dict:
    session_id = _create_session(db, client_id, InterviewSession, InterviewAnswer)
    first_question = QUESTIONS[0] if QUESTIONS else None

    q = None
    if first_question:
        q = {
            "question_id": first_question["id"],
            "text": first_question["text"],
            "tags": first_question["tags"],
            "dimensions": [d for d, _ in first_question["dims"]],
        }

    return {
        "session_id": session_id,
        "question": q,
        "next_question": q,
        "answered_count": 0,
    }


def answer_question(
    db: Session,
    session_id: str,
    question_id: str,
    answer: int,
    InterviewSession,
    InterviewAnswer,
) -> dict:
    sess = _get_session(db, session_id, InterviewSession)
    if sess is None:
        raise ValueError("Sessão não encontrada")
    if sess.completed:
        raise ValueError("Sessão já finalizada")

    answers = json.loads(sess.answers_json or "{}")
    question_ids = json.loads(sess.question_ids_json or "[]")

    # Determine effective question_id: use provided or infer next unanswered
    effective_qid = question_id or None
    if not effective_qid:
        for qid in question_ids:
            if qid not in answers:
                effective_qid = qid
                break

    if effective_qid:
        answers[effective_qid] = answer

    sess.answers_json = json.dumps(answers)
    db.commit()

    answered_count = len(answers)
    total = len(question_ids)

    # Find next unanswered question
    next_q = None
    for qid in question_ids:
        if qid not in answers:
            raw = get_question_by_id(qid)
            if raw:
                next_q = {
                    "question_id": raw["id"],
                    "text": raw["text"],
                    "tags": raw["tags"],
                    "dimensions": [d for d, _ in raw["dims"]],
                }
            break

    done = answered_count >= total

    return {
        "session_id": session_id,
        "next_question": next_q,
        "answered_count": answered_count,
        "done": done,
    }


def finish_session(db: Session, session_id: str, InterviewSession, InterviewAnswer) -> dict:
    sess = _get_session(db, session_id, InterviewSession)
    if sess is None:
        raise ValueError("Sessão não encontrada")

    answers = json.loads(sess.answers_json or "{}")
    user_vector = _compute_vector(answers)
    metrics = _compute_metrics(user_vector, answers)
    ranking = _rank_parties(user_vector)

    result = {
        "session_id": session_id,
        "metricas": metrics,
        "vetor": user_vector,
        "ranking": ranking,
    }

    sess.result_json = json.dumps(result)
    sess.completed = True
    db.commit()

    return result


def get_result(db: Session, session_id: str, InterviewSession) -> dict:
    sess = _get_session(db, session_id, InterviewSession)
    if sess is None:
        raise ValueError("Sessão não encontrada")
    if not sess.result_json:
        # Compute on the fly if not yet persisted
        answers = json.loads(sess.answers_json or "{}")
        user_vector = _compute_vector(answers)
        metrics = _compute_metrics(user_vector, answers)
        ranking = _rank_parties(user_vector)
        return {
            "session_id": session_id,
            "metricas": metrics,
            "vetor": user_vector,
            "ranking": ranking,
        }
    return json.loads(sess.result_json)
