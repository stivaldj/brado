
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    cpf: str = Field(..., description='Brazilian CPF number (identifier)')
    name: Optional[str] = Field(None, description='Optional display name')

class LoginResponse(BaseModel):
    token: str

class EventCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    latitude: float
    longitude: float
    radius: float  # in meters
    start_time: datetime
    end_time: datetime

class EventResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    latitude: float
    longitude: float
    radius: float
    start_time: datetime
    end_time: datetime

class CheckinRequest(BaseModel):
    event_id: int
    latitude: float
    longitude: float
    timestamp: Optional[datetime] = None
    photo: Optional[str] = None  # base64 encoded photo

class CheckinResponse(BaseModel):
    message: str
    root: str

class VoteThemeCreateRequest(BaseModel):
    question: str
    options: List[str]
    open_time: datetime
    close_time: datetime

class VoteThemeResponse(BaseModel):
    id: int
    question: str
    options: List[str]
    open_time: datetime
    close_time: datetime

class VoteTokenRequest(BaseModel):
    theme_id: int

class VoteTokenResponse(BaseModel):
    token: str

class VoteRequest(BaseModel):
    theme_id: int
    option: str
    token: str

class VoteResponse(BaseModel):
    message: str
    root: str


# -------------------------------------------------------------------------
# Auth v2 models (anonymous client-id based auth)
# -------------------------------------------------------------------------
class AuthTokenRequest(BaseModel):
    client_id: str = Field(..., description='Unique client identifier')

class AuthTokenResponse(BaseModel):
    access_token: str
    expires_in: int = 1800
    token_type: str = 'bearer'

class AuthMeResponse(BaseModel):
    subject: str
    ttl: int


# -------------------------------------------------------------------------
# Interview models
# -------------------------------------------------------------------------
class InterviewQuestion(BaseModel):
    question_id: str
    text: str
    tags: List[str] = []
    dimensions: List[str] = []

class InterviewStartRequest(BaseModel):
    user_id: Optional[str] = None

class InterviewStartResponse(BaseModel):
    session_id: str
    question: Optional[InterviewQuestion] = None
    next_question: Optional[InterviewQuestion] = None
    answered_count: int = 0

class InterviewAnswerRequest(BaseModel):
    answer: int = Field(..., ge=1, le=7, description='Likert scale 1-7')
    question_id: Optional[str] = None

class InterviewAnswerResponse(BaseModel):
    session_id: str
    next_question: Optional[InterviewQuestion] = None
    answered_count: int
    done: bool = False

class RankingItem(BaseModel):
    tipo: str
    nome: str
    sigla: Optional[str] = None
    similaridade: float
    explicacao: Optional[str] = None

class InterviewMetricas(BaseModel):
    esquerda_direita: float
    confianca: float
    consistencia: float

class InterviewResult(BaseModel):
    session_id: str
    metricas: InterviewMetricas
    vetor: dict
    ranking: List[RankingItem]


# -------------------------------------------------------------------------
# Budget models
# -------------------------------------------------------------------------
class BudgetAllocation(BaseModel):
    category: str
    percent: float = Field(..., ge=0, le=100)

class BudgetSimulationRequest(BaseModel):
    allocations: List[BudgetAllocation]

class BudgetSimulationResponse(BaseModel):
    valid: bool
    total_percent: float
    tradeoffs: List[str]


# -------------------------------------------------------------------------
# Propositions models
# -------------------------------------------------------------------------
class PropositionItem(BaseModel):
    id: Optional[int] = None
    sigla: Optional[str] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    kind: Optional[str] = None

class PropositionsResponse(BaseModel):
    items: List[PropositionItem]
