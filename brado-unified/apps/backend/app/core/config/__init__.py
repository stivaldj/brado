from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    app_name: str
    environment: str
    log_level: str

    database_url: str
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str

    admin_api_key: str
    admin_rate_limit_per_minute: int

    camara_base_url: str
    camara_user_agent: str
    camara_timeout_seconds: float
    camara_max_rps: float
    camara_max_concurrency: int
    camara_max_retries: int
    camara_proposicoes_static_url_template: str
    camara_votacoes_static_url_template: str
    camara_votacoes_votos_static_url_template: str
    camara_expenses_dataset_url_template: str
    camara_expenses_dataset_separator: str

    vcr_mode: str
    vcr_dir: str

    anchor_provider: str
    interview_target_questions: int
    interview_min_questions_for_finish: int
    interview_anonymization_salt: str
    cors_allow_origins: tuple[str, ...]
    api_v1_auth_required: bool
    api_v1_jwt_secret: str
    api_v1_jwt_ttl_seconds: int
    api_v1_rate_limit_per_minute: int


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "brado-data-core"),
        environment=os.getenv("ENVIRONMENT", "dev"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        database_url=os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@postgres:5432/brado"),
        neo4j_uri=os.getenv("NEO4J_URI", "bolt://neo4j:7687"),
        neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
        neo4j_password=os.getenv("NEO4J_PASSWORD", "neo4j_password"),
        admin_api_key=os.getenv("ADMIN_API_KEY", "change-me"),
        admin_rate_limit_per_minute=int(os.getenv("ADMIN_RATE_LIMIT_PER_MINUTE", "120")),
        camara_base_url=os.getenv("CAMARA_BASE_URL", "https://dadosabertos.camara.leg.br/api/v2"),
        camara_user_agent=os.getenv("CAMARA_USER_AGENT", "brado-data-core/1.0"),
        camara_timeout_seconds=float(os.getenv("CAMARA_TIMEOUT_SECONDS", "30")),
        camara_max_rps=float(os.getenv("CAMARA_MAX_RPS", "3")),
        camara_max_concurrency=int(os.getenv("CAMARA_MAX_CONCURRENCY", "4")),
        camara_max_retries=int(os.getenv("CAMARA_MAX_RETRIES", "4")),
        camara_proposicoes_static_url_template=os.getenv(
            "CAMARA_PROPOSICOES_STATIC_URL_TEMPLATE",
            "https://dadosabertos.camara.leg.br/arquivos/proposicoes/json/proposicoes-{year}.json",
        ),
        camara_votacoes_static_url_template=os.getenv(
            "CAMARA_VOTACOES_STATIC_URL_TEMPLATE",
            "https://dadosabertos.camara.leg.br/arquivos/votacoes/json/votacoes-{year}.json",
        ),
        camara_votacoes_votos_static_url_template=os.getenv(
            "CAMARA_VOTACOES_VOTOS_STATIC_URL_TEMPLATE",
            "https://dadosabertos.camara.leg.br/arquivos/votacoesVotos/json/votacoesVotos-{year}.json",
        ),
        camara_expenses_dataset_url_template=os.getenv("CAMARA_EXPENSES_DATASET_URL_TEMPLATE", ""),
        camara_expenses_dataset_separator=os.getenv("CAMARA_EXPENSES_DATASET_SEPARATOR", ","),
        vcr_mode=os.getenv("VCR_MODE", "off"),
        vcr_dir=os.getenv("VCR_DIR", "backend/tests/fixtures/vcr"),
        anchor_provider=os.getenv("ANCHOR_PROVIDER", "composite"),
        interview_target_questions=int(os.getenv("INTERVIEW_TARGET_QUESTIONS", "40")),
        interview_min_questions_for_finish=int(os.getenv("INTERVIEW_MIN_QUESTIONS_FOR_FINISH", "20")),
        interview_anonymization_salt=os.getenv("INTERVIEW_ANONYMIZATION_SALT", "replace-me"),
        cors_allow_origins=tuple(
            origin.strip()
            for origin in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
            if origin.strip()
        ),
        api_v1_auth_required=os.getenv("API_V1_AUTH_REQUIRED", "false").lower() in {"1", "true", "yes", "on"},
        api_v1_jwt_secret=os.getenv("API_V1_JWT_SECRET", "change-me-v1-token-secret"),
        api_v1_jwt_ttl_seconds=int(os.getenv("API_V1_JWT_TTL_SECONDS", "3600")),
        api_v1_rate_limit_per_minute=int(os.getenv("API_V1_RATE_LIMIT_PER_MINUTE", "120")),
    )
