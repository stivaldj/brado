from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from .constants import DIMENSIONS, LIKERT_MAX, LIKERT_MIN


class InterviewStartRequest(BaseModel):
    user_id: str | None = Field(default=None, max_length=256)
    metadata: dict[str, Any] = Field(default_factory=dict)


class QuestionResponse(BaseModel):
    id: str
    pergunta: str
    tipo_resposta: str
    dimensoes_afetadas: dict[str, float]
    tags: list[str] = Field(default_factory=list)


class InterviewStartResponse(BaseModel):
    session_id: str
    question: QuestionResponse


class AnswerRequest(BaseModel):
    question_id: str
    answer: int = Field(ge=LIKERT_MIN, le=LIKERT_MAX)


class AnswerResponse(BaseModel):
    session_id: str
    answered_questions: int
    next_question: QuestionResponse | None


class ScoringVector(BaseModel):
    vetor: dict[str, float]
    esquerda_direita: float
    confianca: float
    consistencia: float


class RankingEntry(BaseModel):
    tipo: str
    id: str
    nome: str
    sigla: str | None = None
    similaridade: float
    explicacao: str


class InterviewResultResponse(BaseModel):
    session_id: str
    resultado: ScoringVector
    ranking: list[RankingEntry]


class BudgetAllocation(BaseModel):
    category: str
    percent: float = Field(ge=0, le=100)


class BudgetSimulationRequest(BaseModel):
    allocations: list[BudgetAllocation]


class BudgetSimulationResponse(BaseModel):
    valid: bool
    total_percent: float
    tradeoffs: list[str]


class LegislativeQueryResponse(BaseModel):
    items: list[dict[str, Any]]


class UpsertLegislatorProfile(BaseModel):
    external_id: str
    name: str
    chamber: str
    party: str
    state: str | None = None
    vector: dict[str, float]

    @field_validator("vector")
    @classmethod
    def validate_vector(cls, value: dict[str, float]) -> dict[str, float]:
        normalized = {key: float(value.get(key, 0.0)) for key in DIMENSIONS}
        return normalized


class UpsertPartyProfile(BaseModel):
    acronym: str
    name: str
    vector: dict[str, float]

    @field_validator("vector")
    @classmethod
    def validate_vector(cls, value: dict[str, float]) -> dict[str, float]:
        normalized = {key: float(value.get(key, 0.0)) for key in DIMENSIONS}
        return normalized


class ApiV1TokenRequest(BaseModel):
    client_id: str = Field(min_length=2, max_length=128)


class ApiV1TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
