import os
import tempfile
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional

# Carrega variáveis do .env antes de qualquer leitura de os.getenv
try:
    from dotenv import load_dotenv as _load_dotenv
    _load_dotenv(os.path.join(os.path.dirname(__file__), '.env'), override=False)
except ImportError:
    pass

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    ForeignKey,
    LargeBinary,
    Text,
    create_engine,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _create_engine(db_url: str):
    if db_url.startswith("sqlite:"):
        return create_engine(
            db_url,
            echo=False,
            future=True,
            connect_args={"check_same_thread": False, "timeout": 30},
        )
    return create_engine(db_url, echo=False, future=True)


def _fallback_sqlite_url() -> str:
    configured = os.getenv("BACKEND_FALLBACK_DB_URL")
    if configured:
        return configured
    # Isolate fallback DB per process to avoid cross-process file locks in dev/test.
    return f"sqlite:///{os.path.join(tempfile.gettempdir(), f'br_manifest_fallback_{os.getpid()}.db')}"


def _is_truthy(value: Optional[str]) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _strict_db_mode_enabled() -> bool:
    if _is_truthy(os.getenv("DB_STRICT_MODE")):
        return True
    env = (os.getenv("APP_ENV") or os.getenv("ENV") or os.getenv("NODE_ENV") or "").strip().lower()
    return env == "production"

# Read DB URL from environment or .env file
DB_URL = os.getenv('DB_URL')
if not DB_URL:
    # Attempt to load from .env file in the same directory
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('DB_URL='):
                    DB_URL = line.split('=', 1)[1]
                    break
    except Exception:
        pass
    if not DB_URL:
        raise RuntimeError('DB_URL environment variable not set and not found in .env')

# Create engine and session factory with fallback to SQLite if PostgreSQL connection fails
STRICT_DB_MODE = _strict_db_mode_enabled()
try:
    engine = _create_engine(DB_URL)
    logger.info('Using DB_URL from environment: %s', DB_URL)
except Exception as e:
    if STRICT_DB_MODE:
        raise RuntimeError(
            f"Strict DB mode enabled. Failed to initialize primary DB engine ({DB_URL}): {e}"
        ) from e
    fallback_url = _fallback_sqlite_url()
    engine = _create_engine(fallback_url)
    logger.warning('Failed to connect using DB_URL (%s). Falling back to SQLite (%s). Error: %s', DB_URL, fallback_url, e)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()

# ORM models
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, nullable=False, index=True)
    cpf = Column(String, nullable=False)

class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius = Column(Float, nullable=False)
    start_time = Column(Float, nullable=False)  # store as UNIX timestamp
    end_time = Column(Float, nullable=False)
    salt = Column(String, nullable=False)
    # relationship to checkins
    checkins = relationship('CheckIn', back_populates='event', cascade='all, delete-orphan')

class Theme(Base):
    __tablename__ = 'themes'
    id = Column(Integer, primary_key=True, index=True)
    question = Column(String, nullable=False)
    options = Column(Text, nullable=False)  # JSON‑encoded list of strings
    open_time = Column(Float, nullable=False)
    close_time = Column(Float, nullable=False)
    votes = relationship('Vote', back_populates='theme', cascade='all, delete-orphan')
    tokens = relationship('VoteToken', back_populates='theme', cascade='all, delete-orphan')

class CheckIn(Base):
    __tablename__ = 'checkins'
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(Float, nullable=False)
    photo_hash = Column(String, nullable=True)
    leaf_hash = Column(String, nullable=False)
    event = relationship('Event', back_populates='checkins')
    user = relationship('User')
    __table_args__ = (
        UniqueConstraint('event_id', 'user_id', name='uq_checkin_user_per_event'),
    )

class VoteToken(Base):
    __tablename__ = 'vote_tokens'
    token = Column(String, primary_key=True, index=True)
    theme_id = Column(Integer, ForeignKey('themes.id'), nullable=False)
    user_hash = Column(String, nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    theme = relationship('Theme', back_populates='tokens')
    __table_args__ = (
        UniqueConstraint('theme_id', 'user_hash', name='uq_vote_token_user_per_theme'),
    )

class Vote(Base):
    __tablename__ = 'votes'
    id = Column(Integer, primary_key=True, index=True)
    theme_id = Column(Integer, ForeignKey('themes.id'), nullable=False)
    token = Column(String, ForeignKey('vote_tokens.token'), nullable=False)
    option = Column(String, nullable=False)
    leaf_hash = Column(String, nullable=False)
    theme = relationship('Theme', back_populates='votes')
    vote_token = relationship('VoteToken')


class CamaraSnapshot(Base):
    __tablename__ = 'camara_snapshots'
    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String, nullable=False, index=True)
    item_id = Column(String, nullable=False)
    source_url = Column(String, nullable=False)
    sort_value = Column(String, nullable=True)
    payload = Column(Text, nullable=False)
    fetched_at = Column(Float, nullable=False)
    __table_args__ = (
        UniqueConstraint('endpoint', 'item_id', name='uq_camara_snapshot_endpoint_item'),
    )


