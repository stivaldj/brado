from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CHAR,
    JSON,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from . import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class RawPayload(Base):
    __tablename__ = "raw_payloads"

    id = Column(String(36), primary_key=True, default=_uuid, nullable=False)
    source = Column(String(64), nullable=False)
    endpoint = Column(String(255), nullable=False)
    params_json = Column(JSON, nullable=False, default=dict)
    primary_key_value = Column("primary_key", String(255), nullable=True)
    fetched_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    http_status = Column(Integer, nullable=False)
    url = Column(Text, nullable=False)
    sha256 = Column(CHAR(64), nullable=False)
    body_json = Column(JSON, nullable=False)
    batch_id = Column(String(36), ForeignKey("ingestion_batches.id"), nullable=False)

    batch = relationship("IngestionBatch", back_populates="raw_payloads")
    batch_items = relationship("BatchItem", back_populates="raw_payload", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("source", "endpoint", "primary_key", "fetched_at", name="uq_raw_payload_version"),
        Index("ix_raw_payload_source_endpoint", "source", "endpoint"),
        Index("ix_raw_payload_batch_id", "batch_id"),
        Index("ix_raw_payload_fetched_at", "fetched_at"),
    )


class IngestionBatch(Base):
    __tablename__ = "ingestion_batches"

    id = Column(String(36), primary_key=True, default=_uuid, nullable=False)
    source = Column(String(64), nullable=False)
    batch_type = Column(String(128), nullable=False)
    range_start = Column(Date, nullable=True)
    range_end = Column(Date, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(32), nullable=False, default="running")
    item_count = Column(Integer, nullable=False, default=0)
    merkle_root = Column(CHAR(64), nullable=True)
    anchor_id = Column(String(36), ForeignKey("anchors.id"), nullable=True)
    notes = Column(Text, nullable=True)

    raw_payloads = relationship("RawPayload", back_populates="batch", cascade="all, delete-orphan")
    items = relationship("BatchItem", back_populates="batch", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_ingestion_batch_type_started", "batch_type", "started_at"),)


class BatchItem(Base):
    __tablename__ = "batch_items"

    id = Column(String(36), primary_key=True, default=_uuid, nullable=False)
    batch_id = Column(String(36), ForeignKey("ingestion_batches.id"), nullable=False)
    raw_payload_id = Column(String(36), ForeignKey("raw_payloads.id"), nullable=False)
    item_sha256 = Column(CHAR(64), nullable=False)
    leaf_index = Column(Integer, nullable=False)

    batch = relationship("IngestionBatch", back_populates="items")
    raw_payload = relationship("RawPayload", back_populates="batch_items")

    __table_args__ = (
        UniqueConstraint("batch_id", "raw_payload_id", name="uq_batch_raw_payload"),
        Index("ix_batch_items_batch_leaf", "batch_id", "leaf_index"),
    )


class Anchor(Base):
    __tablename__ = "anchors"

    id = Column(String(36), primary_key=True, default=_uuid, nullable=False)
    anchor_type = Column(String(64), nullable=False)
    entry_type = Column(String(255), nullable=False)
    root = Column(CHAR(64), nullable=False)
    anchored_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    provider_payload = Column(JSON, nullable=False, default=dict)


class JobState(Base):
    __tablename__ = "job_state"

    job_name = Column(String(128), primary_key=True, nullable=False)
    cursor_json = Column(JSON, nullable=False, default=dict)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    status = Column(String(32), nullable=False, default="idle")


class ReconcileReport(Base):
    __tablename__ = "reconcile_reports"

    id = Column(String(36), primary_key=True, default=_uuid, nullable=False)
    run_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    status = Column(String(32), nullable=False)
    report_json = Column(JSON, nullable=False)


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(String(32), primary_key=True, nullable=False)
    prompt = Column(Text, nullable=False)
    response_type = Column(String(32), nullable=False, default="LIKERT_7")
    dimensions_json = Column(JSON, nullable=False)
    tags_json = Column(JSON, nullable=False, default=list)
    active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    answers = relationship("InterviewAnswer", back_populates="question")

    __table_args__ = (Index("ix_interview_questions_active", "active"),)


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(String(36), primary_key=True, default=_uuid, nullable=False)
    anon_user_hash = Column(CHAR(64), nullable=False)
    status = Column(String(32), nullable=False, default="in_progress")
    metadata_json = Column(JSON, nullable=False, default=dict)
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    answers = relationship("InterviewAnswer", back_populates="session", cascade="all, delete-orphan")
    result = relationship("InterviewResult", back_populates="session", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_interview_sessions_started_at", "started_at"),
        Index("ix_interview_sessions_anon_user_hash", "anon_user_hash"),
    )


class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    id = Column(String(36), primary_key=True, default=_uuid, nullable=False)
    session_id = Column(String(36), ForeignKey("interview_sessions.id"), nullable=False)
    question_id = Column(String(32), ForeignKey("interview_questions.id"), nullable=False)
    answer_value = Column(Integer, nullable=False)
    answered_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    session = relationship("InterviewSession", back_populates="answers")
    question = relationship("InterviewQuestion", back_populates="answers")

    __table_args__ = (
        UniqueConstraint("session_id", "question_id", name="uq_interview_answer_once_per_question"),
        Index("ix_interview_answers_session_id", "session_id"),
    )


class InterviewResult(Base):
    __tablename__ = "interview_results"

    id = Column(String(36), primary_key=True, default=_uuid, nullable=False)
    session_id = Column(String(36), ForeignKey("interview_sessions.id"), nullable=False, unique=True)
    vector_json = Column(JSON, nullable=False)
    left_right_score = Column(Float, nullable=False, default=0.0)
    confidence = Column(Float, nullable=False, default=0.0)
    consistency = Column(Float, nullable=False, default=0.0)
    ranking_json = Column(JSON, nullable=False, default=dict)
    generated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    session = relationship("InterviewSession", back_populates="result")

    __table_args__ = (Index("ix_interview_results_generated_at", "generated_at"),)


class LegislatorProfile(Base):
    __tablename__ = "legislator_profiles"

    id = Column(String(36), primary_key=True, default=_uuid, nullable=False)
    external_id = Column(String(64), nullable=False)
    name = Column(String(255), nullable=False)
    chamber = Column(String(16), nullable=False)
    party = Column(String(16), nullable=False)
    state = Column(String(2), nullable=True)
    vector_json = Column(JSON, nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("external_id", "chamber", name="uq_legislator_profiles_external_chamber"),
        Index("ix_legislator_profiles_party", "party"),
    )


class PartyProfile(Base):
    __tablename__ = "party_profiles"

    id = Column(String(36), primary_key=True, default=_uuid, nullable=False)
    acronym = Column(String(16), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    vector_json = Column(JSON, nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
