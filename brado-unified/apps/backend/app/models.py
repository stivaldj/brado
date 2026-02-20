from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class LoginRequest(BaseModel):
    cpf: str

class LoginResponse(BaseModel):
    token: str

class EventCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    latitude: float
    longitude: float
    radius: float
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
    photo: Optional[str] = None

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
    token: str
    option: str

class VoteResponse(BaseModel):
    message: str
    root: str