class DeputadoNormalizado(Base):
    __tablename__ = 'deputados_normalizados'
    id = Column(Integer, primary_key=True, index=True)
    uri = Column(String, nullable=False)
    nome_civil = Column(String, nullable=True)
    cpf = Column(String, nullable=True)
    sexo = Column(String, nullable=True)
    url_website = Column(String, nullable=True)
    rede_social_json = Column(Text, nullable=True)
    data_nascimento = Column(String, nullable=True)
    data_falecimento = Column(String, nullable=True)
    uf_nascimento = Column(String, nullable=True)
    municipio_nascimento = Column(String, nullable=True)
    escolaridade = Column(String, nullable=True)
    status_nome = Column(String, nullable=True)
    status_nome_eleitoral = Column(String, nullable=True)
    status_sigla_partido = Column(String, nullable=True)
    status_sigla_uf = Column(String, nullable=True)
    status_id_legislatura = Column(Integer, nullable=True)
    status_situacao = Column(String, nullable=True)
    status_condicao_eleitoral = Column(String, nullable=True)
    status_data = Column(String, nullable=True)
    status_email = Column(String, nullable=True)
    foto_url = Column(String, nullable=True)
    foto_bytes = Column(LargeBinary, nullable=True)
    foto_sha256 = Column(String, nullable=True)
    foto_content_type = Column(String, nullable=True)
    gabinete_nome = Column(String, nullable=True)
    gabinete_predio = Column(String, nullable=True)
    gabinete_sala = Column(String, nullable=True)
    gabinete_andar = Column(String, nullable=True)
    gabinete_telefone = Column(String, nullable=True)
    gabinete_email = Column(String, nullable=True)
    atualizado_em = Column(Float, nullable=False)


class DeputadoDespesa(Base):
    __tablename__ = "deputado_despesas"
    id = Column(Integer, primary_key=True, index=True)
    deputado_id = Column(Integer, ForeignKey("deputados_normalizados.id"), nullable=False, index=True)
    dedupe_key = Column(String, nullable=False, unique=True, index=True)
    ano = Column(Integer, nullable=False, index=True)
    mes = Column(Integer, nullable=False, index=True)
    data_documento = Column(String, nullable=True)
    tipo_despesa = Column(String, nullable=True)
    nome_fornecedor = Column(String, nullable=True)
    cnpj_cpf_fornecedor = Column(String, nullable=True)
    cod_lote = Column(Integer, nullable=True)
    cod_documento = Column(String, nullable=True)
    parcela = Column(Integer, nullable=True)
    tipo_documento = Column(String, nullable=True)
    num_documento = Column(String, nullable=True)
    num_ressarcimento = Column(String, nullable=True)
    valor_documento = Column(Float, nullable=True)
    valor_glosa = Column(Float, nullable=True)
    valor_liquido = Column(Float, nullable=True)
    url_documento = Column(String, nullable=True)
    raw_json = Column(Text, nullable=True)
    fetched_at = Column(Float, nullable=False, index=True)


class DeputadoDespesaSyncState(Base):
    __tablename__ = "deputado_despesas_sync_state"
    id = Column(Integer, primary_key=True, index=True)
    deputado_id = Column(Integer, nullable=False, index=True)
    ano = Column(Integer, nullable=False, index=True)
    pagina_atual = Column(Integer, nullable=False, default=1)
    status = Column(String, nullable=False, default="pending")
    erro = Column(Text, nullable=True)
    updated_at = Column(Float, nullable=False, index=True)
    __table_args__ = (
        UniqueConstraint("deputado_id", "ano", name="uq_despesas_sync_state_dep_ano"),
    )


class InterviewSession(Base):
    __tablename__ = "interview_sessions"
    id = Column(String, primary_key=True, index=True)
    client_id = Column(String, nullable=False, index=True)
    question_ids_json = Column(Text, nullable=False)
    answers_json = Column(Text, nullable=False, default="{}")
    result_json = Column(Text, nullable=True)
    completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(Float, nullable=False)


class InterviewAnswer(Base):
    __tablename__ = "interview_answers"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("interview_sessions.id"), nullable=False, index=True)
    question_id = Column(String, nullable=False)
    answer = Column(Integer, nullable=False)


# Helper functions
def init_db() -> None:
    """Create all tables if they do not exist.
    If the primary DB connection fails (e.g., PostgreSQL unavailable),
    fall back to a local SQLite database.
    """
    global engine, SessionLocal
    try:
        Base.metadata.create_all(bind=engine)
        logger.info('Database tables created using primary DB')
    except Exception as e:
        if STRICT_DB_MODE:
            raise RuntimeError(
                f"Strict DB mode enabled. Failed to create tables on primary DB ({DB_URL}): {e}"
            ) from e
        # Fallback to SQLite
        fallback_url = _fallback_sqlite_url()
        fallback_engine = _create_engine(fallback_url)
        Base.metadata.create_all(bind=fallback_engine)
        logger.warning('Failed to create tables on primary DB (%s). Falling back to SQLite (%s). Error: %s', DB_URL, fallback_url, e)
        # Reassign engine and SessionLocal for the rest of the application
        engine = fallback_engine
        SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# Export symbols for import elsewhere
__all__ = [
    'engine',
    'SessionLocal',
    'Base',
    'User',
    'Event',
    'Theme',
    'CheckIn',
    'VoteToken',
    'Vote',
    'CamaraSnapshot',
    'DeputadoNormalizado',
    'DeputadoDespesa',
    'DeputadoDespesaSyncState',
    'InterviewSession',
    'InterviewAnswer',
    'init_db',
]
